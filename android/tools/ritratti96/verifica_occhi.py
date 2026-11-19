"""Gate of the 96 px portraits WITHOUT eyes: the eye and brow areas, where the app draws the animated
eyes, must hold only the saint's skin (base and far-side shadow). Prints the saints that fail.
    ~/venv/ritratti/bin/python -I verifica_occhi.py [out_senza]
"""
import json, re, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).parent
out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "out_senza") / "sprites"
data = json.loads(re.search(r"var TRATTI = (.*)\n", (HERE / "tratti96.data.js").read_text(encoding="utf-8")).group(1))
# fixed geometry of libreria96 (figure coordinates + 1: the outline grows the figure by 1 px)
# from occhi(): brows (raised, worried), lids (wide, "mono" corner), lower lash; +1 for the outline
ZONE = [(x, y) for y in range(34, 47) for x in list(range(32, 42)) + list(range(54, 64))]
bad = []
for d in data:
    im = Image.open(out / f"p_{d['id']}.png").convert("RGB")
    ok = {im.getpixel((34, 44)), im.getpixel((62, 44))}          # skin base, far-side shadow (both inside the area)
    wrong = [(x, y) for x, y in ZONE if im.getpixel((x, y)) not in ok]
    if wrong:
        bad.append((d["n"], len(wrong), wrong[:4]))
for b in bad:
    print(*b, sep="\t")
print(f"{len(data) - len(bad)}/{len(data)} ok", file=sys.stderr)
