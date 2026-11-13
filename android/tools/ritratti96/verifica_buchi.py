"""Gate: no holes in the figure. Build buchi96.px.js first (the portraits on a magenta background):
    node <pxl>/bin/pxl.js build buchi96.px.js --no-preview --out ~/mannaggia-cache/buchi96
    ~/venv/ritratti/bin/python -I verifica_buchi.py [~/mannaggia-cache/buchi96]
Magenta (lit, or darkened by the figure's shadow layer) inside the neck column or below the shoulder
line means the background shows through. Prints the saints that fail.
"""
import json, re, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).parent
out = Path(sys.argv[1] if len(sys.argv) > 1 else "~/mannaggia-cache/buchi96").expanduser() / "sprites"
data = json.loads(re.search(r"var TRATTI = (.*)\n", (HERE / "tratti96.data.js").read_text(encoding="utf-8")).group(1))
mag = lambda c: c[1] <= 8 and c[0] == c[2] and c[0] >= 150
bad = 0
for d in data:
    im = Image.open(out / f"p_{d['id']}.png").convert("RGB")
    if any(mag(im.getpixel((x, y))) and (y >= 84 or abs(x - 48) <= 12) for y in range(60, 96) for x in range(8, 88)):
        bad += 1; print(d["n"])
print(f"{len(data) - bad}/{len(data)} ok", file=sys.stderr)
