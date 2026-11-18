"""Hamlet Tertia 18 (OFL 1.1, Gotico-Antiqua project, ANRT Nancy 2019) completed for the saints' names.

The original has 114 glyphs: no accented letters beyond ä ö ü Ü, no «º». This script adds every letter of
santi.txt the font lacks, as base letter + a mark drawn in the font's own style (the slanted strokes of its
dieresis), plus a few letters built from two glyphs (æ, ǆ) or a stroke (ł, ø, đ, Đ, ð) and «º».
The OFL allows modified versions (the font declares no Reserved Font Name); the result stays under the OFL,
with the family renamed «Hamlet Tertia Mannaggia».

    ~/venv/ritratti/bin/python -I hamlet_esteso.py --santi ../../app/src/main/assets/santi.txt \\
        --out ../../app/src/main/res/font/hamlet_tertia.otf

Needs fonttools (pip install fonttools in ~/venv/ritratti).
"""
import argparse, unicodedata
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen

HERE = Path(__file__).parent
X_TOP, CAP_TOP = 410, 700           # x-height and cap height of the font
SU, SU_CAP = 483, 742               # where marks above start, over a lowercase and over a capital


# --- the marks, as polygons in font units, horizontally centred on x 0, from y 0 upwards (or down from 0) ---
def dot(cx, y):                     # one dot of the font's dieresis: a slanted parallelogram
    return [[(cx - 58, y), (cx - 3, y), (cx + 59, y + 77), (cx + 57, y + 81), (cx - 11, y + 81), (cx - 58, y + 2)]]

ACUTO = [[(-55, 0), (-15, 0), (85, 120), (75, 135), (25, 135)]]
GRAVE = [[(55, 0), (15, 0), (-85, 120), (-75, 135), (-25, 135)]]
CIRC = [[(-95, 0), (-55, 0), (0, 70), (55, 0), (95, 0), (20, 115), (-20, 115)]]
CARON = [[(-95, 115), (-55, 115), (0, 45), (55, 115), (95, 115), (20, 0), (-20, 0)]]
MACRON = [[(-90, 30), (90, 30), (90, 72), (-90, 72)]]
TILDE = [[(-100, 20), (-65, 75), (-20, 50), (25, 40), (60, 80), (100, 95), (65, 40), (20, 5), (-25, 15), (-60, 30), (-90, 5)]]
BREVE = [[(-90, 110), (-55, 110), (-40, 60), (0, 45), (40, 60), (55, 110), (90, 110), (70, 30), (0, 0), (-70, 30)]]
DIAER = dot(-65, 0) + dot(65, 0)
PUNTO = dot(0, 0)
DOPPIO = [[(x - 55, y) for x, y in ACUTO[0]], [(x + 55, y) for x, y in ACUTO[0]]]
UNCINO = [[(-30, 0), (5, 0), (5, 45), (45, 70), (45, 115), (0, 140), (-45, 125), (-30, 100), (0, 108), (12, 95), (12, 78), (-30, 55)]]
# below the baseline: cedilla, ogonek (both hang from the letter's foot), comma, dot
CEDIGLIA = [[(-15, 0), (20, 0), (20, -45), (70, -70), (60, -140), (-40, -155), (-40, -125), (25, -115), (25, -85), (-15, -60)]]
OGONEK = [[(0, 0), (40, 0), (5, -60), (25, -110), (85, -125), (85, -150), (-25, -140), (-45, -80)]]
VIRGOLA = [[(-20, -40), (35, -40), (40, -90), (-5, -170), (-30, -165), (0, -95), (-25, -95)]]
PUNTO_SOTTO = dot(0, -175)
BREVE_SOTTO = [[(x, y - 230) for x, y in BREVE[0]]]
MACRON_SOTTO = [[(x, y - 200) for x, y in MACRON[0]]]

SOPRA = {"\u0301": ACUTO, "\u0300": GRAVE, "\u0302": CIRC, "\u030C": CARON, "\u0304": MACRON, "\u0303": TILDE,
         "\u0306": BREVE, "\u0308": DIAER, "\u0307": PUNTO, "\u030B": DOPPIO, "\u0309": UNCINO}
SOTTO = {"\u0327": CEDIGLIA, "\u0328": OGONEK, "\u0326": VIRGOLA, "\u0323": PUNTO_SOTTO, "\u032E": BREVE_SOTTO,
         "\u0331": MACRON_SOTTO}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(HERE / "Hamlet-Tertia18.otf"))
    ap.add_argument("--santi", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    f = TTFont(a.src)
    gs, cm = f.getGlyphSet(), f.getBestCmap()
    cff = f["CFF "].cff
    td = cff.topDictIndex[0]
    priv, cs = td.Private, td.CharStrings
    order = f.getGlyphOrder()
    nome = {c: g for c, g in cm.items()}

    def bounds(g):
        p = BoundsPen(gs); gs[g].draw(p); return p.bounds

    def contorni(g):
        p = RecordingPen(); gs[g].draw(p)
        out, cur = [], []
        for op, args in p.value:
            cur.append((op, args))
            if op in ("closePath", "endPath"): out.append(cur); cur = []
        return out

    def senza_punto(g):                 # the dotless i: the stem only, without the contour of its dot
        cs_ = contorni(g)
        def top(c): return max(pt[1] for _, args in c for pt in args)
        return sorted(cs_, key=top)[:-1]

    nuovi = {}

    def aggiungi(ch, larghezza, disegna):
        name = "uni%04X" % ord(ch)
        pen = T2CharStringPen(larghezza - priv.nominalWidthX, gs)
        disegna(pen)
        c = pen.getCharString(private=priv, globalSubrs=cff.GlobalSubrs)
        nuovi[name] = (ord(ch), larghezza, c)
        return name

    def poligoni(pen, polys, dx=0, dy=0, sx=1.0, sy=1.0):
        for poly in polys:
            pts = [(dx + x * sx, dy + y * sy) for x, y in poly]
            pen.moveTo(pts[0])
            for p in pts[1:]: pen.lineTo(p)
            pen.closePath()

    def base_su(pen, g, dx=0, solo=None):
        tp = TransformPen(pen, (1, 0, 0, 1, dx, 0))
        if solo is None: gs[g].draw(tp)
        else:
            for c in solo:
                for op, args in c: getattr(tp, op)(*args)

    def segno(ch):
        """base + marks: the base letter, a mark above at the letter's top, one below at its foot."""
        d = unicodedata.normalize("NFD", ch)
        base, marks = d[0], d[1:]
        if ord(base) not in nome or not marks: return False
        g = nome[ord(base)]
        x0, y0, x1, y1 = bounds(g)
        larg = f["hmtx"][g][0]
        maiusc = base.isupper() or base in "bdfhklt"
        solo = senza_punto(g) if base in "ij" else None
        def disegna(pen):
            base_su(pen, g, solo=solo)
            cx, alto = (x0 + x1) / 2, SU_CAP if maiusc else SU
            s = 0.8 if base.isupper() else 1.0               # flatter over capitals: they stay under the ascent
            for k, m in enumerate(marks):
                if m in SOPRA:
                    if base in "dlt" and m == "\u030C":      # ď ľ ť: the caron as an apostrophe beside the stem
                        poligoni(pen, VIRGOLA, x1 + 40, 720, 0.8, 0.8)
                    else:
                        g_ = 1.3 if m in "\u0301\u0300\u030B" else 1.0          # acute and grave: as tall as the dieresis is wide
                        poligoni(pen, SOPRA[m], cx + (25 if m != "\u0308" else 0), alto + k * 125, g_, s * g_)
                elif m in SOTTO:
                    piede = x1 - 45 if m == "\u0328" else cx
                    poligoni(pen, SOTTO[m], piede, 0)
                elif m == "\u031B":                          # horn: a small hook at the top right
                    poligoni(pen, [[(0, 0), (30, 0), (75, 60), (60, 110), (25, 110), (40, 65)]], x1 - 25, y1 - 60)
        aggiungi(ch, larg, disegna)
        return True

    def barrata(ch, g, ya, xa=None, lunghezza=150):
        """a letter crossed by a slanted stroke (ł ø) or a bar (đ Đ ð)."""
        x0, y0, x1, y1 = bounds(g)
        cx = xa if xa is not None else (x0 + x1) / 2
        def disegna(pen):
            base_su(pen, g)
            h = lunghezza / 2
            if ch == "ł":
                poligoni(pen, [[(cx - h, ya - 60), (cx - h + 40, ya - 60), (cx + h, ya + 60), (cx + h - 40, ya + 60)]])
            elif ch == "ø":                 # a steep slash right through the bowl
                poligoni(pen, [[(cx - 120, -40), (cx - 80, -40), (cx + 120, 450), (cx + 80, 450)]])
            else:
                poligoni(pen, [[(cx - h, ya), (cx + h, ya), (cx + h, ya + 38), (cx - h, ya + 38)]])
        aggiungi(ch, f["hmtx"][g][0], disegna)

    def coppia(ch, g1, g2, ritira=25):
        w1 = f["hmtx"][g1][0]
        def disegna(pen):
            base_su(pen, g1); base_su(pen, g2, dx=w1 - ritira)
        aggiungi(ch, w1 - ritira + f["hmtx"][g2][0], disegna)

    nomi = [l.strip() for l in open(a.santi, encoding="utf-8") if l.strip()]
    serve = sorted({ch for n in nomi for ch in n if ord(ch) not in cm and ch != " "} | {"º"})
    mancano = []
    for ch in serve:
        if segno(ch): continue
        if ch == "ł": barrata(ch, "l", 300, lunghezza=170)
        elif ch == "ø": barrata(ch, "o", 200, lunghezza=300)
        elif ch == "đ": barrata(ch, "d", 560, xa=bounds("d")[2] - 60, lunghezza=150)
        elif ch == "Đ": barrata(ch, "D", 330, xa=bounds("D")[0] + 60, lunghezza=150)
        elif ch == "ð": barrata(ch, "d", 560, lunghezza=200)
        elif ch == "æ": coppia(ch, "a", "e", 60)
        elif ch in "ʹʾ": aggiungi(ch, f["hmtx"]["quoteright"][0], lambda pen: base_su(pen, "quoteright"))
        elif ch == "º":                 # a small raised o over a bar
            o0 = bounds("o")
            def disegna(pen):
                tp = TransformPen(pen, (0.55, 0, 0, 0.55, 20, 390)); gs["o"].draw(tp)
                poligoni(pen, [[(30, 330), (30 + (o0[2] - o0[0]) * 0.55, 330), (30 + (o0[2] - o0[0]) * 0.55, 365), (30, 365)]])
            aggiungi(ch, int(o0[2] * 0.55) + 60, disegna)
        elif ch == "/": aggiungi(ch, 300, lambda pen: poligoni(pen, [[(20, -60), (70, -60), (280, 720), (230, 720)]]))
        elif ch == "_": aggiungi(ch, 500, lambda pen: poligoni(pen, [[(0, -120), (500, -120), (500, -80), (0, -80)]]))
        elif ch == "#": aggiungi(ch, 520, lambda pen: poligoni(pen, [[(140, 0), (185, 0), (245, 640), (200, 640)], [(300, 0), (345, 0), (405, 640), (360, 640)],
                                                                     [(60, 190), (470, 190), (480, 235), (70, 235)], [(80, 410), (490, 410), (500, 455), (90, 455)]]))
        else: mancano.append(ch)
    # ǆ (one name): d + ž, ž being one of the new glyphs
    if "ǆ" in serve and "uni017E" in nuovi:
        w1 = f["hmtx"]["d"][0] - 20
        zc = nuovi["uni017E"][2]
        def disegna(pen):
            base_su(pen, "d")
            zc.draw(TransformPen(pen, (1, 0, 0, 1, w1, 0)))
        aggiungi("ǆ", w1 + nuovi["uni017E"][1], disegna)
        mancano = [c for c in mancano if c != "ǆ"]

    # into the font: CharStrings, glyph order, metrics, cmap
    for name, (cp, larg, c) in nuovi.items():
        c.private, c.globalSubrs = priv, cff.GlobalSubrs
        cs.charStrings[name] = len(cs.charStringsIndex)
        cs.charStringsIndex.append(c)
        td.charset.append(name)
        order.append(name)
        bp = BoundsPen(None); c.draw(bp)
        f["hmtx"][name] = (larg, int(bp.bounds[0]) if bp.bounds else 0)
        for t in f["cmap"].tables:
            if t.isUnicode(): t.cmap[cp] = name
    f.setGlyphOrder(order)
    f["maxp"].numGlyphs = len(order)
    if "DSIG" in f: del f["DSIG"]
    nuovo_nome = {1: "Hamlet Tertia Mannaggia", 4: "Hamlet Tertia Mannaggia", 6: "HamletTertia-Mannaggia", 16: "Hamlet Tertia Mannaggia"}
    for rec in f["name"].names:         # renamed: a modified version
        if rec.nameID in nuovo_nome: rec.string = nuovo_nome[rec.nameID]
        elif rec.nameID == 3: rec.string = "HamletTertia-Mannaggia; modified from " + rec.toUnicode()
    f.save(a.out)
    print(f"{len(nuovi)} glyphs added -> {a.out}" + (f"; still missing: {''.join(mancano)}" if mancano else ""))


if __name__ == "__main__":
    main()
