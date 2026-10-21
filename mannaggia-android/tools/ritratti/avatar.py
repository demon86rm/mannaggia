#!/usr/bin/env python3
"""Avatar in pixel art dei santi (mezzo busto, 48x48), disegnati da zero.

Nessuna immagine esistente viene usata: ogni avatar e' composto da pezzi
disegnati qui (testa, capelli, barba, copricapo, abito, attributo, aureola),
scelti in base ai tratti del santo. I tratti vengono da una tabella fatta a
mano per i santi piu' famosi (FAMOSI) o, per gli altri, da regole sui dati
Wikidata (genere, cariche, ordine religioso, mestiere, martirio). Le piccole
variazioni (carnagione, colori) sono deterministiche: dipendono dal nome.

Uso (venv con pillow; dalla cartella mannaggia-android):
    python tools/ritratti/avatar.py --nomi lista.txt --out ~/mannaggia-avatar-prova
"""

import argparse
import hashlib
import importlib.util
import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
S = 48  # lato dell'avatar

# --- Tavolozza ----------------------------------------------------------------

OUTLINE = (34, 24, 32)
SKINS = [(246, 208, 176), (234, 186, 146), (212, 156, 112), (172, 116, 78), (120, 80, 54)]
HAIRS = {"nero": (40, 32, 30), "castano": (104, 66, 40), "biondo": (214, 172, 92),
         "rosso": (160, 72, 36), "grigio": (150, 146, 144), "bianco": (232, 228, 220)}
GOLD, GOLD_DARK, GOLD_LIGHT = (232, 184, 56), (176, 124, 28), (252, 228, 132)
HALO, HALO_RING = (252, 232, 150), (226, 182, 70)
HALO_BEATO, HALO_BEATO_RING = (236, 230, 200), (196, 184, 140)
WHITE, BLACK = (240, 238, 232), (36, 34, 40)
RED, DARK_RED = (178, 34, 44), (120, 20, 30)
STEEL, STEEL_DARK, STEEL_LIGHT = (156, 164, 176), (100, 106, 120), (210, 216, 226)
GREEN, DARK_GREEN = (70, 150, 70), (38, 96, 46)
BROWN_HABIT, BLACK_HABIT = (122, 82, 50), (44, 40, 46)
EYE = (40, 30, 34)
MOUTH = (168, 84, 80)
BACKGROUNDS = [(94, 120, 168), (120, 92, 150), (84, 140, 130), (170, 110, 90),
               (110, 130, 90), (150, 96, 112), (88, 108, 128), (160, 140, 96)]
ROBES = [(70, 96, 160), (150, 50, 60), (60, 120, 90), (130, 90, 150), (180, 130, 60),
         (90, 90, 110), (40, 110, 140), (160, 80, 40)]


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


# --- Tratti -------------------------------------------------------------------

@dataclass
class Tratti:
    donna: bool = False
    beato: bool = False
    eta: str = "adulto"          # giovane | adulto | anziano
    pelle: int | None = None     # indice in SKINS, None = dal nome
    capelli: str = "corti"       # corti | lunghi | ricci | calvo | tonsura | nessuno
    colore_capelli: str | None = None
    barba: str = "nessuna"       # nessuna | corta | lunga
    copricapo: str = "nessuno"   # nessuno | velo | cappuccio | mitra | tiara | corona | elmo | spine
    abito: str = "tunica"        # tunica | apostolo | saio | benedettino | domenicano | vescovo
                                 # | papa | cardinale | armatura | crociato | regale | nudo | suora
    colore_abito: tuple | None = None
    attributo: str = "nessuno"   # chiavi | frecce | palma | spada | lancia | giglio | rosa | libro
                                 # | croce | pastorale | occhi | nessuno
    extra: list = field(default_factory=list)  # "ferita_fronte", "stigmate", ...


# Iconografia dei santi piu' noti, scritta a mano.
FAMOSI = {
    "San Pietro": Tratti(eta="anziano", capelli="calvo", colore_capelli="bianco", barba="corta",
                         abito="apostolo", colore_abito=(60, 90, 170), attributo="chiavi"),
    "San Francesco d'Assisi": Tratti(capelli="tonsura", colore_capelli="castano", barba="corta",
                                     copricapo="cappuccio", abito="saio", attributo="croce",
                                     extra=["stigmate"]),
    "San Pio da Pietrelcina": Tratti(eta="anziano", capelli="calvo", colore_capelli="bianco",
                                     barba="lunga", abito="saio", attributo="nessuno",
                                     extra=["guanti"]),
    "Santa Rita da Cascia": Tratti(donna=True, copricapo="velo", abito="suora",
                                   colore_abito=BLACK_HABIT, attributo="rosa",
                                   extra=["ferita_fronte"]),
    "Santa Giovanna d'Arco": Tratti(donna=True, eta="giovane", capelli="corti",
                                    colore_capelli="castano", abito="armatura", attributo="spada"),
    "San Sebastiano": Tratti(eta="giovane", capelli="ricci", colore_capelli="castano",
                             abito="nudo", attributo="frecce"),
    "San Gennaro": Tratti(capelli="corti", colore_capelli="nero", copricapo="mitra",
                          abito="vescovo", colore_abito=RED, attributo="pastorale"),
    "Santa Lucia": Tratti(donna=True, eta="giovane", capelli="lunghi", colore_capelli="castano",
                          abito="tunica", colore_abito=(60, 120, 80), attributo="occhi"),
    "San Giorgio": Tratti(eta="giovane", capelli="ricci", colore_capelli="biondo",
                          abito="crociato", attributo="lancia"),
    "Sant'Antonio di Padova": Tratti(eta="giovane", capelli="tonsura", colore_capelli="castano",
                                     abito="saio", attributo="giglio"),
    "San Giuseppe": Tratti(eta="anziano", capelli="corti", colore_capelli="grigio", barba="corta",
                           abito="apostolo", colore_abito=(150, 110, 60), attributo="giglio"),
    "Sant'Agostino d'Ippona": Tratti(eta="anziano", capelli="calvo", colore_capelli="grigio",
                                     barba="lunga", copricapo="mitra", abito="vescovo",
                                     colore_abito=(40, 70, 150), attributo="libro"),
    "San Giovanni Paolo II": Tratti(eta="anziano", capelli="corti", colore_capelli="bianco",
                                    copricapo="nessuno", abito="papa", attributo="croce"),
}


# --- Disegno ------------------------------------------------------------------

class Canvas:
    """48x48 RGBA layer drawn with aliased PIL primitives (pixel-exact)."""

    def __init__(self):
        self.img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def ell(self, box, c):
        self.d.ellipse(box, fill=c + (255,))

    def rect(self, box, c):
        self.d.rectangle(box, fill=c + (255,))

    def poly(self, pts, c):
        self.d.polygon(pts, fill=c + (255,))

    def line(self, pts, c, w=1):
        self.d.line(pts, fill=c + (255,), width=w)

    def px(self, x, y, c):
        if 0 <= x < S and 0 <= y < S:
            self.img.putpixel((x, y), c + (255,))

    def recolor(self, box, src, dst):
        """Replace color [src] with [dst] inside [box] (for shading one part only)."""
        x0, y0, x1, y1 = box
        for y in range(max(0, y0), min(S, y1 + 1)):
            for x in range(max(0, x0), min(S, x1 + 1)):
                if self.img.getpixel((x, y))[:3] == src:
                    self.img.putpixel((x, y), dst + (255,))


def h(name, salt):
    return int(hashlib.sha1(f"{salt}:{name}".encode()).hexdigest(), 16)


def draw_halo(c, t):
    fill, ring = (HALO_BEATO, HALO_BEATO_RING) if t.beato else (HALO, HALO_RING)
    c.ell((8, 1, 40, 33), ring)
    c.ell((9, 2, 39, 32), fill)


def draw_body(c, t, robe):
    a = t.abito
    if a == "nudo":
        skin = robe  # caller passes skin for bare chest
        c.ell((5, 32, 43, 64), skin)
        c.recolor((31, 32, 47, 47), skin, shade(skin, 0.85))
        c.rect((5, 43, 43, 47), (220, 220, 210))  # perizoma / panno
        return
    c.ell((5, 32, 43, 64), robe)
    c.recolor((31, 32, 47, 47), robe, shade(robe, 0.8))
    c.recolor((0, 32, 13, 47), robe, shade(robe, 1.15))
    if a == "apostolo":  # manto su una spalla
        mantle = (204, 160, 70) if robe[2] > robe[0] else (180, 60, 60)
        c.poly([(5, 47), (5, 38), (12, 33), (20, 33), (34, 47)], mantle)
        c.recolor((0, 32, 47, 47), mantle, mantle)
    elif a == "saio":
        c.line([(24, 35), (24, 47)], (230, 220, 190))  # cordone
        c.px(23, 44, (230, 220, 190)); c.px(25, 45, (230, 220, 190))
    elif a == "domenicano":
        c.poly([(5, 47), (6, 37), (13, 33), (19, 34), (17, 47)], BLACK)
        c.poly([(43, 47), (42, 37), (35, 33), (29, 34), (31, 47)], BLACK)
    elif a in ("vescovo", "papa"):
        c.rect((21, 34, 27, 47), GOLD)              # stola / pallio
        c.rect((22, 34, 26, 47), shade(GOLD, 1.1))
        c.rect((23, 38, 25, 40), robe)              # croce sulla stola
        c.px(24, 37, robe); c.px(24, 41, robe)
        if a == "papa":
            c.poly([(6, 40), (10, 34), (20, 32), (28, 32), (38, 34), (42, 40), (24, 44)], RED)  # mozzetta
            c.rect((22, 34, 26, 47), GOLD)
    elif a == "cardinale":
        c.poly([(6, 40), (10, 34), (20, 32), (28, 32), (38, 34), (42, 40), (24, 44)], shade(RED, 0.9))
    elif a in ("armatura", "crociato"):
        c.ell((5, 32, 43, 64), STEEL)
        c.recolor((31, 32, 47, 47), STEEL, STEEL_DARK)
        c.recolor((0, 32, 13, 47), STEEL, STEEL_LIGHT)
        c.ell((4, 32, 16, 40), STEEL_LIGHT)          # spallacci
        c.ell((32, 32, 44, 40), STEEL_DARK)
        if a == "crociato":
            c.rect((14, 36, 34, 47), WHITE)
            c.rect((22, 37, 26, 47), RED)
            c.rect((17, 40, 31, 43), RED)
    elif a == "regale":
        c.poly([(6, 40), (10, 34), (20, 32), (28, 32), (38, 34), (42, 40), (24, 43)], WHITE)  # ermellino
        for x, y in ((12, 37), (18, 39), (24, 40), (30, 39), (36, 37)):
            c.px(x, y, BLACK)
    elif a == "suora":
        c.poly([(14, 33), (34, 33), (31, 41), (24, 43), (17, 41)], WHITE)  # soggolo sul petto


def draw_head(c, t, skin):
    c.rect((21, 28, 27, 34), shade(skin, 0.88))   # collo
    c.ell((16, 10, 32, 30), skin)                 # testa
    c.recolor((29, 10, 33, 30), skin, shade(skin, 0.9))
    c.ell((14, 18, 17, 23), skin)                 # orecchie
    c.ell((31, 18, 34, 23), shade(skin, 0.9))


def draw_face(c, t, skin):
    ey = 20
    for x in (20, 27):
        c.px(x, ey, EYE); c.px(x, ey + 1, EYE)
        c.px(x + (1 if x == 20 else -1), ey, (250, 250, 250))  # luce negli occhi
    if t.eta == "anziano":
        c.line([(19, 18), (21, 18)], shade(skin, 0.7))
        c.line([(26, 18), (28, 18)], shade(skin, 0.7))
    c.px(24, 23, shade(skin, 0.78))               # naso
    c.px(23, 24, shade(skin, 0.85))
    c.line([(22, 26), (26, 26)], MOUTH)
    if t.donna:
        c.px(19, 24, (236, 150, 150)); c.px(29, 24, (236, 150, 150))
        c.line([(19, 19), (21, 19)], EYE); c.line([(26, 19), (28, 19)], EYE)  # ciglia
    if "ferita_fronte" in t.extra:
        c.px(24, 15, DARK_RED); c.px(24, 16, RED)


def draw_hair(c, t, hair, skin):
    st = t.capelli
    if st == "nessuno" or t.copricapo in ("velo", "cappuccio"):
        return
    if st == "calvo":
        c.rect((15, 17, 17, 24), hair); c.rect((31, 17, 33, 24), hair)  # corona di capelli ai lati
        c.px(22, 12, shade(skin, 1.12)); c.px(23, 12, shade(skin, 1.12))  # riflesso sulla pelata
        return
    if st == "tonsura":
        c.ell((15, 9, 33, 21), hair)
        c.ell((17, 13, 31, 31), skin)
        c.ell((19, 9, 29, 13), skin)              # chierica
        return
    if st == "lunghi":
        c.ell((14, 8, 34, 24), hair)
        c.rect((14, 16, 18, 38), hair); c.rect((30, 16, 34, 38), hair)
    elif st == "ricci":
        c.ell((14, 7, 34, 21), hair)
        for x in range(14, 35, 3):
            c.ell((x - 2, 6, x + 1, 9), hair)
        c.ell((13, 13, 16, 20), hair); c.ell((32, 13, 35, 20), hair)
    else:  # corti
        c.ell((15, 8, 33, 20), hair)
        c.rect((15, 14, 17, 20), hair); c.rect((31, 14, 33, 20), hair)
    c.ell((17, 13, 31, 31), skin)                 # ridisegna il viso sotto la frangia
    c.recolor((29, 13, 33, 31), skin, shade(skin, 0.9))


def draw_beard(c, t, hair):
    if t.barba == "corta":
        c.poly([(17, 22), (19, 28), (24, 32), (29, 28), (31, 22), (30, 27), (24, 30), (18, 27)], hair)
        c.ell((17, 23, 31, 33), hair)
        c.line([(21, 25), (27, 25)], hair)        # baffi
        c.line([(22, 27), (26, 27)], MOUTH)
    elif t.barba == "lunga":
        c.poly([(17, 23), (31, 23), (30, 36), (24, 42), (18, 36)], hair)
        c.line([(20, 25), (28, 25)], hair)
        c.line([(22, 27), (26, 27)], MOUTH)
        c.line([(21, 33), (23, 38)], shade(hair, 0.85)); c.line([(27, 33), (25, 38)], shade(hair, 0.85))


def draw_cover_back(c, t, robe):
    """Parts of the headwear that sit behind the face (veil, hood)."""
    if t.copricapo == "velo":
        c.ell((13, 6, 35, 30), robe if t.abito == "suora" else (70, 90, 150))
        c.rect((13, 18, 35, 40), robe if t.abito == "suora" else (70, 90, 150))
        c.ell((16, 10, 32, 32), WHITE)            # soggolo
    elif t.copricapo == "cappuccio":
        c.ell((12, 6, 36, 32), robe)
        c.recolor((30, 6, 36, 32), robe, shade(robe, 0.8))
        c.ell((15, 9, 33, 31), shade(robe, 0.55))  # interno in ombra


def draw_cover_front(c, t, skin):
    cp = t.copricapo
    if cp == "velo":
        c.ell((18, 13, 30, 29), skin)             # viso dentro il soggolo
    elif cp == "cappuccio":
        c.ell((17, 12, 31, 30), skin)
        c.recolor((29, 12, 31, 30), skin, shade(skin, 0.9))
    elif cp == "mitra":
        c.poly([(17, 13), (17, 4), (24, 0), (31, 4), (31, 13)], WHITE)
        c.recolor((27, 0, 31, 13), WHITE, (214, 210, 204))
        c.rect((23, 1, 25, 13), GOLD)
        c.rect((17, 11, 31, 13), GOLD)
    elif cp == "tiara":
        c.ell((18, 0, 30, 15), WHITE)
        for y in (4, 8, 12):
            c.line([(18, y), (30, y)], GOLD)
        c.px(24, 0, GOLD)
    elif cp == "corona":
        c.rect((17, 9, 31, 12), GOLD)
        for x in (17, 21, 24, 27, 31):
            c.line([(x, 6), (x, 9)], GOLD)
        c.px(24, 10, RED)
    elif cp == "elmo":
        c.ell((15, 6, 33, 20), STEEL)
        c.rect((15, 13, 33, 16), STEEL_DARK)
        c.ell((18, 14, 30, 30), skin)
    elif cp == "spine":
        for x in range(16, 33, 2):
            c.px(x, 12 + (x % 4 == 0), (90, 70, 40))


def draw_attribute(c, t):
    a = t.attributo
    if a == "chiavi":
        for dx, col in ((0, GOLD), (4, STEEL_LIGHT)):
            x = 37 + dx
            c.ell((x - 2, 22, x + 2, 26), col)
            c.d.point((x, 24), fill=(0, 0, 0, 0))  # anello della chiave
            c.line([(x, 26), (x, 44)], col)
            c.rect((x + 1, 40, x + 2, 41), col); c.rect((x + 1, 43, x + 2, 44), col)
    elif a == "frecce":
        for (x0, y0, x1, y1) in ((8, 33, 22, 44), (40, 30, 28, 42), (12, 46, 24, 38)):
            c.line([(x0, y0), (x1, y1)], (110, 80, 50))
            c.px(x0, y0, STEEL); c.px(x0 + (1 if x0 < x1 else -1), y0, (230, 230, 230))
    elif a == "palma":
        c.line([(41, 46), (41, 22)], DARK_GREEN)
        for y in range(23, 40, 3):
            c.line([(41, y), (37, y + 3)], GREEN); c.line([(41, y), (45, y + 3)], GREEN)
    elif a == "spada":
        c.line([(41, 14), (41, 38)], STEEL_LIGHT, 2)
        c.line([(37, 38), (45, 38)], GOLD)
        c.line([(41, 39), (41, 44)], (110, 70, 40))
        c.px(41, 45, GOLD)
    elif a == "lancia":
        c.line([(42, 2), (42, 47)], (130, 90, 50))
        c.poly([(42, 0), (40, 5), (44, 5)], STEEL_LIGHT)
    elif a in ("giglio", "rosa"):
        c.line([(40, 46), (40, 24)], DARK_GREEN)
        c.line([(40, 34), (37, 31)], GREEN); c.line([(40, 30), (43, 27)], GREEN)
        flower = WHITE if a == "giglio" else (210, 40, 70)
        for (x, y) in ((40, 20), (38, 22), (42, 22), (40, 23)):
            c.ell((x - 1, y - 1, x + 1, y + 1), flower)
        c.px(40, 22, GOLD if a == "giglio" else DARK_RED)
    elif a == "libro":
        c.rect((29, 36, 39, 45), (150, 40, 40))
        c.rect((30, 37, 38, 44), (176, 56, 50))
        c.line([(29, 45), (39, 45)], (240, 232, 200))
        c.rect((33, 39, 35, 41), GOLD)
    elif a == "croce":
        c.line([(41, 14), (41, 46)], (120, 80, 50), 2)
        c.line([(37, 20), (45, 20)], (120, 80, 50), 2)
    elif a == "pastorale":
        c.line([(41, 10), (41, 47)], GOLD_DARK, 2)
        c.ell((38, 3, 45, 11), GOLD)
        c.d.ellipse((40, 5, 43, 9), fill=(0, 0, 0, 0))  # riccio del pastorale: si vede lo sfondo
    elif a == "occhi":
        c.ell((31, 38, 45, 44), GOLD)
        c.ell((32, 39, 44, 43), GOLD_LIGHT)
        for x in (35, 40):
            c.ell((x - 1, 40, x + 1, 42), WHITE); c.px(x, 41, (60, 90, 160))
    if "stigmate" in t.extra:
        c.px(24, 39, DARK_RED)


def outline(layer):
    """Dark 1-px outline around everything drawn (on transparent neighbours)."""
    src = layer.copy()
    out = layer.copy()
    for y in range(S):
        for x in range(S):
            if src.getpixel((x, y))[3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < S and 0 <= ny < S and src.getpixel((nx, ny))[3]:
                    out.putpixel((x, y), OUTLINE + (255,))
                    break
    return out


def render(name, t):
    skin = SKINS[t.pelle if t.pelle is not None else [0, 1, 1, 2, 2, 3][h(name, "pelle") % 6]]
    hair = HAIRS[t.colore_capelli or ["nero", "castano", "castano", "biondo", "rosso", "nero"][h(name, "capelli") % 6]]
    if t.eta == "anziano" and not t.colore_capelli:
        hair = HAIRS["grigio" if h(name, "grigio") % 2 else "bianco"]
    robe = t.colore_abito or {
        "saio": BROWN_HABIT, "benedettino": BLACK_HABIT, "domenicano": WHITE, "suora": BLACK_HABIT,
        "cardinale": RED, "papa": WHITE,
    }.get(t.abito) or ROBES[h(name, "abito") % len(ROBES)]
    bg = BACKGROUNDS[h(name, "sfondo") % len(BACKGROUNDS)]

    halo = Canvas()
    draw_halo(halo, t)
    fig = Canvas()
    draw_body(fig, t, skin if t.abito == "nudo" else robe)
    draw_cover_back(fig, t, robe)
    draw_head(fig, t, skin)
    draw_hair(fig, t, hair, skin)
    draw_cover_front(fig, t, skin)
    draw_face(fig, t, skin)
    draw_beard(fig, t, hair)
    draw_attribute(fig, t)

    img = Image.new("RGBA", (S, S), bg + (255,))
    # Background: darker lower band for a bit of depth.
    ImageDraw.Draw(img).rectangle((0, 36, S, S), fill=shade(bg, 0.85) + (255,))
    img.alpha_composite(outline(halo.img))
    fig_o = outline(fig.img)
    img.alpha_composite(fig_o)
    return img.convert("RGB")


# --- Tratti da Wikidata -------------------------------------------------------

def wikidata_tratti(names):
    """Tratti dalle regole, per santi non in FAMOSI. Richiede la rete."""
    spec = importlib.util.spec_from_file_location("gs", ROOT / "tools/genera_santi.py")
    gs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gs)
    people = gs.collect(gs.fetch())
    qids = {gs.display_name(p): q for q, p in people.items()}
    wanted = {qids[n]: n for n in names if n in qids}
    if not wanted:
        return {}
    query = """SELECT ?item ?propLabel ?valLabel ?birth WHERE {
      VALUES ?item { %s }
      OPTIONAL { ?item wdt:P569 ?birth }
      OPTIONAL { VALUES ?p { wdt:P39 wdt:P611 wdt:P106 wdt:P1196 } ?item ?p ?val.
                 BIND(STR(?p) AS ?propLabel) }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }""" % " ".join("wd:" + q for q in wanted)
    facts = {n: {"labels": [], "birth": None} for n in wanted.values()}
    for row in gs.fetch(query):
        n = wanted[row["item"]["value"].rsplit("/", 1)[1]]
        if "valLabel" in row:
            facts[n]["labels"].append(row["valLabel"]["value"].lower())
        if "birth" in row and facts[n]["birth"] is None:
            facts[n]["birth"] = int(row["birth"]["value"][:5].lstrip("+").split("-")[0] or 0)
    out = {}
    for q, n in wanted.items():
        p = people[q]
        out[n] = regole(n, p["female"], not p["saint"], " | ".join(facts[n]["labels"]), facts[n]["birth"])
    return out


def regole(name, donna, beato, labels, birth):
    t = Tratti(donna=donna, beato=beato)
    has = lambda *ws: any(w in labels for w in ws)  # noqa: E731
    t.eta = ["giovane", "adulto", "adulto", "anziano"][h(name, "eta") % 4]
    if donna:
        t.capelli = "lunghi"
    else:
        t.capelli = ["corti", "corti", "ricci", "calvo"][h(name, "taglio") % 4]
        t.barba = ["nessuna", "corta", "lunga"][h(name, "barba") % 3] if (birth or 0) < 1600 else "nessuna"
    if has("pope"):
        t.copricapo, t.abito, t.attributo, t.barba = "tiara", "papa", "croce", "nessuna" if (birth or 0) > 1500 else t.barba
    elif has("cardinal"):
        t.abito, t.attributo = "cardinale", "libro"
    elif has("bishop", "archbishop", "patriarch"):
        t.copricapo, t.abito, t.attributo = "mitra", "vescovo", "pastorale"
    elif has("franciscan", "capuchin", "friars minor", "poor clares", "conventual"):
        t.abito, t.capelli = "saio", ("tonsura" if not donna else t.capelli)
        if donna:
            t.copricapo, t.abito, t.colore_abito = "velo", "suora", BROWN_HABIT
    elif has("dominican", "order of preachers"):
        t.abito, t.capelli = "domenicano", ("tonsura" if not donna else t.capelli)
        if donna:
            t.copricapo, t.abito, t.colore_abito = "velo", "suora", BLACK_HABIT
    elif has("benedictine", "cistercian", "trappist", "carthusian", "abbot", "monk"):
        t.abito, t.capelli = "benedettino", ("tonsura" if not donna else t.capelli)
        if donna:
            t.copricapo, t.abito, t.colore_abito = "velo", "suora", BLACK_HABIT
    elif donna and has("nun", "religious sister", "abbess", "carmelite", "ursuline", "sisters"):
        t.copricapo, t.abito, t.colore_abito = "velo", "suora", BLACK_HABIT
    elif has("king", "monarch", "emperor", "prince", "queen", "duke", "empress", "princess"):
        t.copricapo, t.abito = "corona", "regale"
        t.colore_abito = (120, 40, 120) if h(name, "re") % 2 else (150, 40, 50)
    elif has("soldier", "knight", "military"):
        t.abito, t.attributo = "armatura", "spada"
    elif has("priest", "jesuit", "presbyter", "missionary"):
        t.abito, t.colore_abito, t.attributo = "tunica", BLACK, "libro"
    if t.attributo == "nessuno" and has("martyr", "execution", "decapitation", "killed", "homicide", "crucifixion"):
        t.attributo = "palma"
    elif t.attributo == "nessuno":
        t.attributo = ["nessuno", "libro", "croce", "giglio"][h(name, "attr") % 4]
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nomi", required=True)
    ap.add_argument("--out", default=str(Path.home() / "mannaggia-avatar-prova"))
    ap.add_argument("--zoom", type=int, default=6)
    args = ap.parse_args()
    names = [l.strip() for l in open(args.nomi, encoding="utf-8") if l.strip()]
    tratti = {n: FAMOSI[n] for n in names if n in FAMOSI}
    tratti.update(wikidata_tratti([n for n in names if n not in FAMOSI]))
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    tiles = []
    for n in names:
        if n not in tratti:
            print(f"  non trovato: {n}", file=sys.stderr)
            continue
        img = render(n, tratti[n])
        img.save(out / f"{hashlib.sha1(n.encode()).hexdigest()[:12]}.png")
        tiles.append((n + ("" if n in FAMOSI else " *"), img))

    z, cols = args.zoom, 5
    cell = S * z
    sheet = Image.new("RGB", (cols * (cell + 12) + 12, ((len(tiles) + cols - 1) // cols) * (cell + 30) + 12), (28, 28, 28))
    d = ImageDraw.Draw(sheet)
    for i, (n, img) in enumerate(tiles):
        x = 12 + (i % cols) * (cell + 12)
        y = 12 + (i // cols) * (cell + 30)
        sheet.paste(img.resize((cell, cell), Image.NEAREST), (x, y))
        d.text((x, y + cell + 6), n, fill=(230, 230, 230))
    sheet.save(out / "provino.png")
    print(f"{len(tiles)} avatar in {out} (* = tratti dalle regole Wikidata)", file=sys.stderr)


if __name__ == "__main__":
    main()
