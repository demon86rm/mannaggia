"""Gate of the 96 px portraits WITHOUT the mouth: its zone, where the app draws the mouth (bocca.px.js,
Bocca.kt), must hold one skin colour only. Prints the saints that fail.
    ~/venv/ritratti/bin/python -I verifica_bocca.py [out_senza]
Zone (figure coordinates + 1 for the outline): without a beard rows 53-58, dx -7..7 (the forms of BOCCHE);
with a beard the opening barba6() leaves under the moustache, rows 54-56, |dx| <= 58 - y; with a
moustache only (San Joseph Mukasa) rows 54-58: row 53 is the moustache (his form, M2, does not use it).
"""
import json, re, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).parent
out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "out_senza") / "sprites"
data = json.loads(re.search(r"var TRATTI = (.*)\n", (HERE / "tratti96.data.js").read_text(encoding="utf-8")).group(1))
CX = 47
NUDA = [(CX + dx + 1, y + 1) for y in range(53, 59) for dx in range(-7, 8)]
BAFFI = [p for p in NUDA if p[1] > 54]
BARBA = [(CX + dx + 1, y + 1) for y in range(54, 57) for dx in range(-7, 8) if abs(dx) <= 58 - y]
bad = []
for d in data:
    im = Image.open(out / f"p_{d['id']}.png").convert("RGB")
    zona = BARBA if d["barba"] in ("corta", "lunga") else BAFFI if d["barba"] == "baffi" else NUDA
    colori = {im.getpixel(p) for p in zona}
    if len(colori) > 1:
        bad.append((d["n"], d["bocca_f"], len(colori)))
for b in bad:
    print(*b, sep="\t")
print(f"{len(data) - len(bad)}/{len(data)} ok", file=sys.stderr)
