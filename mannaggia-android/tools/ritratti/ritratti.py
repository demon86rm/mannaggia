#!/usr/bin/env python3
"""Ritratti in pixel art dei santi, dalle immagini di Wikimedia Commons.

Per ogni santo di santi.txt con un'immagine su Wikidata (P18), con licenza
compatibile con la GPLv3:
1. scarica la miniatura da Commons, con licenza e autore per i crediti;
2. ritaglia un quadrato attorno al volto (OpenCV YuNet), o in alto se non ne trova;
3. riduce a 48x48 e a una tavolozza di pochi colori, senza dithering.

Uso (venv con pillow, opencv-python-headless e numpy; dalla cartella mannaggia-android):
    python tools/ritratti/ritratti.py --nomi lista.txt --casuali 10 --out ~/mannaggia-ritratti-prova

Crea <out>/<sha1(santo)[:12]>.png (lo stesso nome dei file audio), crediti.tsv e
provino.png (originale ritagliato e pixel art affiancati, ingranditi) da guardare a occhio.
"""

import argparse
import hashlib
import html
import importlib.util
import io
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # mannaggia-android/
USER_AGENT = "mannaggia-ritratti/1.0 (https://github.com/demon86rm/mannaggia)"
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/"
             "face_detection_yunet/face_detection_yunet_2023mar.onnx")
YUNET = Path.home() / ".cache/mannaggia/face_detection_yunet_2023mar.onnx"

# Licenze compatibili con la GPLv3 (decisione 2026-10-21). Le BY-SA 2.x/3.0 no.
LICENSE_OK = re.compile(r"^(public domain|pd\b.*|cc0.*|no restrictions|copyrighted free use|"
                        r"cc[ -]by[ -]\d(\.\d)?|cc[ -]by[ -]sa[ -]4\.0)$", re.I)


def load_genera_santi():
    spec = importlib.util.spec_from_file_location("gs", ROOT / "tools/genera_santi.py")
    gs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gs)
    return gs


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def saint_images(gs, known):
    """santo -> titolo del file su Commons (prima immagine P18)."""
    people = gs.collect(gs.fetch())
    images = {}
    query = "SELECT ?item ?img WHERE { VALUES ?status { %s } ?item wdt:P411 ?status; wdt:P18 ?img. }" % gs.STATUSES
    for row in gs.fetch(query):
        images.setdefault(row["item"]["value"].rsplit("/", 1)[1], row["img"]["value"])
    out = {}
    for qid, p in people.items():
        name = gs.display_name(p)
        if name in known and qid in images:
            out[name] = urllib.parse.unquote(images[qid].rsplit("/", 1)[1])
    return out


def commons_info(titles, width=512):
    """titolo -> {license, artist, url, page}, a blocchi di 50."""
    info = {}
    titles = list(titles)
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "prop": "imageinfo",
            "titles": "|".join("File:" + t for t in chunk),
            "iiprop": "extmetadata|url", "iiurlwidth": width,
            "iiextmetadatafilter": "LicenseShortName|Artist",
        })
        data = get_json(url)
        # The API normalizes titles (spaces vs underscores): map them back.
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"].values():
            if "imageinfo" not in page:
                continue
            ii = page["imageinfo"][0]
            meta = ii.get("extmetadata", {})
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))
            title = norm.get(page["title"], page["title"])[5:]
            info[title] = {
                "license": meta.get("LicenseShortName", {}).get("value", "?"),
                "artist": " ".join(html.unescape(artist).split()) or "sconosciuto",
                "url": ii.get("thumburl") or ii["url"],
                "page": ii.get("descriptionurl", ""),
            }
    return info


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def face_crop(img, detector, scale):
    """Square crop around the largest face (with hair/halo), else the top of the image."""
    w, h = img.size
    detector.setInputSize((w, h))
    _, faces = detector.detect(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    if faces is not None and len(faces):
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])[:4]
        side = min(max(fw, fh) * scale, w, h)
        cx, cy = x + fw / 2, y + fh * 0.42  # a bit above the face centre: halo
        found = True
    else:
        side = min(w, h) * 0.8
        cx, cy = w / 2, side / 2 + h * 0.04  # faces sit in the upper part of portraits
        found = False
    left = min(max(cx - side / 2, 0), w - side)
    top = min(max(cy - side / 2, 0), h - side)
    return img.crop((int(left), int(top), int(left + side), int(top + side))), found


def pixelate(img, size, colors):
    small = img.resize((size, size), Image.BOX)
    small = ImageEnhance.Contrast(small).enhance(1.15)
    small = ImageEnhance.Color(small).enhance(1.25)
    return small.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                          dither=Image.Dither.NONE).convert("RGB")


def file_id(saint):
    return hashlib.sha1(saint.encode("utf-8")).hexdigest()[:12]


def contact_sheet(items, path, zoom=6, cols=4):
    """Original crop and pixel art side by side, with the name below."""
    tile = 48 * zoom
    cell_w, cell_h = tile * 2 + 12, tile + 28
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + 12, rows * cell_h + 12), (32, 32, 32))
    draw = ImageDraw.Draw(sheet)
    for i, (name, crop, pixel) in enumerate(items):
        x = 12 + (i % cols) * cell_w
        y = 12 + (i // cols) * cell_h
        sheet.paste(crop.resize((tile, tile), Image.BILINEAR), (x, y))
        sheet.paste(pixel.resize((tile, tile), Image.NEAREST), (x + tile + 4, y))
        draw.text((x, y + tile + 6), name, fill=(230, 230, 230))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--santi", default=str(ROOT / "app/src/main/assets/santi.txt"))
    ap.add_argument("--nomi", help="file con i santi da convertire (uno per riga)")
    ap.add_argument("--casuali", type=int, default=0, help="aggiunge N santi a caso con licenza valida")
    ap.add_argument("--out", default=str(Path.home() / "mannaggia-ritratti-prova"))
    ap.add_argument("--size", type=int, default=48)
    ap.add_argument("--colori", type=int, default=20)
    ap.add_argument("--scala-volto", type=float, default=2.6, help="lato del ritaglio / lato del volto")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    known = {l.strip() for l in open(args.santi, encoding="utf-8") if l.strip() and not l.startswith("#")}
    images = saint_images(load_genera_santi(), known)
    print(f"{len(images)} santi con immagine su Wikidata", file=sys.stderr)

    wanted = [l.strip() for l in open(args.nomi, encoding="utf-8") if l.strip()] if args.nomi else []
    pool = sorted(set(images) - set(wanted))
    random.Random(args.seed).shuffle(pool)
    info = commons_info([images[n] for n in wanted if n in images] + [images[n] for n in pool[:args.casuali * 4]])

    def usable(name):
        i = info.get(images.get(name, ""))
        return i is not None and LICENSE_OK.match(i["license"].strip())

    chosen = [n for n in wanted if usable(n)]
    for n in wanted:
        if n not in images:
            print(f"  senza immagine: {n}", file=sys.stderr)
        elif not usable(n):
            print(f"  licenza esclusa: {n} ({info.get(images[n], {}).get('license', '?')})", file=sys.stderr)
    chosen += [n for n in pool[:args.casuali * 4] if usable(n)][:args.casuali]

    if not YUNET.exists():
        YUNET.parent.mkdir(parents=True, exist_ok=True)
        YUNET.write_bytes(urllib.request.urlopen(YUNET_URL, timeout=60).read())
    detector = cv2.FaceDetectorYN.create(str(YUNET), "", (320, 320), 0.6)

    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    sheet, credits = [], []
    for name in chosen:
        meta = info[images[name]]
        try:
            img = download(meta["url"])
        except Exception as e:  # noqa: BLE001 - keep going, report at the end
            print(f"  download fallito: {name}: {e}", file=sys.stderr)
            continue
        crop, found = face_crop(img, detector, args.scala_volto)
        pixel = pixelate(crop, args.size, args.colori)
        pixel.save(out / f"{file_id(name)}.png", optimize=True)
        sheet.append((name + ("" if found else "  (no volto)"), crop, pixel))
        credits.append((name, images[name], meta["artist"], meta["license"], meta["page"]))
        print(f"{name}: {meta['license']}, volto {'si' if found else 'no'}", file=sys.stderr)
        time.sleep(0.2)  # be gentle with Commons

    with open(out / "crediti.tsv", "w", encoding="utf-8") as f:
        f.write("santo\tfile\tautore\tlicenza\tpagina\n")
        for row in credits:
            f.write("\t".join(row) + "\n")
    if sheet:
        contact_sheet(sheet, out / "provino.png")
    print(f"{len(credits)} ritratti in {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
