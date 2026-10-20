"""Misura quanti santi di santi.txt hanno origine non italiana (Wikidata) o grafia non italiana.

Uso (dalla cartella mannaggia-android):
    python3 -I tools/tts/origine_santi.py tools/genera_santi.py app/src/main/assets/santi.txt origine_santi.tsv

Il TSV prodotto (santo, origine, grafia_strana, qid) serve a pronuncia_auto.py --qid.
"""
import collections, csv, importlib.util, re, sys

spec = importlib.util.spec_from_file_location("gs", sys.argv[1])
gs = importlib.util.module_from_spec(spec); spec.loader.exec_module(gs)
santi_txt = set(l.strip() for l in open(sys.argv[2], encoding="utf-8") if l.strip() and not l.startswith("#"))

ITALIA = {"Q38", "Q237", "Q238"}  # Italia, Vaticano, San Marino (paese attuale del luogo)
gs.QUERY = gs.QUERY.replace("SELECT ?item ?label ?status ?gender",
                            "SELECT ?item ?label ?status ?gender ?birthCountry ?citizen") \
    .replace("OPTIONAL { ?item wdt:P21 ?gender }",
             "OPTIONAL { ?item wdt:P21 ?gender }\n  OPTIONAL { ?item wdt:P19/wdt:P17 ?birthCountry }\n"
             "  OPTIONAL { ?item wdt:P27 ?citizen }")

# Lettere e nessi che l'italiano non usa: il TTS rischia di sbagliarli.
STRANO = re.compile(r"[kwyjxäöüßñçãõåøæœłśźżčšžřőűáíóúâêîôûëïÿ]|lr|nr|tl|sch|sh|th|ch(?![ei])|ck|ph|tz|cz|sz|aa|ee|oo|uu|ij", re.I)

people = {}
for row in gs.fetch():
    q = row["item"]["value"].rsplit("/", 1)[1]
    p = people.setdefault(q, {"label": row["label"]["value"], "saint": False, "female": False,
                              "birth": set(), "cit": set()})
    st = row["status"]["value"].rsplit("/", 1)[1]
    p["saint"] |= st in gs.SAINT
    if "gender" in row and row["gender"]["value"].rsplit("/", 1)[1] in gs.FEMALE: p["female"] = True
    if "birthCountry" in row: p["birth"].add(row["birthCountry"]["value"].rsplit("/", 1)[1])
    if "citizen" in row: p["cit"].add(row["citizen"]["value"].rsplit("/", 1)[1])

res = {}
for q, p in people.items():
    name = gs.TITLE_RE.sub("", p["label"].strip()).replace("’", "'")
    name = name[:1].upper() + name[1:]
    title = gs.saint_title(name, p["female"]) if p["saint"] else ("Beata " if p["female"] else "Beato ")
    full = title + name
    if full not in santi_txt: continue
    paesi = p["birth"] or p["cit"]
    if not paesi: orig = "sconosciuta"
    elif paesi & ITALIA: orig = "italiana"
    else: orig = "straniera"
    # Old cittadinanze (Impero romano, Regno d'Italia...) non sono Q38: conta solo il luogo di nascita se c'e'.
    res[full] = (orig, bool(STRANO.search(name)), q)

c = collections.Counter((o, s) for o, s, _ in res.values())
tot = len(santi_txt)
print(f"santi.txt: {tot}, abbinati a Wikidata: {len(res)}")
for o in ("italiana", "straniera", "sconosciuta"):
    n = c[(o, True)] + c[(o, False)]
    print(f"  origine {o:11s}: {n:5d}  di cui con grafia non italiana: {c[(o, True)]}")
with open(sys.argv[3], "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["santo", "origine", "grafia_strana", "qid"])
    for k in sorted(res): w.writerow([k, res[k][0], int(res[k][1]), res[k][2]])
