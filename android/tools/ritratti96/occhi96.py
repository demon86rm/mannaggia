"""Writes the eye data the app needs for the 96 px portraits: occhi96.tsv and emozioni.txt.

    ~/venv/ritratti/bin/python -I occhi96.py --app ../../app/src/main/assets/avatar \
        [--anteprima ~/mannaggia-cache/anteprima96] [--speciali ~/mannaggia-cache/speciali_occhi96] \
        [--pazienza ~/mannaggia-cache/pazienza_occhi96]

occhi96.tsv: id <TAB> iris <TAB> brows (the hair colour x 0.75; the specials: sampled) <TAB> lower lash <TAB> shape ("" or "mono") <TAB> glasses (0/1).
The colours are read from the portraits drawn WITH open eyes (anteprima96.px.js, and the specials), at fixed
pixels: the left eye is at x 36, y 41 in the 94 px figure, +1 in the 96 px image (outline), so brow (35,37), iris (36,44), lower lash (37,46). The app draws the
same eyes on the portrait without eyes.
emozioni.txt: the 6 emotions of occhi.px.js (EMOZIONI), one line each: name, then 48 steps "dx,dy,lid,browL,browR,worry,small".
"""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
from PIL import Image

HERE = Path(__file__).parent
cache = Path.home() / "mannaggia-cache"
ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--anteprima", default=str(cache / "anteprima96"))
ap.add_argument("--speciali", default=str(cache / "speciali_occhi96"))
ap.add_argument("--pazienza", default=str(cache / "pazienza_occhi96"))
a = ap.parse_args()
app = Path(a.app)
fid = lambda n: hashlib.sha1(n.encode("utf-8")).hexdigest()[:12]
hexa = lambda im, x, y: "#%02x%02x%02x" % im.getpixel((x, y))[:3]
# brows: the hair colour, a little darker (the ramp's darkest step was pure black for most saints)
brow = lambda h: "#%02x%02x%02x" % tuple(round(int(h[i:i + 2], 16) * 0.75) for i in (1, 3, 5))

data = json.loads(re.search(r"var TRATTI = (.*)\n", (HERE / "tratti96.data.js").read_text(encoding="utf-8")).group(1))
GLASSES = {fid("San Massimiliano Maria Kolbe"), fid("San Josemaría Escrivá de Balaguer")}
rows = []
for d in data:
    im = Image.open(Path(a.anteprima) / "sprites" / f"p_{d['id']}.png").convert("RGB")
    rows.append((d["id"], hexa(im, 36, 44), brow(d["chioma"]), hexa(im, 37, 46), d.get("occhi") or "", int(d["id"] in GLASSES)))
speciali = [l.strip() for l in (app / "speciali.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
sp = Path(a.speciali) / "sprites"
files = ["spec_s1_santo_subito", "spec_s2_san_culo", "spec_s3_san_calendario", "spec_s4_san_deploy", "spec_s5_san_sudo", None, "spec_s7_santa_cunegonda"]
for i, (nome, f) in enumerate(zip(speciali, files), 1):
    src = Path(a.pazienza) / "sprites" / "pazienza_96.png" if f is None else sp / f"{f}.png"
    im = Image.open(src).convert("RGB")
    rows.append((fid(nome), hexa(im, 36, 44), hexa(im, 35, 37), hexa(im, 37, 46), "", int(i == 4)))
(app / "occhi96.tsv").write_text("# id\tiride\tsopracciglia\tpalpebra_sotto\tforma\tocchiali\n" +
                                 "".join("\t".join(map(str, r)) + "\n" for r in rows), encoding="utf-8")

src = (HERE / "occhi.px.js").read_text(encoding="utf-8")
code = src[src.index("var fr ="):src.index("function occhi(")]
js = "const E = new Function(%s + '; return EMOZIONI')(); console.log(JSON.stringify(E))" % json.dumps(code)
em = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
lines = ["# emozione<TAB>passi (12 al secondo): dx,dy,palpebra,sopracciglioSx,sopracciglioDx,preoccupato,pupilla_piccola"]
for nome, seq in em.items():
    lines.append(nome + "\t" + ";".join(f"{f['g'][0]},{f['g'][1]},{f['lid']},{f['brow'][0]},{f['brow'][1]},{int(f['worry'])},{int(f['small'])}" for f in seq))
(app / "emozioni.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(rows), "rows;", {k: len(v) for k, v in em.items()})
