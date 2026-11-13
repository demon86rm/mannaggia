"""Exports the saints for the 96 px generator (ritratti96.px.js) as tratti96.data.js
(var TRATTI = [...]), in the vocabulary of libreria96.px.js. The rules stay in avatar.py
(FAMOSI, PELLE, regole(), the Wikidata cache, the name hashes for skin, hair, robe and
background), so every saint keeps the identity it has in today's album. Traits the library
has no part for fall back to a generic one, listed in ripieghi.tsv.

    ~/venv/ritratti/bin/python -I esporta.py --repo ~/Git/mannaggia-android/android [--campione 30]
"""
import argparse, collections, importlib.util, json, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True, help="the android folder of the repo")
ap.add_argument("--campione", type=int, default=0, help="only N saints per category (0 = all)")
ap.add_argument("--nomi", help="only these saints (one per line)")
ap.add_argument("--out", default=str(Path(__file__).with_name("tratti96.data.js")))
args = ap.parse_args()
repo = Path(args.repo).expanduser()
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location("avatar", repo / "tools/ritratti/avatar.py")
av = importlib.util.module_from_spec(spec)
spec.loader.exec_module(av)

hexc = lambda c: "#%02x%02x%02x" % tuple(c[:3])
names = [l.strip() for l in open(repo / "app/src/main/assets/santi.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
facts = av.wikidata_facts(names, repo / "tools/ritratti/tratti_wikidata.json")
leggendari = {l.strip() for l in open(repo / "app/src/main/assets/avatar/leggendari.txt", encoding="utf-8") if l.strip() and not l.startswith("#")}
IRIDI = ["#5a4636", "#5a4636", "#6b4a30", "#4c6a8a", "#5a6a3e", "#6a5a4a"]   # brown most often

# Face features of the 96 px portraits for the saints of other peoples (the 48 px ones have no
# such detail): nose, lips, eye shape, hair type; dark eyes. Same saints as PELLE in avatar.py.
AFRICANI = ["Santa Giuseppina Bakhita", "San Mosè l'Etiope", "Beata Maria Clementina Anuarite Nengapeta",
            "Beato Isidore Bakanja", "Santa Sara la Nera", "San Martino de Porres", "San Carlo Lwanga", "San Kizito",
            "San Joseph Mukasa", "San Gyaviira Mayanja Musoke", "Sant'Achilleo Kiwanuka", "Sant'Ambrogio Kibuuka",
            "Sant'Andrea Kaggwa", "Beato Davide Okelo", "Beato Gildo Irwa", "San John Coltrane"]
ASIA_EST = ["San Paolo Miki", "Sant'Agostino Zhao Rong"]
UGANDA = ["San Carlo Lwanga", "San Kizito", "San Joseph Mukasa", "San Gyaviira Mayanja Musoke", "Sant'Achilleo Kiwanuka",
          "Sant'Ambrogio Kibuuka", "Sant'Andrea Kaggwa", "Beato Davide Okelo", "Beato Gildo Irwa"]
BARBE_UGANDA = {"San Joseph Mukasa": {"barba": "baffi"}, "Sant'Andrea Kaggwa": {"barba": "corta", "colore_barba": "#4a3a30"}}   # a tone lighter: black merged with his skin
VOLTO = {**{n: {"naso": "largo", "labbra": "piene", "capelli": "afro", "iride": "#6b4a30"} for n in AFRICANI},
         **{n: {"occhi": "mono", "capelli": "lisci", "iride": "#6b4a30"} for n in ASIA_EST},
         "Sant'Andrea Kim Taegon": {"occhi": "mono", "capelli": "lisci", "iride": "#6b4a30", "copricapo": "gat", "abito": "hanbok"},
         "San Lorenzo Ruiz": {"capelli": "lisci", "iride": "#6b4a30"},
         "Santa Kateri Tekakwitha": {"capelli": "trecce", "iride": "#6b4a30", "abito": "coperta", "secondo": "#2a4a8a"},
         "San Juan Diego Cuauhtlatoatzin": {"capelli": "lunghi_lisci", "iride": "#6b4a30", "abito": "tilma", "secondo": "#c8a878"}}

# library vocabulary: what avatar.py calls a trait -> the part of libreria96.px.js
ABITI = {"tunica", "mantello", "suora", "domenicano", "saio", "talare", "vescovo", "benedettino", "cistercense", "regale",
         "papa", "cardinale", "armatura", "moderno", "dalmatica", "hanbok", "coperta", "tilma",
         "crociato", "pelliccia", "righe", "nudo", "camice", "sari"}                       # the last six: parti96.px.js
ABITO_ALIAS = {"apostolo": "mantello"}
COPRICAPI = {"velo", "cappuccio", "mitra", "corona", "tiara", "zucchetto_rosso", "zucchetto_bianco", "gat",
             "pellegrino", "corona_rose", "elmo", "sari"}
ATTRIBUTI = {"palma", "croce", "giglio", "libro", "pastorale", "bastone", "scopa", "rosa", "spada", "sassofono",
             # parti96.px.js
             "chiavi", "ruota", "drago", "agnello", "leone", "colomba", "teschio", "bambino", "cane", "penna", "ihs", "vaso",
             "citta", "cuore", "tenaglia", "coltello", "candele", "arpa", "caritas", "conchiglia", "aquila", "graticola", "bue",
             "ascia", "palle", "trifoglio", "frecce", "sega", "frusta", "maialino", "torre", "organo", "ostensorio", "occhi",
             "pietre", "pesce", "lancia"}
ATTR_ALIAS = {"crocifisso": "croce", "croce_x": "croce", "tau": "croce", "rosario": "croce", "bordone": "bastone",
              "bordone_provola": "bastone"}
# extras drawn by parti96.px.js; the others (glasses on the eyes, the stigmata on the hands) are left out
EXTRA = {"croce_rossa", "stella", "medaglione", "fiamma", "mantello", "sole_petto", "spine", "stelle", "manto_azzurro", "ferita_fronte"}
CAPELLI = {"corti": "corti", "lunghi": "lunghi", "ricci": "ricci", "calvo": "calvo", "tonsura": "tonsura", "nessuno": "calvo"}
ripieghi = collections.Counter()
esempi = collections.defaultdict(list)


def tratti(n):
    f = facts.get(n)
    if n in av.FAMOSI:
        return av.FAMOSI[n]
    if f:
        return av.regole(n, f["female"], f["beato"], " | ".join(f["labels"]), f["birth"])
    return av.regole(n, n.startswith(("Santa", "Beata")), n.startswith("Beat"), "", None)


def ripiego(n, kind, val):
    ripieghi[(kind, val)] += 1
    if len(esempi[(kind, val)]) < 3:
        esempi[(kind, val)].append(n)


def voce(n):
    t, h = tratti(n), av.h
    # the same choices as avatar.render()
    skin = av.pelle_di(n, t)
    hair = av.HAIRS[t.colore_capelli or ("nero" if n in av.PELLE else None)
                    or ["nero", "castano", "castano", "biondo", "rosso", "nero"][h(n, "capelli") % 6]]
    if t.eta == "anziano" and not t.colore_capelli:
        hair = av.HAIRS["grigio" if h(n, "grigio") % 2 else "bianco"]
    robe = t.colore_abito or {
        "saio": av.BROWN_HABIT, "benedettino": av.BLACK_HABIT, "domenicano": av.WHITE, "suora": av.BLACK_HABIT,
        "cardinale": av.RED, "papa": av.WHITE, "cistercense": av.WHITE, "talare": av.BLACK_HABIT,
        "dalmatica": (170, 40, 50), "camice": av.WHITE,
    }.get(t.abito) or av.ROBES[h(n, "abito") % len(av.ROBES)]
    cat = av.categoria(t)
    bg = av.BG_CATEGORIA.get(cat) or av.BACKGROUNDS[h(n, "sfondo") % len(av.BACKGROUNDS)]
    abito = ABITO_ALIAS.get(t.abito, t.abito)
    if abito not in ABITI:
        ripiego(n, "abito", t.abito); abito = "tunica"
    elif t.abito in ABITO_ALIAS:
        ripiego(n, "abito", t.abito)
    cop = t.copricapo if t.copricapo in COPRICAPI else None
    if t.copricapo not in COPRICAPI and t.copricapo != "nessuno":
        ripiego(n, "copricapo", t.copricapo)
    # up to two attributes the library can draw: the first on the right, the second mirrored on the left
    attrs = [ATTR_ALIAS.get(a, a) for a in t.attributo.split("+") if ATTR_ALIAS.get(a, a) in ATTRIBUTI][:2]
    attr = attrs[0] if attrs else None
    for a in t.attributo.split("+"):
        if a != "nessuno" and ATTR_ALIAS.get(a, a) not in ATTRIBUTI:
            ripiego(n, "attributo", a)
    for e in t.extra:
        if e not in EXTRA:
            ripiego(n, "extra", e)
    d = {"n": n, "id": av.file_id(n), "cat": cat or "altro", "leggendario": n in leggendari, "famoso": n in av.FAMOSI,
         "donna": t.donna, "beato": t.beato, "eta": t.eta, "capelli": CAPELLI.get(t.capelli, "corti"), "barba": t.barba,
         "copricapo": cop, "abito": abito, "attributo": attr, "attributi": attrs, "martire": t.martire,
         "extra": [e for e in t.extra if e in EXTRA],
         "pelle": hexc(skin), "chioma": hexc(hair), "veste": hexc(robe), "sfondo": hexc(bg),
         "velo": hexc(av.veil_color(t, robe)) if cop == "velo" else None,
         "secondo": hexc(av.ROBES[h(n, "manto") % len(av.ROBES)]) if abito == "mantello" else None,
         "iride": IRIDI[h(n, "iride") % len(IRIDI)], "guance": t.donna or t.eta == "giovane"}
    if abito == "regale":                   # the mantle in the colour avatar.py gives kings (red or purple)
        d["secondo"], d["veste"] = d["veste"], "#e8dcc0"
    # face variants, fixed by the name (as the colours): face shape, nose, mouth, curly-hair style, hairline
    d.update({"viso": h(n, "viso") % 3, "naso_v": h(n, "naso") % 3, "bocca": h(n, "bocca") % 3,
              "afro_v": h(n, "afro") % 3, "attacc": h(n, "attaccatura") % 3 - 1})
    if n in UGANDA and h(n, "kanzu") % 2:   # the barkcloth over the shoulder, on the white kanzu
        d.update({"abito": "mantello", "veste": "#ece6da", "secondo": "#9a5032"})
    d.update(BARBE_UGANDA.get(n, {}))       # the grown men among the martyrs, not the young pages
    v = VOLTO.get(n, {})
    d.update(v)
    if v.get("capelli") == "afro" and t.capelli in ("calvo", "tonsura", "nessuno"):
        d["capelli"] = CAPELLI[t.capelli]   # bald stays bald
    return d


sel = names
if args.nomi:
    tutti = set(names)
    sel = [l.strip() for l in open(args.nomi, encoding="utf-8") if l.strip() in tutti]
voci = [voce(n) for n in sel]
if args.campione:
    per = {}
    for v in sorted(voci, key=lambda v: av.h(v["n"], "campione")):
        per.setdefault(v["cat"], [])
        if len(per[v["cat"]]) < args.campione:
            per[v["cat"]].append(v)
    voci = [v for c in sorted(per) for v in per[c]]
Path(args.out).write_text("// Generated by esporta.py from avatar.py: do not edit.\nvar TRATTI = "
                          + json.dumps(voci, ensure_ascii=False) + "\n", encoding="utf-8")
with open(Path(args.out).with_name("ripieghi.tsv"), "w", encoding="utf-8") as out:
    out.write("# tipo\ttratto di avatar.py\tsanti\tesempi (tratti senza una parte a 96 px: parte generica o niente)\n")
    for (k, v), c in ripieghi.most_common():
        out.write(f"{k}\t{v}\t{c}\t{'; '.join(esempi[(k, v)])}\n")
print(f"{len(voci)} santi -> {args.out}; ripieghi: {sum(ripieghi.values())} in {len(ripieghi)} tratti", file=sys.stderr)
