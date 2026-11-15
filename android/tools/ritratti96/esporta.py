"""Exports the saints for the 96 px generator (ritratti96.px.js) as tratti96.data.js
(var TRATTI = [...]), in the vocabulary of libreria96.px.js. The rules stay in avatar.py
(FAMOSI, PELLE, regole(), the Wikidata cache, the name hashes for skin, hair, robe and
background), so every saint keeps the identity it has in today's album. Traits the library
has no part for fall back to a generic one, listed in ripieghi.tsv.

    ~/venv/ritratti/bin/python -I esporta.py --repo ~/Git/mannaggia-android/android [--campione 30]
"""
import argparse, collections, importlib.util, json, sys
from dataclasses import replace
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
# men's cuts by hair family, and by age where one of them is a receding hairline (corti 2, calvo 3) or
# the hair left at the sides (calvo 2)
TAGLI = {"corti": {"giovane": (1, 1, 3, 3, 4, 4, 5, 5, 2), "adulto": (1, 2, 3, 4, 5), "anziano": (2, 2, 2, 1, 3, 4, 5)},
         "ricci": (1, 2, 3), "tonsura": (1, 2),
         "calvo": {"giovane": (1, 1, 3), "adulto": (1, 2, 3, 3), "anziano": (1, 2, 2, 3)}}
CAPELLI = {"corti": "corti", "lunghi": "lunghi", "ricci": "ricci", "calvo": "calvo", "tonsura": "tonsura", "nessuno": "calvo"}
# women the old rules of avatar.py dress as a priest (labels "missionary", "deaconess", "priest"): the four
# religious wear the nun's habit and veil, the other nine the tunic (the user's decision, 2026-11-15)
RELIGIOSE = {"Santa Giulia Billiart", "Santa Marguerite Bourgeoys", "Santa Maria Troncatti", "Beata Maria Teresa Ledóchowska"}
# what the rules by birth year cannot know (the user's decisions, 2026-11-15), laid over them: San Hoel, a
# Breton king of the 6th century with no year on Wikidata; Beata Nera Tolomei, of the 13th century, whom
# Wikidata dates to 300; San Cirillo VI, a Coptic pope, not a Roman one (black cassock, no headwear until the
# headwear is redrawn)
ECCEZIONI = {"San Hoel": {"regale_v": 2, "corona_v": 2},
             "Beata Nera Tolomei": {"tunica_v": 0},
             "San Giosafat Kuncewycz": {"mitra_v": 2},     # a Greek Catholic bishop, with no Eastern label
             "San Cirillo VI di Alessandria": {"abito": "talare", "talare_v": 1, "veste": "#2c282e", "copricapo": None,
                                               "barba": "lunga", "chioma": "#e8e4dc"}}
ripieghi = collections.Counter()
esempi = collections.defaultdict(list)


def orientale(lab):
    """Eastern, by Wikidata's labels in lower case; a Latin patriarch of an Eastern see is not."""
    return "latin patriarch" not in lab and any(
        k in lab for k in ("orthodox", "constantinople", "byzantine", "coptic", "armenian", "syriac"))


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
    cat = av.categoria(t)                   # the background's category, before the change of dress below
    if t.donna and t.abito == "talare":
        t = replace(t, abito="suora", copricapo="velo") if n in RELIGIOSE else replace(t, abito="tunica")
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
    if abito == "vescovo":                  # cope, chasuble with a Y orphrey, chasuble with the pallium (ABITI.vescovo)
        d["vescovo_v"] = h(n, "paramenti") % 3
    # the mitre (COPRICAPI.mitra in libreria96), the user's rules of 2026-11-15, by birth year: by 1000 or with
    # no year the low plain one (1), the mitre being born low about then; after 1000 the Eastern bishops, by
    # Wikidata's labels, their crown (2), which is late; of the others 1001-1500 the precious one (0), after
    # 1500 the tall one in cloth of gold (3). "patriarch" alone is not Eastern: Aquileia had Latin ones, and so
    # had Constantinople (San Pietro Tommaso)
    if d.get("copricapo") == "mitra":
        f = facts.get(n) or {}
        lab, nato = " | ".join(f.get("labels", [])).lower(), f.get("birth")
        d["mitra_v"] = 1 if nato is None or nato <= 1000 else 2 if orientale(lab) else 0 if nato <= 1500 else 3
    # the cross and the staff in the hand (ATTRIBUTI96 in libreria96), the user's rules of 2026-11-15. The cross:
    # gold (1) for popes, cardinals and sovereigns; the Eastern one with three bars (3) by Wikidata's labels;
    # a crucifix (2), a modern devotion, for those born after 1500; plain wood (0) for the rest. The staff: the
    # tau one of the desert monks (1) for those born by 600, the knobbed stick (0) for the others. A cross
    # already on the chest stays: the user wants both
    f = facts.get(n) or {}
    if "croce" in attrs:
        d["croce_v"] = (1 if d["abito"] in ("papa", "regale", "cardinale") else 3 if orientale(" | ".join(f.get("labels", [])).lower())
                        else 2 if (f.get("birth") or 0) > 1500 else 0)
    if "bastone" in attrs:
        d["bastone_v"] = int(f.get("birth") is not None and f["birth"] <= 600)
    # women's long hair: one of five styles (pieghe6 in libreria96), from the name; no bun (3) under a crown.
    # The old geometric cut (0) is no longer given to women: the user found it unnatural
    if d.get("donna") and d.get("capelli") == "lunghi":
        d["piega"] = (1, 2, 4, 5)[h(n, "piega") % 4] if d.get("copricapo") else 1 + h(n, "piega") % 5
    if n in UGANDA and h(n, "kanzu") % 2:   # the barkcloth over the shoulder, on the white kanzu
        d.update({"abito": "mantello", "veste": "#ece6da", "secondo": "#9a5032"})
    d.update(ECCEZIONI.get(n, {}))          # here for the dress, and again at the end for the variants
    d.update(BARBE_UGANDA.get(n, {}))       # the grown men among the martyrs, not the young pages
    v = VOLTO.get(n, {})
    d.update(v)
    if v.get("capelli") == "afro" and t.capelli in ("calvo", "tonsura", "nessuno"):
        d["capelli"] = CAPELLI[t.capelli]   # bald stays bald
    # the tunic (ABITI.tunica in libreria96): clavi (1) and the draped one with fibulae (2) are ancient dress,
    # for those born by the year 600; the later ones wear the plain round neck (0). Where Wikidata gives no
    # birth year, half and half from the name, but a blessed gets the round neck (nearly all of them are
    # medieval or modern). Among the ancient, clavi for two men in three, the drape
    # for two women in three (the user's rules, 2026-11-14)
    if d["abito"] == "tunica":
        nato = (facts.get(n) or {}).get("birth")
        antico = nato <= 600 if nato is not None else not d["beato"] and h(n, "epoca96") % 2 == 0
        d["tunica_v"] = 0 if not antico else 1 if (h(n, "tunica96") % 3 < 2) != bool(d["donna"]) else 2
    # the cassock (ABITI.talare in libreria96), the user's rules of 2026-11-14: born by 1500, before the Roman
    # collar, a priest's chasuble (3); then a missionary (Wikidata's labels) the crucifix on a cord (1); a
    # martyr the surplice and a red stole (2); of the others one in three the surplice and stole, two the
    # shoulder cape (0). d.stola: the stole's or the chasuble's colour, red for a martyr, else from the name.
    if d["abito"] == "talare":
        f = facts.get(n) or {}
        antico = f.get("birth") is not None and f["birth"] <= 1500
        if antico:
            v = 3
        elif any("missionar" in l.lower() for l in f.get("labels", [])):
            v = 1
        else:
            v = 2 if d["martire"] or h(n, "talare96") % 3 == 0 else 0
        d["talare_v"] = v
        if v >= 2:
            d["stola"] = "#a8283a" if d["martire"] else ("#3c785a", "#6a3a7c", "#e8e0cc" if v == 3 else "#d0a030")[h(n, "stola96") % 3]
    # the nun's habit (ABITI.suora in libreria96), the user's rules of 2026-11-14: the scapular (2) for the
    # orders that wear it, by Wikidata's labels; a crucifix on the guimpe (1) for the other nuns born after
    # 1500, the modern congregations; the wide guimpe alone (0) for the rest
    if d["abito"] == "suora":
        f = facts.get(n) or {}
        lab = " | ".join(f.get("labels", [])).lower()
        d["suora_v"] = (2 if any(k in lab for k in ("benedictin", "cistercian", "carmel", "dominic"))
                        else 1 if f.get("birth") is not None and f["birth"] > 1500 else 0)
    # the Benedictine (ABITI.benedettino in libreria96), the user's rules of 2026-11-14: an abbot (Wikidata's
    # labels) the gold cross on the scapular (1); of the others half the scapular (0), half the choir cowl (2)
    if d["abito"] == "benedettino":
        abate = any("abbot" in l.lower() for l in (facts.get(n) or {}).get("labels", []))
        d["benedettino_v"] = 1 if abate else 2 * (h(n, "benedettino96") % 2)
    # the friar's habit (ABITI.saio in libreria96), the user's rules of 2026-11-14, by Wikidata's labels: a
    # Carmelite the white mantle (3); a hermit the patched habit (2). The cord (0) and the wooden tau (1)
    # are Franciscan: half and half, but only for one of a Franciscan order or born after 1200; the earlier
    # monks, and those with neither a year nor an order, wear the patched habit
    if d["abito"] == "saio":
        f = facts.get(n) or {}
        lab = " | ".join(f.get("labels", [])).lower()
        francescano = any(k in lab for k in ("francisc", "friars minor", "capuchin", "poor clares")) or (f.get("birth") or 0) > 1200
        d["saio_v"] = 3 if "carmel" in lab else 2 if "hermit" in lab or not francescano else h(n, "saio96") % 2
    # kings and queens (ABITI.regale and COPRICAPI.corona in libreria96), the user's rules of 2026-11-14, robe
    # and crown together: Byzantine (1) for the sovereigns of the East, by Wikidata's labels, and the Roman
    # emperors born by 600; the mantle with a brooch and the circlet (2) for the others born by 1000; ermine
    # and the pointed crown (0), later fashions, for the rest
    if d["abito"] == "regale":
        f = facts.get(n) or {}
        lab, nato = " | ".join(f.get("labels", [])).lower(), f.get("birth")
        oriente = any(k in lab for k in ("byzantine", "kiev", "russia", "georgia", "armenia")) or (
            "roman emperor" in lab and "holy roman emperor" not in lab and nato is not None and nato <= 600)
        d["regale_v"] = d["corona_v"] = 1 if oriente else 2 if nato is not None and nato <= 1000 else 0
    # the popes (ABITI.papa and COPRICAPI.tiara in libreria96), the user's rules of 2026-11-14, by birth year:
    # after 1500, or with the skullcap, the mozzetta and stole (0); 601-1500 the cope (1); by 600 or with no
    # year, the early popes, the chasuble with the pallium (2), red for a martyr. The tiara has one crown
    # (1) for those born by 1250 or with no year, three (0) after
    if d["abito"] == "papa":
        nato = (facts.get(n) or {}).get("birth") or 0
        d["papa_v"] = 0 if nato > 1500 or d.get("copricapo") != "tiara" else 1 if nato > 600 else 2
        d["tiara_v"] = 0 if nato > 1250 else 1
        if d["papa_v"] == 2 and d["martire"]:
            d["stola"] = "#a8283a"
    # soldiers (ABITI.armatura in libreria96), the user's rules of 2026-11-14, by birth year: by 600 or with
    # no year (ancient martyrs) the Roman centurion's cuirass (1); 601-1300 mail (2); 1301-1700 plate (0);
    # after 1700 a uniform (3)
    if d["abito"] == "armatura":
        nato = (facts.get(n) or {}).get("birth") or 0
        d["armatura_v"] = 1 if nato <= 600 else 2 if nato <= 1300 else 0 if nato <= 1700 else 3
    # Dominicans, Cistercians and cardinals (libreria96), the user's rules of 2026-11-14. A Dominican: half
    # with the black cappa (0), half in white (1), from the name. A Cistercian: the black scapular (0), or all
    # in white (1) for a Carthusian, by Wikidata's labels. A cardinal: ermine (1) if born by 1500 or with no
    # year, the mozzetta and a pectoral cross (0) after
    if d["abito"] == "domenicano":
        d["domenicano_v"] = h(n, "domenicano96") % 2
    if d["abito"] == "cistercense":
        d["cistercense_v"] = int("carthusian" in " | ".join((facts.get(n) or {}).get("labels", [])).lower())
    if d["abito"] == "cardinale":
        d["cardinale_v"] = int(((facts.get(n) or {}).get("birth") or 0) <= 1500)
    # the mantle (ABITI.mantello) lies on the tunic: with the clavi (1) for the apostles and the other ancient
    # ones; the plain round neck (0) only for the modern (the Uganda martyrs' kanzu). The limit is 1500, not
    # 600: Wikidata gives San Pietro the year 1260. Modern dress (ABITI.moderno): the collar
    # open (0) for those born after 1970, a tie (1) for the others
    if d["abito"] == "mantello":
        d["tunica_v"] = int(((facts.get(n) or {}).get("birth") or 0) <= 1500)
    if d["abito"] == "moderno":
        d["moderno_v"] = int(((facts.get(n) or {}).get("birth") or 0) <= 1970)
    # men's hair: one of the family's cuts (tagli6 in libreria96), from the name. The old shapes (0) are no
    # longer given: the user replaced them all. Receding hair tends to come with age
    tg = None if d.get("donna") else TAGLI.get(d["capelli"])
    if tg:
        tg = tg.get(d["eta"], tg["adulto"]) if isinstance(tg, dict) else tg
        d["taglio"] = tg[h(n, "taglio96") % len(tg)]   # not "taglio": avatar.py draws the hair family with that one
    # the lily (ATTRIBUTI96.giglio), the user's rules of 2026-11-15: a Western sovereign the gold sceptre with
    # the fleur-de-lis (2); the others, the Eastern sovereigns among them, the flower: of them two in three
    # the stalk with three open flowers (0), one in three an open flower and two buds (1), from the name.
    # Here, after the robes: it reads regale_v
    if "giglio" in attrs:
        d["giglio_v"] = 2 if d["abito"] == "regale" and d.get("regale_v") != 1 else int(h(n, "giglio96") % 3 == 0)
    # the martyr's palm (ATTRIBUTI96.palma), the user's rules of 2026-11-15: a sovereign, crowned already, the
    # frond alone (0); of the others one in three the frond with the gold laurel wreath (1), from the name
    if "palma" in attrs:
        d["palma_v"] = 0 if d["abito"] == "regale" else int(h(n, "palma96") % 3 == 0)
    # the sword (ATTRIBUTI96.spada), the user's rules of 2026-11-15: of the armour's age, so that blade and
    # cuirass match: the centurion the gladius (1), the uniform the sabre (2), mail and plate the medieval
    # sword (0); San Paolo, in the apostle's mantle, the long sword of his iconography (0)
    if "spada" in attrs:
        d["spada_v"] = {1: 1, 3: 2}.get(d.get("armatura_v"), 0)
    # the book (ATTRIBUTI96.libro), the user's rules of 2026-11-15: the gold gospel book (1) for cardinals,
    # bishops, popes and sovereigns; open (2) for writers, theologians and doctors of the Church, by Wikidata's
    # labels; a leather codex (0) for the rest, its colour (libro_c) from the name
    if "libro" in attrs:
        lab = " | ".join((facts.get(n) or {}).get("labels", [])).lower()
        d["libro_v"] = (1 if d["abito"] in ("cardinale", "vescovo", "papa", "regale")
                        else 2 if any(k in lab for k in ("writer", "theologian", "doctor of the church")) else 0)
        d["libro_c"] = h(n, "libro96") % 4
    d.update(ECCEZIONI.get(n, {}))
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
