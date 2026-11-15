"""Writes the eye data the app needs for the 96 px portraits: occhi96.tsv and emozioni.txt.

    ~/venv/ritratti/bin/python -I occhi96.py --app ../../app/src/main/assets/avatar \
        [--anteprima ~/mannaggia-cache/anteprima96] [--speciali ~/mannaggia-cache/speciali_occhi96] \
        [--pazienza ~/mannaggia-cache/pazienza_occhi96]

occhi96.tsv: id <TAB> iris (middle tone) <TAB> brows <TAB> skin (crease and lower lid) <TAB> shape ("" or "mono")
<TAB> glasses (0/1) <TAB> brows' tail <TAB> bushy brows (0/1).
The colours are read from the portraits drawn WITH open eyes (anteprima96.px.js, and the specials: the B
eyes of occhi() in occhi.px.js), at fixed pixels of the left eye. It is at x 36, y 41 in the 94 px figure,
+1 in the 96 px image (outline): iris (36,44), brows (37,37), skin (37,46), the brows' tail (32,38); the brows
are bushy (three rows) when (37,36) has their colour too. The app draws the same eyes on the portrait
without eyes (Occhi.kt).
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

def campioni(im):
    """iris, brows, skin, tail, bushy: sampled from a portrait with open B eyes."""
    b = hexa(im, 37, 37)
    return hexa(im, 36, 44), b, hexa(im, 37, 46), hexa(im, 32, 38), int(hexa(im, 37, 36) == b)


data = json.loads(re.search(r"var TRATTI = (.*)\n", (HERE / "tratti96.data.js").read_text(encoding="utf-8")).group(1))
GLASSES = {fid("San Massimiliano Maria Kolbe"), fid("San Josemaría Escrivá de Balaguer")}
rows = []
for d in data:
    im = Image.open(Path(a.anteprima) / "sprites" / f"p_{d['id']}.png").convert("RGB")
    i, b, s, t, f = campioni(im)
    rows.append((d["id"], i, b, s, d.get("occhi") or "", int(d["id"] in GLASSES), t, f))
speciali = [l.strip() for l in (app / "speciali.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
sp = Path(a.speciali) / "sprites"
files = ["spec_s1_santo_subito", "spec_s2_san_culo", "spec_s3_san_calendario", "spec_s4_san_deploy", "spec_s5_san_sudo", None, "spec_s7_santa_cunegonda"]
for i, (nome, f) in enumerate(zip(speciali, files), 1):
    src = Path(a.pazienza) / "sprites" / "pazienza_96.png" if f is None else sp / f"{f}.png"
    im = Image.open(src).convert("RGB")
    ir, b, s, t, f = campioni(im)
    rows.append((fid(nome), ir, b, s, "", int(i == 4), t, f))
(app / "occhi96.tsv").write_text("# id\tiride\tsopracciglia\tpelle\tforma\tocchiali\tcoda\tfolte\n" +
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
