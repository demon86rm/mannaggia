#!/usr/bin/env python3
"""Genera app/src/main/assets/santi.txt a partire da Wikidata (dati CC0).

Uso (dalla cartella mannaggia-android):
    python3 -I tools/genera_santi.py > app/src/main/assets/santi.txt

Interroga l'endpoint SPARQL di Wikidata per le persone con stato di
canonizzazione "santo" o "beato" che hanno un'etichetta in italiano,
esclude le figure di altre religioni, e
antepone il titolo corretto (San, Sant', Santo, Santa, Beato, Beata).
"""

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
QUERY = """
SELECT ?item ?label ?status ?gender WHERE {
  VALUES ?status { %s }
  VALUES ?kind { wd:Q5 wd:Q20643955 }
  ?item wdt:P411 ?status; wdt:P31 ?kind; rdfs:label ?label.
  FILTER(LANG(?label) = "it")
  FILTER NOT EXISTS { VALUES ?rel { %s } ?item wdt:P140 ?rel. }
  OPTIONAL { ?item wdt:P21 ?gender }
}
""" % (" ".join("wd:" + q for q in SAINT + BLESSED), " ".join("wd:" + q for q in NON_CHRISTIAN))

TITLE_RE = re.compile(r"^(?:(?:santa|santo|san|beata|beato|papa)\s+|sant['’]\s*)", re.IGNORECASE)
VALID_RE = re.compile(r"^[A-ZÀ-Ý][\w'’\-. àèéìòùÀÈÉÌÒÙçÇ]+$")


def fetch():
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": QUERY})
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


def main():
    people = {}
    for row in fetch():
        qid = row["item"]["value"].rsplit("/", 1)[1]
        if qid in EXCLUDE:
            continue
        p = people.setdefault(qid, {"label": row["label"]["value"], "saint": False,
                                    "blessed": False, "female": False})
        status = row["status"]["value"].rsplit("/", 1)[1]
        if status in SAINT:
            p["saint"] = True
        elif status in BLESSED:
            p["blessed"] = True
        if "gender" in row and row["gender"]["value"].rsplit("/", 1)[1] in FEMALE:
            p["female"] = True

    names = set()
    for p in people.values():
        name = TITLE_RE.sub("", p["label"].strip()).replace("’", "'")
        name = name[:1].upper() + name[1:]
        # Scarta etichette non tradotte (Q-id), con parentesi, cifre o alfabeti non latini.
        if len(name) < 3 or not VALID_RE.match(name) or re.search(r"\d", name):
            continue
        if p["saint"]:
            title = saint_title(name, p["female"])
        else:
            title = "Beata " if p["female"] else "Beato "
        names.add(title + name)

    print("# Santi e beati da Wikidata (https://www.wikidata.org), dati CC0.")
    print("# Generato con tools/genera_santi.py, non modificare a mano.")
    for n in sorted(names):
        print(n)
    print(f"{len(names)} nomi", file=sys.stderr)


if __name__ == "__main__":
    main()
