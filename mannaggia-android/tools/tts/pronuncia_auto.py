#!/usr/bin/env python3
"""Propone una grafia "all'italiana" per i santi dal nome straniero.

1. Filtro: trova le parole del nome che non seguono la grafia italiana.
2. Lingua: dal paese di nascita (o cittadinanza) su Wikidata; se manca, dalla grafia.
3. espeak-ng trascrive la parola in IPA in quella lingua.
4. Una tabella converte l'IPA in lettere che il TTS italiano legge correttamente.

Uso:
    python pronuncia_auto.py --santi santi.txt --conta                # solo il filtro
    python pronuncia_auto.py --santi santi.txt --nomi lista.txt       # proposte per questi santi
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request

# --- 1. Filtro -------------------------------------------------------------

TITOLI = re.compile(r"^(Sant'|Santo|Santa|San|Beato|Beata)\s*")
# Parole italiane brevi o titoli che finiscono in consonante e vanno lasciati stare.
OK = {"di", "da", "de", "del", "dal", "della", "dei", "degli", "delle", "e", "il", "la", "lo",
      "in", "con", "per", "san", "sant", "papa", "suor"}
ROMANO = re.compile(r"^[IVXLC]+$")
# Lettere e nessi che l'italiano non usa.
STRANO = re.compile(r"[kwyjxäöüßñçãõåøæœłśźżčšžřőűâêîôûëïÿāēīōūḷṇṭḍṣ]|lr|nr|tl|sch|sh|th|ck|ph|tz|cz|sz|"
                    r"aa|ee|oo|uu|ij|ch(?![ei])", re.I)
ACCENTO = re.compile(r"[àèéìíòóùú](?=\w)", re.I)  # in italiano l'accento scritto sta solo in fondo


def straniera(parola):
    p = parola.strip("'.-,").replace("'", "")
    if not p or p.lower() in OK or ROMANO.match(p) or len(p) == 1:
        return False
    if STRANO.search(p) or ACCENTO.search(p):
        return True
    return p[-1].lower() not in "aeiouàèéìòù"  # le parole italiane finiscono quasi sempre in vocale


def parole_straniere(santo):
    nome = TITOLI.sub("", santo)
    return [w for w in re.split(r"[\s\-]+", nome) if straniera(w)]


# --- 2. Lingua -------------------------------------------------------------

# Inglese britannico (vocali piu vicine all italiano), con la r rimessa in ipa().
# Spagnolo: es-419 (America Latina) legge la z come s.
PAESE_LINGUA = {
    "Q183": "de", "Q40": "de", "Q39": "de", "Q142": "fr", "Q31": "fr", "Q29": "es", "Q96": "es-419",
    "Q414": "es-419", "Q739": "es-419", "Q717": "es-419", "Q419": "es-419", "Q298": "es-419",
    "Q736": "es-419", "Q241": "es-419", "Q145": "en-gb", "Q21": "en-gb", "Q22": "en-gb", "Q25": "en-gb",
    "Q27": "en-gb", "Q30": "en-gb", "Q16": "en-gb", "Q408": "en-gb", "Q45": "pt", "Q155": "pt",
    "Q36": "pl", "Q55": "nl", "Q28": "hu",
    "Q213": "cs", "Q214": "sk", "Q224": "hr", "Q215": "sl", "Q34": "sv", "Q20": "nb", "Q35": "da",
    "Q33": "fi", "Q37": "lt", "Q212": "uk", "Q17": "ja", "Q881": "vi", "Q884": "ko",
}


def lingua_da_grafia(parole):
    t = " ".join(parole).lower()
    for pattern, lang in [(r"ñ|ll|rr|ez\b", "es"), (r"\bcs|cs\b|gy|ő|ű|á", "hu"),
                          (r"ß|sch|ä|ö|ü|tz|\bvom\b|\bvon\b|ss\b|see\b|ayr|ei|ind\b", "de"),
                          (r"ç|é|è|ê|eau|oux|ille|champ|agne\b|eux\b", "fr"),
                          (r"ł|ś|ź|ż|cz|sz", "pl"), (r"č|š|ž|ř", "cs"),
                          (r"ij|aa|oo", "nl"), (r"ã|õ|nh|lh", "pt"), (r"th|sh|w|y\b|ck", "en-gb")]:
        if re.search(pattern, t):
            return lang
    return "en-gb"


def paesi_wikidata(qids):
    values = " ".join("wd:" + q for q in qids)
    query = f"""SELECT ?item ?c WHERE {{ VALUES ?item {{ {values} }}
      {{ ?item wdt:P19/wdt:P17 ?c }} UNION {{ ?item wdt:P27 ?c }} }}"""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json",
                                               "User-Agent": "mannaggia-pronuncia/1.0"})
    out = {}
    with urllib.request.urlopen(req, timeout=120) as r:
        for row in json.load(r)["results"]["bindings"]:
            q = row["item"]["value"].rsplit("/", 1)[1]
            out.setdefault(q, []).append(row["c"]["value"].rsplit("/", 1)[1])
    return out


# --- 3-4. IPA -> grafia italiana --------------------------------------------

def ipa(parola, lang):
    r = subprocess.run(["espeak-ng", "-v", lang, "-q", "--ipa", parola], capture_output=True, text=True)
    s = r.stdout.strip()
    if lang == "en-gb":
        # L'inglese britannico non pronuncia la r dopo vocale, ma all'orecchio italiano serve:
        # per ogni r della grafia non seguita da vocale, la rimette dopo la prossima vocale lunga o schwa.
        mancanti = len(re.findall(r"r(?![aeiouy])", parola.lower()))
        pos = 0
        while mancanti and (m := re.compile(r"[ɔɑɜəɛɪʊ]ː?(?![ɹr])").search(s, pos)):
            if s[m.start():m.end()].endswith("ː") or m.group().startswith("ə") and m.end() == len(s) \
                    or m.group().startswith("ɜ"):
                s = s[:m.end()] + "ɹ" + s[m.end():]
                mancanti -= 1
            pos = m.end() + 1
    return s


VOCALI = {"a": "a", "ɑ": "a", "ɐ": "a", "æ": "e", "ʌ": "a", "ɒ": "o", "ɔ": "o", "o": "o", "e": "e",
          "ɛ": "e", "ə": "e", "ɜ": "e", "i": "i", "ɪ": "i", "u": "u", "ʊ": "u", "y": "iu", "ʏ": "iu",
          "ø": "e", "œ": "e", "ɯ": "u", "ɨ": "i"}
ACCENTATE = {"a": "à", "e": "è", "i": "ì", "o": "ò", "u": "ù"}
# Prima i dittonghi inglesi da rendere con una vocale sola, poi le consonanti.
# C/G/S = c, g, sc dolci; ʒ non esiste in italiano, la piu' vicina e' la g dolce.
CONSONANTI = [("əʊ", "o"), ("oʊ", "o"),
              ("tʃ", "C"), ("dʒ", "G"), ("ʃ", "S"), ("ts", "z"), ("dz", "z"), ("ʒ", "G"), ("θ", "t"),
              ("ð", "d"), ("ɲ", "gn"), ("ʎ", "gl"), ("ŋ", "ng"), ("x", "k"), ("ç", "sc"), ("χ", "k"),
              ("ʁ", "r"), ("ɹ", "r"), ("ɾ", "r"), ("ʀ", "r"), ("ɫ", "l"), ("w", "u"), ("j", "i"),
              ("h", ""), ("ʔ", ""), ("ɡ", "g"), ("β", "b"), ("ɣ", "g")]


def italiano(ipa_str):
    """Converte un'IPA di espeak in una grafia che il TTS italiano legge in modo simile."""
    s = re.sub(r"[ːˌ\-.]|̃", lambda m: "n" if m.group() == "̃" else "", ipa_str)
    for a, b in CONSONANTI:
        s = s.replace(a, b)
    out, accento = [], False
    for ch in s:
        if ch == "ˈ":
            accento = True
            continue
        if ch in VOCALI:
            v = VOCALI[ch]
            if accento and len(v) == 1:
                v, accento = ACCENTATE[v], False
            out.append(v)
        else:
            out.append(ch)
    s = "".join(out)
    # Suoni duri prima di quelli dolci, altrimenti la "gi" appena scritta diventerebbe "ghi".
    s = re.sub(r"k(?=[eièì])", "ch", s); s = re.sub(r"k", "c", s)   # c dura
    s = re.sub(r"g(?=[eièì])", "gh", s)                                # g dura
    # C/G/S = suoni dolci: davanti a e/i bastano c/g/sc, altrimenti serve la i.
    s = re.sub(r"C(?=[eièì])", "c", s); s = s.replace("C", "ci")
    s = re.sub(r"G(?=[eièì])", "g", s); s = s.replace("G", "gi")
    s = re.sub(r"S(?=[eièì])", "sc", s); s = s.replace("S", "sci")
    s = re.sub(r"(.)\1+", r"\1", s)                                    # niente doppie inventate
    return s[:1].upper() + s[1:] if s else s


def proposta(santo, lang):
    stranieri = set(parole_straniere(santo))
    pezzi = re.split(r"([\s\-]+)", santo)
    return "".join(italiano(ipa(p, lang)) if p in stranieri else p for p in pezzi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--santi", required=True)
    ap.add_argument("--conta", action="store_true", help="conta i nomi segnalati dal filtro ed esce")
    ap.add_argument("--nomi", help="file con i santi (uno per riga) per cui fare la proposta")
    ap.add_argument("--qid", help="TSV santo<TAB>...<TAB>qid (origine_santi.tsv) per la lingua")
    args = ap.parse_args()

    santi = [s.strip() for s in open(args.santi, encoding="utf-8") if s.strip() and not s.startswith("#")]
    if args.conta:
        segnalati = [s for s in santi if parole_straniere(s)]
        print(f"{len(segnalati)} santi su {len(santi)} con parole non italiane")
        for s in segnalati:
            print(s, "|", " ".join(parole_straniere(s)), file=sys.stderr)
        return

    nomi = [s.strip() for s in open(args.nomi, encoding="utf-8") if s.strip()]
    qid = {}
    if args.qid:
        for row in open(args.qid, encoding="utf-8"):
            f = row.rstrip("\n").split("\t")
            qid[f[0]] = f[-1]
    paesi = paesi_wikidata([qid[n] for n in nomi if n in qid]) if qid else {}
    for n in nomi:
        lang = next((PAESE_LINGUA[c] for c in paesi.get(qid.get(n), []) if c in PAESE_LINGUA), None)
        fonte = "wikidata" if lang else "grafia"
        lang = lang or lingua_da_grafia(parole_straniere(n))
        print(f"{n}\t{proposta(n, lang)}\t{lang} ({fonte})")


if __name__ == "__main__":
    main()
