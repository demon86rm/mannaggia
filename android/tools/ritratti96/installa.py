"""Copies the generated 96 px portraits into the app's assets, with the app's file names.

    ~/venv/ritratti/bin/python -I installa.py --app ../../app/src/main/assets/avatar \
        [--ritratti ~/mannaggia-cache/ritratti96] [--speciali ~/mannaggia-cache/speciali_app96] \
        [--pazienza ~/mannaggia-cache/pazienza_app96]

- ritratti96: p_<id>.png -> <id>.png (the 5420 saints of santi.txt)
- speciali_app96: s1..s5, s7 and decollato96 -> the file_id of the saint on that line of speciali.txt, and decollato.png
- pazienza_app96: pazienza96_base -> the file_id of S6
- martiri.txt: the martyrs (tratti96.data.js, from avatar.py), for the «… martire» label of the parchment card
"""
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True, help="assets/avatar of the app")
cache = Path.home() / "mannaggia-cache"
ap.add_argument("--ritratti", default=str(cache / "ritratti96"))
ap.add_argument("--speciali", default=str(cache / "speciali_app96"))
ap.add_argument("--pazienza", default=str(cache / "pazienza_app96"))
a = ap.parse_args()
app = Path(a.app)
fid = lambda n: hashlib.sha1(n.encode("utf-8")).hexdigest()[:12]

n = 0
for f in sorted((Path(a.ritratti) / "sprites").glob("p_*.png")):
    shutil.copyfile(f, app / (f.stem[2:] + ".png")); n += 1
speciali = [l.strip() for l in (app / "speciali.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
sp, pz = Path(a.speciali) / "sprites", Path(a.pazienza) / "sprites"
for i, nome in enumerate(speciali, 1):
    src = pz / "pazienza96_base.png" if i == 6 else sp / f"s{i}.png"
    shutil.copyfile(src, app / (fid(nome) + ".png")); n += 1
shutil.copyfile(sp / "decollato96.png", app / "decollato.png")
dati = json.loads(re.search(r"var TRATTI = (.*)\n", (Path(__file__).parent / "tratti96.data.js").read_text(encoding="utf-8")).group(1))
martiri = [d["n"] for d in dati if d.get("martire")]
(app / "martiri.txt").write_text("# I martiri (Wikidata, via avatar.py): etichetta «… martire» della carta.\n" + "\n".join(martiri) + "\n", encoding="utf-8")
print(f"{n} portraits + decollato.png + martiri.txt ({len(martiri)}) -> {app}")
