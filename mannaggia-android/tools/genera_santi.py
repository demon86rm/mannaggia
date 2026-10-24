#!/usr/bin/env python3
"""Genera app/src/main/assets/santi.txt a partire da Wikidata (dati CC0).

Uso (dalla cartella mannaggia-android):
    python3 -I tools/genera_santi.py > app/src/main/assets/santi.txt
    python3 -I tools/genera_santi.py --feste app/src/main/assets/feste.tsv \\
        --solo app/src/main/assets/santi.txt

Interroga l'endpoint SPARQL di Wikidata per le persone con stato di
canonizzazione "santo" o "beato" che hanno un'etichetta in italiano,
esclude le figure di altre religioni, e
antepone il titolo corretto (San, Sant', Santo, Santa, Beato, Beata).

Con --feste scrive invece le feste (P841) in formato MM-DD<TAB>santo, solo per
i santi gia' presenti in --solo: cosi' santi.txt non cambia. In ogni giorno i
santi sono ordinati dal piu' famoso (piu' voci Wikipedia) al meno noto, e il
primo e' il "santo del giorno" mostrato dall'app.
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "mannaggia-saint-list/1.0 (https://github.com/demon86rm/mannaggia)"

# Stati di santita' (P411): santo, santo cattolico, santo canonizzato, santo martire,
# santo pre-congregazione, ieromartire, megalomartire, taumaturgo, confessore,
# stilita, isapostolo, apostolo.
SAINT = ["Q43115", "Q3464126", "Q123110154", "Q4377390", "Q18344276", "Q2993173",
         "Q3332786", "Q1349880", "Q2354129", "Q401642", "Q619869", "Q43412"]
BLESSED = ["Q2369287"]
FEMALE = {"Q6581072", "Q1052281"}  # femmina, donna transgender

# Religioni non cristiane da escludere (induismo, islam, sufismo, buddismo, sikhismo).
# L'ebraismo resta: figure bibliche come San Giuseppe sono marcate cosi'.
NON_CHRISTIAN = ["Q9089", "Q432", "Q9603", "Q748", "Q9316"]

# Voci escluse a mano: Shu'ayb (profeta islamico/druso marcato come santo).
EXCLUDE = {"Q982867"}

# Esseri umani (Q5) o figure bibliche (Q20643955, es. San Giuseppe).
QUERY_TEMPLATE = """
SELECT ?item ?label ?status ?gender WHERE {
  VALUES ?status { %s }
  VALUES ?kind { wd:Q5 wd:Q20643955 }
  ?item wdt:P411 ?status; wdt:P31 ?kind; rdfs:label ?label.
  FILTER(LANG(?label) = "it")
  FILTER NOT EXISTS { VALUES ?rel { %s } ?item wdt:P140 ?rel. }
  OPTIONAL { ?item wdt:P21 ?gender }
}
"""
STATUSES = " ".join("wd:" + q for q in SAINT + BLESSED)
QUERY = QUERY_TEMPLATE % (STATUSES, " ".join("wd:" + q for q in NON_CHRISTIAN))
# Festa (P841, il valore e' un giorno come "October 18") e numero di voci Wikipedia.
# Query separata: unita a QUERY moltiplica le righe e Wikidata va in timeout.
FEAST_QUERY = """
SELECT ?item ?feastLabel ?sitelinks WHERE {
  VALUES ?status { %s }
  ?item wdt:P411 ?status; wdt:P841 ?feast; wikibase:sitelinks ?sitelinks.
  ?feast rdfs:label ?feastLabel. FILTER(LANG(?feastLabel) = "en")
}
""" % STATUSES

# Correzioni a mano per --feste. Le voci Wikipedia misurano la fama nel mondo, non nel
# calendario italiano, e Wikidata non ha alcune feste principali.
# Feste mancanti su Wikidata (santo -> giorni da aggiungere).
EXTRA_FEASTS = {
    "San Giuseppe": ["03-19"],
    "San Paolo di Tarso": ["06-29"],
}
# Santo del giorno imposto (giorno -> santo): finisce in cima a quel giorno.
SAINT_OF_DAY = {
    "01-17": "Sant'Antonio abate",
    "01-20": "San Sebastiano",
    "03-19": "San Giuseppe",
    "05-22": "Santa Rita da Cascia",
    "05-26": "San Filippo Neri",
    "06-29": "San Pietro",
    "08-11": "Santa Chiara d'Assisi",
    "08-16": "San Rocco",
    "09-23": "San Pio da Pietrelcina",
    "12-26": "Santo Stefano",
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
DATE_RE = re.compile(r"^(%s) (\d{1,2})$" % "|".join(MONTHS))

# Italian titles, plus the English/French ones some Italian labels copy ("Saint Amun", "Sainte Ode"):
# without them the app would say "San Saint Amun".
TITLE_RE = re.compile(r"^(?:(?:santa|santo|san|beata|beato|papa|saint|sainte|st\.)\s+|sant['’]\s*)", re.IGNORECASE)
VALID_RE = re.compile(r"^[A-ZÀ-Ý][\w'’\-. àèéìòùÀÈÉÌÒÙçÇ]+$")


def fetch(query=QUERY):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={
        "Accept": "application/sparql-results+json",
        "User-Agent": USER_AGENT,
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)["results"]["bindings"]


def saint_title(name, female):
    if female:
        return "Sant'" if name[0] in "AEIOUÀÈÉÌÒÙ" else "Santa "
    if name[0] in "AEIOUÀÈÉÌÒÙ":
        return "Sant'"
    if re.match(r"^(S[^aeiouàèéìòù]|Z|Gn|Ps|X)", name):
        return "Santo "
    return "San "


def collect(rows):
    """Group SPARQL rows by item: label, saint/blessed and gender."""
    people = {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[1]
        if qid in EXCLUDE:
            continue
        p = people.setdefault(qid, {"label": row["label"]["value"], "saint": False,
                                    "blessed": False, "female": False,
                                    "feasts": set(), "sitelinks": 0})
        status = row["status"]["value"].rsplit("/", 1)[1]
        if status in SAINT:
            p["saint"] = True
        elif status in BLESSED:
            p["blessed"] = True
        if "gender" in row and row["gender"]["value"].rsplit("/", 1)[1] in FEMALE:
            p["female"] = True
    return people


def add_feasts(people, rows):
    """Merge FEAST_QUERY rows (feast days as MM-DD, sitelinks) into [people]."""
    for row in rows:
        p = people.get(row["item"]["value"].rsplit("/", 1)[1])
        if p is None:
            continue
        # Feast values that are not days ("Eastern Orthodoxy", ...) are skipped.
        if m := DATE_RE.match(row["feastLabel"]["value"]):
            p["feasts"].add(f"{MONTHS.index(m.group(1)) + 1:02d}-{int(m.group(2)):02d}")
        p["sitelinks"] = int(row["sitelinks"]["value"])


def display_name(p):
    """Name as shown in the app ("San Pietro"), or None if the label is unusable."""
    name = TITLE_RE.sub("", p["label"].strip()).replace("’", "'")
    name = name[:1].upper() + name[1:]
    # Scarta etichette non tradotte (Q-id), con parentesi, cifre o alfabeti non latini.
    if len(name) < 3 or not VALID_RE.match(name) or re.search(r"\d", name):
        return None
    if p["saint"]:
        title = saint_title(name, p["female"])
    else:
        title = "Beata " if p["female"] else "Beato "
    return title + name


def write_feasts(path, only_path):
    known = {l.strip() for l in open(only_path, encoding="utf-8") if l.strip() and not l.startswith("#")}
    days = {}  # "MM-DD" -> {santo: sitelinks}
    people = collect(fetch())
    add_feasts(people, fetch(FEAST_QUERY))
    for p in people.values():
        name = display_name(p)
        if name not in known:
            continue
        for day in p["feasts"] | set(EXTRA_FEASTS.get(name, [])):
            saints = days.setdefault(day, {})
            saints[name] = max(saints.get(name, 0), p["sitelinks"])
    for day, name in SAINT_OF_DAY.items():
        if name not in known:
            sys.exit(f"SAINT_OF_DAY: {name!r} non e' in {only_path}")
        days.setdefault(day, {})[name] = float("inf")  # always first
    lines = 0
    with open(path, "w", encoding="utf-8") as out:
        out.write("# Feste dei santi (MM-DD<TAB>santo) da Wikidata (https://www.wikidata.org), dati CC0.\n")
        out.write("# Generato con tools/genera_santi.py --feste, non modificare a mano.\n")
        out.write("# In ogni giorno il primo e' il piu' famoso (piu' voci Wikipedia): il santo del giorno.\n")
        for day in sorted(days):
            for name, _ in sorted(days[day].items(), key=lambda kv: (-kv[1], kv[0])):
                out.write(f"{day}\t{name}\n")
                lines += 1
    print(f"{lines} feste, {len(days)} giorni", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feste", help="scrive le feste in questo file invece di stampare i santi")
    ap.add_argument("--solo", help="con --feste: tiene solo i santi di questo santi.txt")
    ap.add_argument("--correggi", help="rifà i titoli dei nomi di questo santi.txt, senza Wikidata "
                                       "(i santi restano gli stessi, cosi' l'album non cambia)")
    args = ap.parse_args()
    if args.correggi:
        print_names(retitle(args.correggi))
        return
    if args.feste:
        if not args.solo:
            ap.error("--feste richiede --solo")
        write_feasts(args.feste, args.solo)
        return

    print_names({n for p in collect(fetch()).values() if (n := display_name(p))})


def print_names(names):
    print("# Santi e beati da Wikidata (https://www.wikidata.org), dati CC0.")
    print("# Generato con tools/genera_santi.py, non modificare a mano.")
    for n in sorted(names):
        print(n)
    print(f"{len(names)} nomi", file=sys.stderr)


def retitle(path):
    """The names of an existing santi.txt, with their titles redone by display_name().

    Saint/blessed and gender come from the old title. Lets a fix to the titles (e.g.
    "San Saint Amun" -> "Sant'Amun") reach the app without regenerating from Wikidata,
    which changes over time. Renamed saints are listed on stderr: the app's album must
    migrate them (Album.RENAMED).
    """
    names = set()
    for line in open(path, encoding="utf-8"):
        old = line.strip()
        if not old or old.startswith("#"):
            continue
        m = re.match(r"^(Sant'|Santo|Santa|San|Beato|Beata) ?(.*)$", old)
        title, label = m.group(1), m.group(2)
        # "Sant'" hides the gender, but it only comes before a vowel, where the title is the same.
        female = title in ("Santa", "Beata")
        new = display_name({"label": label, "saint": not title.startswith("Beat"), "female": female})
        if new != old:
            print(f"  {old} -> {new}", file=sys.stderr)
        names.add(new)
    return names


if __name__ == "__main__":
    main()
