#!/usr/bin/env python3
"""Avatar in pixel art dei santi (mezzo busto, 48x48), disegnati da zero.

Nessuna immagine esistente viene usata: ogni avatar e' composto da pezzi
disegnati qui (testa, capelli, barba, copricapo, abito, attributi, aureola),
scelti in base ai tratti del santo. I tratti vengono da una tabella fatta a
mano per i santi piu' famosi (FAMOSI) o, per gli altri, da regole sui dati
Wikidata (genere, cariche, ordine religioso, mestiere, martirio). Le piccole
variazioni (carnagione, colori, volto) sono deterministiche: dipendono dal nome.

I santi leggendari hanno in piu' una cornice d'oro (cornice()), disegnata come
livello separato cosi' l'app puo' applicarla sopra l'avatar. Alcuni hanno una cornice
tutta loro (CORNICI, es. le fiamme del rogo per Giovanna d'Arco). Con l'opzione
"Colorful" dell'app anche gli altri santi hanno una cornice animata (COLORATE: bronzo,
legno, arcobaleno, neon, vaporwave, ...; la palma ai martiri non leggendari), elencata in cornici_colorful.txt.

Uso (venv con pillow; dalla cartella android):
    python tools/ritratti/avatar.py --nomi lista.txt --out ~/mannaggia-avatar-prova
    python tools/ritratti/avatar.py --famosi --out ~/mannaggia-avatar-prova   # tutta la tabella
    python tools/ritratti/avatar.py --tutti --app app/src/main/assets/avatar \\
        --cache tools/ritratti/tratti_wikidata.json                         # asset dell'app
"""

import argparse
import colorsys
import hashlib
import importlib.util
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
S = 48  # lato dell'avatar

# --- Tavolozza ----------------------------------------------------------------

OUTLINE = (34, 24, 32)
SKINS = [(246, 208, 176), (234, 186, 146), (212, 156, 112), (172, 116, 78), (120, 80, 54), (90, 58, 40)]
HAIRS = {"nero": (40, 32, 30), "castano": (104, 66, 40), "biondo": (214, 172, 92),
         "rosso": (160, 72, 36), "grigio": (150, 146, 144), "bianco": (232, 228, 220)}
GOLD, GOLD_DARK, GOLD_LIGHT = (232, 184, 56), (176, 124, 28), (252, 228, 132)
HALO, HALO_RING = (252, 232, 150), (226, 182, 70)
HALO_BEATO, HALO_BEATO_RING = (236, 230, 200), (196, 184, 140)
WHITE, BLACK = (240, 238, 232), (36, 34, 40)
RED, DARK_RED = (178, 34, 44), (120, 20, 30)
STEEL, STEEL_DARK, STEEL_LIGHT = (156, 164, 176), (100, 106, 120), (210, 216, 226)
GREEN, DARK_GREEN = (70, 150, 70), (38, 96, 46)
WOOD, WOOD_DARK = (130, 88, 52), (92, 60, 36)
BROWN_HABIT, BLACK_HABIT, CARMEL = (122, 82, 50), (44, 40, 46), (110, 78, 52)
EYE = (40, 30, 34)
MOUTH = (168, 84, 80)
BACKGROUNDS = [(94, 120, 168), (120, 92, 150), (84, 140, 130), (170, 110, 90),
               (110, 130, 90), (150, 96, 112), (88, 108, 128), (160, 140, 96)]
# Sfondo per categoria: il colore dice subito "che tipo" di santo e'.
BG_CATEGORIA = {"papa": (178, 148, 74), "vescovo": (112, 82, 140), "martire": (150, 72, 72),
                "religioso": (104, 118, 84), "regale": (62, 82, 140), "guerriero": (92, 110, 132)}
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
                                 # | zucchetto_rosso | zucchetto_bianco | pellegrino | corona_rose | sari
    colore_velo: tuple | None = None
    abito: str = "tunica"        # tunica | apostolo | saio | benedettino | domenicano | cistercense
                                 # | vescovo | papa | cardinale | armatura | crociato | regale | nudo
                                 # | suora | dalmatica | pelliccia | talare | righe | camice | moderno
    colore_abito: tuple | None = None
    attributo: str = "nessuno"   # uno o piu', separati da "+": vedi ATTRIBUTI
    extra: list = field(default_factory=list)  # ferita_fronte, stigmate, occhiali, fiamma, stella, medaglione
    martire: bool = False


def T(**kw):
    return Tratti(**kw)


A = lambda **kw: T(abito="apostolo", **kw)  # noqa: E731


# Iconografia dei santi piu' noti, scritta a mano (nomi come in santi.txt).
FAMOSI = {
    # Apostoli ed evangelisti
    "San Pietro": A(eta="anziano", capelli="calvo", colore_capelli="bianco", barba="corta",
                    colore_abito=(60, 90, 170), attributo="chiavi"),
    "San Paolo di Tarso": A(capelli="calvo", colore_capelli="nero", barba="lunga",
                            colore_abito=(150, 50, 60), attributo="spada+libro"),
    "Sant'Andrea": A(eta="anziano", capelli="corti", colore_capelli="bianco", barba="lunga",
                     colore_abito=(60, 120, 90), attributo="croce_x"),
    "San Giacomo il Maggiore": A(capelli="lunghi", colore_capelli="castano", barba="corta",
                                 copricapo="pellegrino", colore_abito=(70, 96, 160),
                                 attributo="bordone+conchiglia"),
    "San Giovanni": A(eta="giovane", capelli="lunghi", colore_capelli="castano",
                      colore_abito=(150, 50, 60), attributo="aquila"),
    "San Matteo": A(capelli="corti", colore_capelli="nero", barba="corta",
                    colore_abito=(180, 130, 60), attributo="libro+penna"),
    "San Marco": A(capelli="ricci", colore_capelli="nero", barba="corta",
                   colore_abito=(130, 90, 150), attributo="leone"),
    "San Luca": A(capelli="corti", colore_capelli="castano", barba="corta",
                  colore_abito=(40, 110, 140), attributo="bue"),
    "San Tommaso": A(capelli="corti", colore_capelli="castano", barba="corta",
                     colore_abito=(60, 120, 90), attributo="lancia"),
    "San Bartolomeo": A(capelli="ricci", colore_capelli="nero", barba="lunga",
                        colore_abito=(160, 80, 40), attributo="coltello"),
    "San Filippo": A(capelli="corti", colore_capelli="grigio", barba="corta",
                     colore_abito=(90, 90, 110), attributo="croce"),
    "San Giacomo il Minore": A(capelli="lunghi", colore_capelli="castano", barba="corta",
                               colore_abito=(70, 96, 160), attributo="bastone"),
    "San Simone il Cananeo": A(eta="anziano", capelli="calvo", colore_capelli="grigio",
                               barba="lunga", colore_abito=(130, 90, 150), attributo="sega"),
    "San Giuda Taddeo": A(capelli="corti", colore_capelli="castano", barba="corta",
                          colore_abito=(60, 120, 90), attributo="bastone", extra=["medaglione", "fiamma"]),
    "San Mattia": A(capelli="corti", colore_capelli="nero", barba="corta",
                    colore_abito=(150, 50, 60), attributo="ascia"),
    # Famiglia di Gesu' e figure bibliche
    "Santa Maria": T(donna=True, eta="giovane", copricapo="velo", colore_velo=(56, 96, 176),
                     abito="tunica", colore_abito=(170, 40, 50), attributo="giglio",
                     extra=["stelle", "manto_azzurro"]),
    "San Davide": T(eta="adulto", capelli="ricci", colore_capelli="rosso", barba="corta",
                    copricapo="corona", abito="regale", colore_abito=(120, 40, 120), attributo="arpa"),
    "San Giuseppe": A(eta="anziano", capelli="corti", colore_capelli="grigio", barba="corta",
                      colore_abito=(150, 110, 60), attributo="giglio"),
    "San Giovanni Battista": T(capelli="lunghi", colore_capelli="castano", barba="lunga",
                               abito="pelliccia", attributo="agnello+croce", martire=True),
    "Santa Maria Maddalena": T(donna=True, capelli="lunghi", colore_capelli="rosso", abito="tunica",
                               colore_abito=(150, 50, 60), attributo="vaso"),
    "Sant'Anna": T(donna=True, eta="anziano", copricapo="velo", colore_velo=(80, 120, 80),
                   abito="tunica", colore_abito=(150, 50, 60), attributo="libro"),
    "San Gioacchino": A(eta="anziano", capelli="corti", colore_capelli="bianco", barba="lunga",
                        colore_abito=(150, 50, 60), attributo="bastone"),
    # Martiri dei primi secoli
    "Santo Stefano": T(eta="giovane", capelli="tonsura", colore_capelli="castano",
                       abito="dalmatica", attributo="pietre+palma", martire=True),
    "San Lorenzo": T(eta="giovane", capelli="tonsura", colore_capelli="nero",
                     abito="dalmatica", attributo="graticola", martire=True),
    "San Sebastiano": T(eta="giovane", capelli="ricci", colore_capelli="castano",
                        abito="nudo", attributo="frecce", martire=True),
    "San Giorgio": T(eta="giovane", capelli="ricci", colore_capelli="biondo",
                     abito="crociato", attributo="lancia+drago", martire=True),
    "Santa Caterina d'Alessandria": T(donna=True, eta="giovane", capelli="lunghi",
                                      colore_capelli="biondo", copricapo="corona",
                                      abito="regale", colore_abito=(150, 40, 60),
                                      attributo="ruota", martire=True),
    "Sant'Agnese": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="biondo",
                     abito="tunica", colore_abito=WHITE, attributo="agnello", martire=True),
    "Santa Cecilia": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="castano",
                       copricapo="corona_rose", abito="tunica", colore_abito=(60, 120, 90),
                       attributo="organo", martire=True),
    "Sant'Agata": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="nero",
                    copricapo="velo", colore_velo=(150, 50, 60), abito="tunica",
                    colore_abito=(150, 50, 60), attributo="palma+tenaglia", martire=True),
    "Santa Lucia": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="castano",
                     abito="tunica", colore_abito=(60, 120, 80), attributo="occhi", martire=True),
    "Santa Barbara": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="biondo",
                       copricapo="corona", abito="regale", colore_abito=(70, 96, 160),
                       attributo="torre", martire=True),
    "Sant'Apollonia di Alessandria": T(donna=True, eta="anziano", copricapo="velo",
                                       colore_velo=(130, 90, 150), abito="tunica",
                                       colore_abito=(130, 90, 150), attributo="tenaglia", martire=True),
    "Santa Margherita di Antiochia": T(donna=True, eta="giovane", capelli="lunghi",
                                       colore_capelli="biondo", abito="tunica",
                                       colore_abito=(150, 50, 60), attributo="croce+drago", martire=True),
    "San Cristoforo": T(capelli="ricci", colore_capelli="castano", barba="lunga", abito="tunica",
                        colore_abito=(160, 80, 40), attributo="bastone+bambino", martire=True),
    "San Vito": T(eta="giovane", capelli="ricci", colore_capelli="castano", abito="tunica",
                  colore_abito=(70, 96, 160), attributo="palma+cane", martire=True),
    "San Valentino": T(eta="anziano", capelli="corti", colore_capelli="bianco", barba="corta",
                       copricapo="mitra", abito="vescovo", colore_abito=RED,
                       attributo="cuore", martire=True),
    "San Gennaro": T(capelli="corti", colore_capelli="nero", copricapo="mitra",
                     abito="vescovo", colore_abito=RED, attributo="pastorale", martire=True),
    "Sant'Efisio": T(eta="giovane", capelli="ricci", colore_capelli="nero", copricapo="elmo",
                     abito="armatura", attributo="spada", martire=True),
    "San Giusto di Trieste": T(eta="giovane", capelli="corti", colore_capelli="biondo",
                               abito="tunica", colore_abito=(70, 96, 160), attributo="palma", martire=True),
    "San Biagio di Sebaste": T(eta="anziano", capelli="corti", colore_capelli="bianco", barba="lunga",
                               copricapo="mitra", abito="vescovo", colore_abito=(150, 50, 60),
                               attributo="candele", martire=True),
    "San Damiano": T(capelli="corti", colore_capelli="castano", barba="corta", abito="tunica",
                     colore_abito=(150, 50, 60), attributo="vaso", martire=True),
    # Vescovi e dottori della Chiesa
    "San Nicola di Bari": T(eta="anziano", capelli="calvo", colore_capelli="bianco", barba="lunga",
                            copricapo="mitra", abito="vescovo", colore_abito=(150, 50, 60),
                            attributo="libro+palle"),
    "San Martino di Tours": T(capelli="corti", colore_capelli="castano", abito="armatura",
                              attributo="spada", extra=["mantello"]),
    "Sant'Ambrogio": T(capelli="corti", colore_capelli="castano", barba="corta", copricapo="mitra",
                       abito="vescovo", colore_abito=(240, 236, 228), attributo="frusta"),
    "Sant'Agostino d'Ippona": T(eta="anziano", capelli="calvo", colore_capelli="grigio",
                                barba="lunga", copricapo="mitra", abito="vescovo",
                                colore_abito=(40, 70, 150), attributo="libro+cuore"),
    "San Patrizio": T(eta="anziano", capelli="corti", colore_capelli="bianco", barba="lunga",
                      copricapo="mitra", abito="vescovo", colore_abito=(50, 130, 70),
                      attributo="pastorale+trifoglio"),
    "San Petronio": T(eta="anziano", capelli="corti", colore_capelli="bianco", barba="corta",
                      copricapo="mitra", abito="vescovo", colore_abito=(150, 50, 60), attributo="citta"),
    "Santo Zeno di Verona": T(pelle=4, capelli="corti", colore_capelli="nero", barba="corta",
                              copricapo="mitra", abito="vescovo", colore_abito=(150, 50, 60),
                              attributo="pastorale+pesce"),
    "San Cataldo": T(eta="anziano", capelli="corti", colore_capelli="bianco", barba="lunga",
                     copricapo="mitra", abito="vescovo", colore_abito=(70, 96, 160), attributo="pastorale"),
    "Sant'Oronzo di Lecce": T(capelli="corti", colore_capelli="nero", barba="corta", copricapo="mitra",
                              abito="vescovo", colore_abito=(150, 50, 60), attributo="pastorale", martire=True),
    "Sant'Ubaldo Baldassini": T(eta="anziano", capelli="corti", colore_capelli="bianco",
                                copricapo="mitra", abito="vescovo", colore_abito=(70, 96, 160),
                                attributo="pastorale"),
    "Sant'Emidio d'Ascoli": T(capelli="corti", colore_capelli="nero", barba="corta", copricapo="mitra",
                              abito="vescovo", colore_abito=(150, 50, 60), attributo="pastorale+citta", martire=True),
    "San Girolamo": T(eta="anziano", capelli="calvo", colore_capelli="bianco", barba="lunga",
                      abito="cardinale", attributo="leone", extra=[]),
    "San Tommaso d'Aquino": T(capelli="tonsura", colore_capelli="castano", abito="domenicano",
                              attributo="libro", extra=["sole_petto"]),
    "San Bonaventura da Bagnoregio": T(eta="anziano", capelli="tonsura", colore_capelli="grigio",
                                       copricapo="zucchetto_rosso", abito="cardinale", attributo="libro"),
    "Sant'Alfonso Maria de' Liguori": T(eta="anziano", capelli="corti", colore_capelli="bianco",
                                        copricapo="mitra", abito="vescovo", colore_abito=BLACK_HABIT,
                                        attributo="libro"),
    "Sant'Ilario di Poitiers": T(eta="anziano", capelli="calvo", colore_capelli="bianco", barba="lunga",
                                 copricapo="mitra", abito="vescovo", colore_abito=(130, 90, 150),
                                 attributo="libro"),
    # Papi
    "San Silvestro I": T(eta="anziano", capelli="corti", colore_capelli="bianco", barba="lunga",
                         copricapo="tiara", abito="papa", attributo="croce"),
    "San Leone I": T(eta="anziano", capelli="corti", colore_capelli="bianco", barba="corta",
                     copricapo="tiara", abito="papa", attributo="libro"),
    "San Gregorio I": T(eta="anziano", capelli="tonsura", colore_capelli="grigio",
                        copricapo="tiara", abito="papa", attributo="libro+colomba"),
    "San Giovanni XXIII": T(eta="anziano", capelli="corti", colore_capelli="grigio",
                            copricapo="zucchetto_bianco", abito="papa", attributo="nessuno",
                            pelle=0),
    "San Paolo VI": T(eta="anziano", capelli="corti", colore_capelli="grigio",
                      copricapo="zucchetto_bianco", abito="papa", attributo="croce"),
    "San Giovanni Paolo II": T(eta="anziano", capelli="corti", colore_capelli="bianco",
                               copricapo="zucchetto_bianco", abito="papa", attributo="croce"),
    # Monaci, frati, fondatori
    "San Benedetto da Norcia": T(eta="anziano", capelli="tonsura", colore_capelli="bianco",
                                 barba="lunga", abito="benedettino", attributo="libro+pastorale"),
    "Santa Scolastica da Norcia": T(donna=True, copricapo="velo", abito="suora",
                                    colore_abito=BLACK_HABIT, attributo="colomba"),
    "San Bernardo di Chiaravalle": T(capelli="tonsura", colore_capelli="castano",
                                     abito="cistercense", attributo="libro+pastorale"),
    "Sant'Antonio abate": T(eta="anziano", capelli="calvo", colore_capelli="bianco", barba="lunga",
                            copricapo="cappuccio", abito="saio", colore_abito=(80, 74, 70),
                            attributo="tau+maialino"),
    "San Francesco d'Assisi": T(capelli="tonsura", colore_capelli="castano", barba="corta",
                                abito="saio", attributo="croce", extra=["stigmate"]),
    "Santa Chiara d'Assisi": T(donna=True, copricapo="velo", abito="suora",
                               colore_abito=BROWN_HABIT, attributo="ostensorio"),
    "Sant'Antonio di Padova": T(eta="giovane", capelli="tonsura", colore_capelli="castano",
                                abito="saio", attributo="giglio+bambino"),
    "San Bernardino da Siena": T(eta="anziano", capelli="tonsura", colore_capelli="grigio",
                                 abito="saio", attributo="ihs"),
    "San Francesco da Paola": T(eta="anziano", capelli="nessuno", colore_capelli="bianco",
                                barba="lunga", copricapo="cappuccio", abito="saio",
                                colore_abito=(96, 70, 52), attributo="bastone+caritas"),
    "San Pio da Pietrelcina": T(eta="anziano", capelli="calvo", colore_capelli="bianco",
                                barba="lunga", abito="saio", attributo="rosario"),
    "San Giuseppe da Copertino": T(capelli="tonsura", colore_capelli="castano", abito="saio",
                                   colore_abito=(70, 66, 64), attributo="croce"),
    "San Domenico di Guzmán": T(capelli="tonsura", colore_capelli="castano", abito="domenicano",
                                attributo="giglio+cane", extra=["stella"]),
    "Santa Caterina da Siena": T(donna=True, copricapo="velo", colore_velo=BLACK, abito="suora",
                                 colore_abito=WHITE, attributo="giglio", extra=["spine"]),
    "Sant'Ignazio di Loyola": T(capelli="calvo", colore_capelli="nero", barba="corta",
                                abito="talare", attributo="ihs"),
    "San Francesco Saverio": T(capelli="corti", colore_capelli="nero", barba="corta",
                               abito="talare", attributo="crocifisso"),
    "San Luigi Gonzaga": T(eta="giovane", capelli="corti", colore_capelli="castano",
                           abito="talare", attributo="giglio+teschio"),
    "San Carlo Borromeo": T(capelli="corti", colore_capelli="castano", copricapo="zucchetto_rosso",
                            abito="cardinale", attributo="crocifisso"),
    "San Filippo Neri": T(eta="anziano", capelli="calvo", colore_capelli="bianco", barba="corta",
                          abito="talare", attributo="giglio"),
    "San Camillo de Lellis": T(capelli="corti", colore_capelli="nero", barba="corta",
                               abito="talare", attributo="crocifisso", extra=["croce_rossa"]),
    "San Vincenzo de' Paoli": T(eta="anziano", capelli="calvo", colore_capelli="bianco",
                                barba="corta", abito="talare", attributo="bambino"),
    "San Giovanni Bosco": T(capelli="ricci", colore_capelli="nero", abito="talare", attributo="nessuno"),
    "San Giovanni Maria Vianney": T(eta="anziano", capelli="lunghi", colore_capelli="bianco",
                                    abito="talare", attributo="rosario"),
    "San Giovanni della Croce": T(capelli="tonsura", colore_capelli="nero", copricapo="cappuccio",
                                  abito="saio", colore_abito=CARMEL, attributo="croce"),
    "San Gerardo Maiella": T(eta="giovane", capelli="corti", colore_capelli="nero",
                             abito="talare", attributo="giglio+teschio"),
    "San Rocco": T(capelli="corti", colore_capelli="castano", barba="corta", copricapo="pellegrino",
                   abito="tunica", colore_abito=(110, 80, 56), attributo="bordone_provola+cane"),
    "San Ranieri Scacceri": T(capelli="lunghi", colore_capelli="castano", barba="lunga",
                              abito="tunica", colore_abito=(110, 80, 56), attributo="bordone"),
    "San Bruno di Colonia": T(capelli="tonsura", colore_capelli="castano", copricapo="cappuccio",
                              abito="cistercense", attributo="teschio+croce"),
    # Sante e mistiche
    "Santa Rita da Cascia": T(donna=True, copricapo="velo", abito="suora",
                              colore_abito=BLACK_HABIT, attributo="rosa", extra=["ferita_fronte"]),
    "Santa Teresa d'Ávila": T(donna=True, eta="anziano", copricapo="velo", colore_velo=BLACK,
                              abito="suora", colore_abito=CARMEL, attributo="libro+penna"),
    "Santa Teresa di Lisieux": T(donna=True, eta="giovane", copricapo="velo", colore_velo=BLACK,
                                 abito="suora", colore_abito=CARMEL, attributo="crocifisso+rosa"),
    "Santa Bernadette Soubirous": T(donna=True, eta="giovane", copricapo="velo",
                                    colore_velo=WHITE, abito="tunica", colore_abito=(90, 80, 90),
                                    attributo="rosario"),
    "Santa Maria Goretti": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="castano",
                             abito="tunica", colore_abito=(220, 210, 190), attributo="giglio", martire=True),
    "Santa Monica": T(donna=True, eta="anziano", copricapo="velo", colore_velo=BLACK,
                      abito="tunica", colore_abito=(80, 76, 84), attributo="libro"),
    "Santa Brigida di Svezia": T(donna=True, eta="anziano", copricapo="velo", colore_velo=BLACK,
                                 abito="suora", colore_abito=(90, 86, 96), attributo="libro+penna"),
    "Santa Francesca Saverio Cabrini": T(donna=True, copricapo="velo", colore_velo=BLACK, abito="suora",
                                         colore_abito=BLACK_HABIT, attributo="crocifisso"),
    "Santa Faustina Kowalska": T(donna=True, eta="giovane", copricapo="velo", colore_velo=BLACK,
                                 abito="suora", colore_abito=BLACK_HABIT, attributo="rosario"),
    "Santa Rosalia": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="biondo",
                       copricapo="corona_rose", abito="saio", attributo="teschio+croce"),
    "Santa Madre Teresa di Calcutta": T(donna=True, eta="anziano", pelle=2, copricapo="sari",
                                        abito="sari", attributo="rosario"),
    "Sant'Elisabetta d'Ungheria": T(donna=True, copricapo="corona", capelli="lunghi",
                                    colore_capelli="biondo", abito="regale",
                                    colore_abito=(130, 90, 150), attributo="rosa"),
    "Santa Giovanna d'Arco": T(donna=True, eta="giovane", capelli="corti", colore_capelli="castano",
                               abito="armatura", attributo="spada", martire=True),
    # Re, imperatori
    # the margrave of Baden (1428-1458, died young) as his statue in the Stiftskirche of Baden-Baden (the
    # user, 2026-11-18): in armour, bareheaded, long hair, a staff with a cross on top
    "Beato Bernardo II di Baden": T(beato=True, eta="giovane", capelli="lunghi", colore_capelli="castano",
                                    abito="armatura", attributo="croce"),
    "San Costantino I": T(capelli="corti", colore_capelli="castano", copricapo="corona",
                          abito="regale", colore_abito=(130, 40, 120), attributo="croce"),
    # Santi del Novecento
    "San Massimiliano Maria Kolbe": T(capelli="corti", colore_capelli="castano", abito="righe",
                                      attributo="palma", extra=["occhiali"], martire=True),
    "San Josemaría Escrivá de Balaguer": T(capelli="corti", colore_capelli="nero", abito="talare",
                                           attributo="nessuno", extra=["occhiali"]),
    "Santa Gianna Beretta Molla": T(donna=True, capelli="corti", colore_capelli="castano",
                                    abito="camice", attributo="nessuno"),
    "San Pier Giorgio Frassati": T(eta="giovane", capelli="corti", colore_capelli="nero",
                                   abito="moderno", colore_abito=(90, 90, 110), attributo="bastone"),
    "San Carlo Acutis": T(eta="giovane", capelli="ricci", colore_capelli="castano",
                          abito="moderno", colore_abito=(170, 40, 50), attributo="nessuno"),
    # Saints of other peoples (skin in PELLE): traits from their best-known images, 2026-11-12.
    "Santa Giuseppina Bakhita": T(donna=True, copricapo="velo", colore_velo=BLACK, abito="suora", attributo="nessuno"),
    "San Mosè l'Etiope": T(eta="anziano", capelli="ricci", colore_capelli="bianco", barba="lunga", abito="saio",
                           colore_abito=(96, 78, 62), attributo="bastone", martire=True),
    "Beata Maria Clementina Anuarite Nengapeta": T(donna=True, eta="giovane", copricapo="velo", colore_velo=WHITE,
                                                   abito="suora", attributo="palma", martire=True),
    "Beato Isidore Bakanja": T(eta="giovane", capelli="ricci", colore_capelli="nero", abito="tunica",
                               colore_abito=WHITE, attributo="palma", martire=True),
    "Santa Sara la Nera": T(donna=True, copricapo="velo", colore_velo=(56, 96, 176), abito="tunica",
                            colore_abito=(178, 140, 60), attributo="nessuno"),
    "San Martino de Porres": T(capelli="ricci", colore_capelli="nero", abito="domenicano", attributo="scopa"),
    **{n: T(eta=e, capelli="ricci", colore_capelli="nero", abito="tunica", colore_abito=WHITE,
            attributo="palma", martire=True)
       for n, e in (("San Carlo Lwanga", "giovane"), ("San Kizito", "giovane"), ("San Joseph Mukasa", "adulto"),
                    ("San Gyaviira Mayanja Musoke", "giovane"), ("Sant'Achilleo Kiwanuka", "giovane"),
                    ("Sant'Ambrogio Kibuuka", "giovane"), ("Sant'Andrea Kaggwa", "adulto"),
                    ("Beato Davide Okelo", "giovane"), ("Beato Gildo Irwa", "giovane"))},
    "Sant'Andrea Kim Taegon": T(eta="giovane", capelli="corti", colore_capelli="nero", abito="tunica",
                                colore_abito=(212, 224, 236), attributo="palma", martire=True),
    "San Paolo Miki": T(capelli="corti", colore_capelli="nero", abito="talare", attributo="croce", martire=True),
    "Sant'Agostino Zhao Rong": T(capelli="corti", colore_capelli="nero", abito="talare", attributo="palma", martire=True),
    "San Lorenzo Ruiz": T(capelli="corti", colore_capelli="nero", abito="tunica", colore_abito=WHITE,
                          attributo="palma", martire=True),
    "Santa Kateri Tekakwitha": T(donna=True, eta="giovane", capelli="lunghi", colore_capelli="nero", abito="tunica",
                                 colore_abito=(138, 90, 58), attributo="giglio"),
    "San Juan Diego Cuauhtlatoatzin": T(capelli="lunghi", colore_capelli="nero", abito="tunica",
                                        colore_abito=(200, 168, 120), attributo="rosa"),
    "San Charbel Makhluf": T(eta="anziano", capelli="nessuno", colore_capelli="bianco", barba="lunga",
                             copricapo="cappuccio", abito="benedettino", attributo="nessuno"),
    "San Kuriakose Elias Chavara": T(capelli="corti", colore_capelli="nero", barba="corta", abito="talare",
                                     colore_abito=WHITE, attributo="libro"),
    # The jazz saxophonist, canonized by the African Orthodox Church (Wikidata marks him as a saint).
    "San John Coltrane": T(pelle=4, capelli="corti", colore_capelli="nero",
                           abito="moderno", colore_abito=(52, 54, 66), attributo="sassofono"),
}

# Figurine speciali fuori catalogo (S1..S7), sbloccabili solo con i trofei.
# L'ordine e' il numero: S1 = la prima. I nomi sono anche la chiave del file (sha1).
SPECIALI = {
    "Santo Subito": T(eta="anziano", capelli="corti", colore_capelli="bianco",
                      copricapo="zucchetto_bianco", abito="papa", attributo="striscione"),
    "San Culo": T(eta="giovane", capelli="ricci", colore_capelli="biondo", abito="tunica",
                  colore_abito=(60, 90, 170), attributo="ferro_cavallo+quadrifoglio"),
    "San Calendario": T(capelli="corti", colore_capelli="castano", barba="corta", abito="tunica",
                        colore_abito=(150, 50, 60), attributo="calendario_mano"),
    "San Deploy": T(capelli="corti", colore_capelli="castano", barba="corta", abito="moderno",
                    colore_abito=(50, 60, 80), attributo="server_fuoco", extra=["cuffie", "occhiali"]),
    "San Sudo": T(eta="giovane", capelli="corti", colore_capelli="castano", copricapo="cappuccio",
                  abito="moderno", colore_abito=(70, 74, 84), attributo="terminale"),
    "Santa Pazienza": T(donna=True, eta="anziano", copricapo="velo", colore_velo=(110, 120, 160),
                        abito="tunica", colore_abito=(110, 120, 160), attributo="clessidra"),
    # mannaggia.sh: "...ti strafulmini santa cunegonda bipalluta protrettice dei VUA".
    "Santa Cunegonda Bipalluta": T(donna=True, copricapo="velo", colore_velo=(60, 60, 70),
                                   abito="tunica", colore_abito=(60, 60, 70), attributo="fulmine+sfere"),
}

# Leggendari per il provino (nell'app si calcoleranno dalle voci Wikipedia).
LEGGENDARI_PROVA = {"San Pietro", "San Paolo di Tarso", "San Francesco d'Assisi",
                    "Sant'Agostino d'Ippona", "San Giovanni Paolo II", "Santa Giovanna d'Arco",
                    "San Tommaso d'Aquino", "Santa Madre Teresa di Calcutta", "San Giovanni Battista",
                    "San Giovanni XXIII", "San Giorgio", "San Nicola di Bari"}


# --- Disegno ------------------------------------------------------------------

class Canvas:
    """RGBA layer (48x48 by default) drawn with aliased PIL primitives (pixel-exact)."""

    def __init__(self, w=S, h=S):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def ell(self, box, c):
        self.d.ellipse(box, fill=c + (255,))

    def ring(self, box, c):
        self.d.ellipse(box, outline=c + (255,))

    def rect(self, box, c):
        self.d.rectangle(box, fill=c + (255,))

    def poly(self, pts, c):
        self.d.polygon(pts, fill=c + (255,))

    def line(self, pts, c, w=1):
        self.d.line(pts, fill=c + (255,), width=w)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img.putpixel((x, y), c + (255,))

    def hole(self, box):
        """Clear pixels so the background shows through (e.g. a key ring)."""
        self.d.ellipse(box, fill=(0, 0, 0, 0))

    def recolor(self, box, src, dst):
        """Replace color [src] with [dst] inside [box] (for shading one part only)."""
        x0, y0, x1, y1 = box
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                if self.img.getpixel((x, y))[:3] == src:
                    self.img.putpixel((x, y), dst + (255,))


def h(name, salt):
    return int(hashlib.sha1(f"{salt}:{name}".encode()).hexdigest(), 16)


def draw_halo(c, t):
    fill, ring = (HALO_BEATO, HALO_BEATO_RING) if t.beato else (HALO, HALO_RING)
    c.ell((8, 1, 40, 33), ring)
    c.ell((9, 2, 39, 32), fill)


def body_base(c, robe):
    c.ell((5, 32, 43, 64), robe)
    c.recolor((31, 32, 47, 47), robe, shade(robe, 0.8))
    c.recolor((0, 32, 13, 47), robe, shade(robe, 1.15))


def mozzetta(c, col):
    c.poly([(6, 40), (10, 34), (20, 32), (28, 32), (38, 34), (42, 40), (24, 44)], col)


def draw_body(c, t, robe, skin):
    a = t.abito
    if a == "nudo":
        body_base(c, skin)
        c.rect((5, 43, 43, 47), (220, 220, 210))  # panno
        return
    if a in ("armatura", "crociato"):
        body_base(c, STEEL)
        c.recolor((31, 32, 47, 47), STEEL, STEEL_DARK)
        c.ell((4, 32, 16, 40), STEEL_LIGHT)          # spallacci
        c.ell((32, 32, 44, 40), STEEL_DARK)
        if a == "crociato":
            c.rect((14, 36, 34, 47), WHITE)
            c.rect((22, 37, 26, 47), RED)
            c.rect((17, 40, 31, 43), RED)
        if "mantello" in t.extra:  # San Martino: il mantello diviso col povero
            c.poly([(5, 47), (5, 37), (11, 33), (16, 34), (14, 47)], RED)
        return
    if a == "pelliccia":
        body_base(c, (176, 120, 66))
        for x, y in ((10, 38), (16, 42), (30, 37), (36, 43), (22, 45), (13, 46), (33, 46)):
            c.px(x, y, (130, 84, 44)); c.px(x + 1, y + 1, (206, 156, 96))
        c.poly([(43, 47), (43, 38), (36, 33), (30, 33), (34, 47)], (170, 40, 50))  # manto rosso
        return
    if a == "righe":
        body_base(c, (210, 214, 224))
        for x in range(7, 43, 4):
            c.recolor((x, 32, x + 1, 47), (210, 214, 224), (70, 90, 150))
            c.recolor((x, 32, x + 1, 47), shade((210, 214, 224), 0.8), shade((70, 90, 150), 0.8))
            c.recolor((x, 32, x + 1, 47), shade((210, 214, 224), 1.15), shade((70, 90, 150), 1.15))
        c.rect((14, 39, 19, 41), WHITE); c.line([(15, 40), (18, 40)], BLACK)  # numero
        return
    if a == "sari":
        body_base(c, WHITE)
        c.line([(10, 36), (20, 47)], (40, 90, 170), 2)
        c.line([(38, 36), (28, 47)], (40, 90, 170), 2)
        return
    body_base(c, robe)
    if a == "apostolo":  # manto su una spalla
        mantle = (204, 160, 70) if robe[2] > robe[0] else (180, 60, 60)
        c.poly([(5, 47), (5, 38), (12, 33), (20, 33), (34, 47)], mantle)
    elif a == "saio":
        c.line([(24, 35), (24, 47)], (230, 220, 190))  # cordone
        c.px(23, 44, (230, 220, 190)); c.px(25, 45, (230, 220, 190))
    elif a == "domenicano":
        c.poly([(5, 47), (6, 37), (13, 33), (19, 34), (17, 47)], BLACK)
        c.poly([(43, 47), (42, 37), (35, 33), (29, 34), (31, 47)], BLACK)
    elif a == "cistercense":
        c.rect((19, 34, 29, 47), BLACK)               # scapolare nero sull'abito bianco
    elif a in ("vescovo", "papa"):
        if a == "papa":
            mozzetta(c, RED)
        c.rect((21, 34, 27, 47), GOLD)                # stola / pallio
        c.rect((22, 34, 26, 47), shade(GOLD, 1.1))
        c.rect((23, 38, 25, 40), robe); c.px(24, 37, robe); c.px(24, 41, robe)
    elif a == "cardinale":
        mozzetta(c, shade(RED, 0.9))
        for y in range(36, 47, 3):
            c.px(24, y, (40, 30, 30))                 # bottoni
    elif a == "regale":
        mozzetta(c, WHITE)                            # ermellino
        for x, y in ((12, 37), (18, 39), (24, 40), (30, 39), (36, 37)):
            c.px(x, y, BLACK)
    elif a == "suora":
        c.poly([(14, 33), (34, 33), (31, 41), (24, 43), (17, 41)], WHITE)  # soggolo sul petto
    elif a == "dalmatica":
        c.rect((15, 34, 17, 47), GOLD); c.rect((31, 34, 33, 47), GOLD)   # clavi
        c.rect((17, 41, 31, 42), GOLD)
    elif a == "talare":
        c.rect((22, 32, 26, 34), WHITE)               # collare
        for y in range(37, 47, 3):
            c.px(24, y, shade(robe, 0.6))
    elif a == "camice":
        c.poly([(18, 33), (24, 40), (30, 33)], (110, 140, 190))  # vestito sotto il camice
        c.line([(19, 36), (19, 44)], (60, 60, 70)); c.ell((18, 44, 21, 46), STEEL)  # stetoscopio
    elif a == "moderno":
        c.poly([(19, 33), (24, 37), (29, 33)], shade(robe, 0.75))  # scollo
    if "manto_azzurro" in t.extra:  # manto della Madonna sopra l'abito rosso
        c.poly([(5, 47), (6, 38), (13, 33), (18, 34), (16, 47)], (56, 96, 176))
        c.poly([(43, 47), (42, 38), (35, 33), (30, 34), (32, 47)], (44, 78, 150))
    if "croce_rossa" in t.extra:
        c.rect((12, 37, 14, 43), RED); c.rect((10, 39, 16, 41), RED)
    if "sole_petto" in t.extra:  # San Tommaso d'Aquino
        c.ell((19, 36, 29, 46), GOLD); c.ell((21, 38, 27, 44), GOLD_LIGHT)
        for (x, y) in ((24, 34), (17, 41), (31, 41), (24, 47)):
            c.px(x, y, GOLD)
    if "medaglione" in t.extra:  # San Giuda Taddeo
        c.ell((20, 37, 28, 45), GOLD); c.ell((22, 39, 26, 43), (234, 186, 146))
        c.px(23, 40, EYE); c.px(25, 40, EYE)


def draw_head(c, skin):
    c.rect((21, 28, 27, 34), shade(skin, 0.88))   # collo
    c.ell((16, 10, 32, 30), skin)                 # testa
    c.recolor((29, 10, 33, 30), skin, shade(skin, 0.9))
    c.ell((14, 18, 17, 23), skin)                 # orecchie
    c.ell((31, 18, 34, 23), shade(skin, 0.9))


def draw_face(c, t, skin, name):
    ey = 20
    occhi = h(name, "occhi") % 3
    bocca = h(name, "bocca") % 3
    for x in (20, 27):
        if occhi == 2:                            # occhi socchiusi / assorti
            c.line([(x - 1, ey + 1), (x, ey + 1)] if x == 20 else [(x, ey + 1), (x + 1, ey + 1)], EYE)
        else:
            c.px(x, ey, EYE); c.px(x, ey + 1, EYE)
            c.px(x + (1 if x == 20 else -1), ey, (250, 250, 250))
    if occhi == 1 or t.eta == "anziano":          # sopracciglia
        col = shade(skin, 0.6) if t.eta == "anziano" else shade(skin, 0.5)
        c.line([(19, 18), (21, 18)], col); c.line([(26, 18), (28, 18)], col)
    c.px(24, 23, shade(skin, 0.78))               # naso
    c.px(23, 24, shade(skin, 0.85))
    if bocca == 0:
        c.line([(22, 26), (26, 26)], MOUTH)
    elif bocca == 1:                              # sorriso
        c.line([(22, 26), (26, 26)], MOUTH); c.px(21, 25, MOUTH); c.px(27, 25, MOUTH)
    else:
        c.line([(23, 26), (25, 26)], MOUTH)
    if t.eta == "anziano":
        c.px(18, 24, shade(skin, 0.85)); c.px(30, 24, shade(skin, 0.8))  # rughe
    if t.donna:
        c.px(19, 24, (236, 150, 150)); c.px(29, 24, (236, 150, 150))
        if occhi != 2:
            c.line([(19, 19), (21, 19)], EYE); c.line([(26, 19), (28, 19)], EYE)  # ciglia
    if "ferita_fronte" in t.extra:
        c.px(24, 15, DARK_RED); c.px(24, 16, RED)
    if "cuffie" in t.extra:  # San Deploy: cuffie con microfono
        c.d.arc((14, 5, 34, 27), 180, 360, fill=(40, 40, 46, 255), width=2)  # archetto sottile
        c.rect((12, 16, 16, 24), (60, 60, 70)); c.rect((32, 16, 36, 24), (60, 60, 70))
        c.line([(15, 25), (21, 28)], (60, 60, 70)); c.px(22, 28, RED)
    if "occhiali" in t.extra:
        for x in (18, 25):
            c.d.rectangle((x, 19, x + 4, 22), outline=(40, 40, 46, 255))
        c.line([(23, 20), (24, 20)], (40, 40, 46))


def draw_hair(c, t, hair, skin):
    st = t.capelli
    if st == "nessuno" or t.copricapo in ("velo", "cappuccio", "sari"):
        return
    if st == "calvo":
        c.rect((15, 17, 17, 24), hair); c.rect((31, 17, 33, 24), hair)
        c.px(22, 12, shade(skin, 1.12)); c.px(23, 12, shade(skin, 1.12))
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


def veil_color(t, robe):
    if t.colore_velo:
        return t.colore_velo
    return robe if t.abito == "suora" else (70, 90, 150)


def draw_cover_back(c, t, robe):
    """Parts of the headwear that sit behind the face (veil, hood, sari)."""
    cp = t.copricapo
    if cp == "velo":
        v = veil_color(t, robe)
        c.ell((13, 6, 35, 30), v)
        c.rect((13, 18, 35, 40), v)
        c.recolor((30, 6, 35, 40), v, shade(v, 0.82))
        if t.abito == "suora":
            c.ell((16, 10, 32, 32), WHITE)        # soggolo
    elif cp == "sari":
        c.ell((13, 6, 35, 30), WHITE)
        c.rect((13, 18, 35, 40), WHITE)
        c.ring((13, 6, 35, 30), (40, 90, 170))    # bordo blu del sari
        c.ring((14, 7, 34, 29), (40, 90, 170))
    elif cp == "cappuccio":
        c.ell((12, 6, 36, 32), robe)
        c.recolor((30, 6, 36, 32), robe, shade(robe, 0.8))
        c.ell((15, 9, 33, 31), shade(robe, 0.5))   # interno in ombra
        c.ring((14, 8, 34, 32), shade(robe, 1.3))   # bordo chiaro: si stacca dai capelli


def draw_cover_front(c, t, skin):
    cp = t.copricapo
    if cp in ("velo", "sari"):
        c.ell((18, 13, 30, 29), skin)             # viso dentro il velo
        c.recolor((28, 13, 30, 29), skin, shade(skin, 0.9))
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
    elif cp == "corona_rose":
        for i, x in enumerate(range(16, 33, 3)):
            c.ell((x - 1, 9, x + 1, 11), (210, 50, 80) if i % 2 else WHITE)
        c.line([(16, 12), (32, 12)], DARK_GREEN)
    elif cp == "elmo":
        c.ell((15, 6, 33, 20), STEEL)
        c.rect((15, 13, 33, 16), STEEL_DARK)
        c.ell((18, 14, 30, 30), skin)
        c.line([(24, 2), (24, 6)], RED, 2)       # pennacchio
    elif cp in ("zucchetto_rosso", "zucchetto_bianco"):
        c.ell((18, 8, 30, 14), RED if cp == "zucchetto_rosso" else WHITE)
    elif cp == "pellegrino":
        c.ell((10, 9, 38, 15), (120, 84, 52))     # tesa larga
        c.ell((16, 5, 32, 13), (140, 98, 60))
        c.ell((22, 8, 26, 11), (240, 228, 200))   # conchiglia sul cappello
    if "stelle" in t.extra:  # corona di dodici stelle (qui sei, sull'aureola)
        for (x, y) in ((12, 8), (17, 4), (24, 2), (31, 4), (36, 8), (38, 15)):
            c.px(x, y, (255, 250, 210))
    if "spine" in t.extra:
        for x in range(17, 32, 2):
            c.px(x, 13 + (x % 4 == 1), (90, 70, 40))
    if "stella" in t.extra:
        c.px(24, 14, GOLD); c.px(23, 15, GOLD_LIGHT); c.px(25, 15, GOLD_LIGHT); c.px(24, 16, GOLD)
    if "fiamma" in t.extra:
        c.poly([(24, 0), (21, 6), (24, 8), (27, 6)], (240, 140, 40)); c.px(24, 5, (255, 220, 90))


# --- Attributi (in mano a destra, in basso a destra o sul petto) ---------------

def at_chiavi(c):
    for dx, col in ((0, GOLD), (4, STEEL_LIGHT)):
        x = 37 + dx
        c.ell((x - 2, 22, x + 2, 26), col); c.d.point((x, 24), fill=(0, 0, 0, 0))
        c.line([(x, 26), (x, 44)], col)
        c.rect((x + 1, 40, x + 2, 41), col); c.rect((x + 1, 43, x + 2, 44), col)


def at_frecce(c):
    for (x0, y0, x1, y1) in ((8, 33, 22, 44), (40, 30, 28, 42), (12, 46, 24, 38)):
        c.line([(x0, y0), (x1, y1)], (110, 80, 50))
        c.px(x0, y0, STEEL); c.px(x0 + (1 if x0 < x1 else -1), y0, (230, 230, 230))


def at_palma(c):
    c.line([(41, 46), (41, 22)], DARK_GREEN)
    for y in range(23, 40, 3):
        c.line([(41, y), (37, y + 3)], GREEN); c.line([(41, y), (45, y + 3)], GREEN)


def at_spada(c):
    c.line([(41, 14), (41, 38)], STEEL_LIGHT, 2)
    c.line([(37, 38), (45, 38)], GOLD)
    c.line([(41, 39), (41, 44)], WOOD)
    c.px(41, 45, GOLD)


def at_lancia(c):
    c.line([(42, 2), (42, 47)], WOOD)
    c.poly([(42, 0), (40, 5), (44, 5)], STEEL_LIGHT)


def _fiore(c, col, centre):
    c.line([(40, 46), (40, 24)], DARK_GREEN)
    c.line([(40, 34), (37, 31)], GREEN); c.line([(40, 30), (43, 27)], GREEN)
    for (x, y) in ((40, 20), (38, 22), (42, 22), (40, 23)):
        c.ell((x - 1, y - 1, x + 1, y + 1), col)
    c.px(40, 22, centre)


def at_giglio(c):
    _fiore(c, WHITE, GOLD)


def at_rosa(c):
    _fiore(c, (210, 40, 70), DARK_RED)


def at_libro(c):
    c.rect((29, 36, 39, 45), (150, 40, 40))
    c.rect((30, 37, 38, 44), (176, 56, 50))
    c.line([(29, 45), (39, 45)], (240, 232, 200))
    c.rect((33, 39, 35, 41), GOLD)


def at_croce(c):
    c.line([(41, 14), (41, 46)], WOOD, 2)
    c.line([(37, 20), (45, 20)], WOOD, 2)


def at_crocifisso(c):
    c.line([(41, 22), (41, 44)], WOOD, 2)
    c.line([(37, 27), (45, 27)], WOOD, 2)
    c.px(41, 26, (234, 186, 146)); c.line([(40, 28), (42, 28)], (234, 186, 146)); c.px(41, 30, (234, 186, 146))


def at_pastorale(c):
    c.line([(41, 10), (41, 47)], GOLD_DARK, 2)
    c.ell((38, 3, 45, 11), GOLD)
    c.hole((40, 5, 43, 9))


def at_occhi(c):
    c.ell((31, 38, 45, 44), GOLD)
    c.ell((32, 39, 44, 43), GOLD_LIGHT)
    for x in (35, 40):
        c.ell((x - 1, 40, x + 1, 42), WHITE); c.px(x, 41, (60, 90, 160))


def at_croce_x(c):  # croce decussata di Sant'Andrea, dietro la spalla
    c.line([(33, 20), (46, 46)], WOOD, 3)
    c.line([(46, 20), (33, 46)], WOOD, 3)


def at_bordone(c):  # bastone del pellegrino con la zucca
    c.line([(42, 6), (42, 47)], WOOD, 2)
    c.ell((40, 12, 45, 18), (200, 150, 70))


PROVOLA, PROVOLA_D, PROVOLA_L = (238, 214, 150), (204, 168, 96), (252, 240, 200)


def at_bordone_provola(c):  # San Rocco: "mannaggia la provola di San Rocco", la sua zucca presa per una provola
    c.line([(42, 6), (42, 47)], WOOD, 2)
    c.ell((41, 9, 44, 12), PROVOLA)                 # la testina
    c.line([(40, 13), (45, 13)], (120, 84, 44))      # lo spago
    c.ell((38, 14, 47, 24), PROVOLA)                 # la pancia
    c.ell((39, 19, 47, 24), PROVOLA_D)               # ombra in basso
    c.ell((39, 15, 43, 18), PROVOLA_L)               # lucido


def at_conchiglia(c):
    c.poly([(20, 41), (24, 35), (28, 41)], (240, 228, 200))
    c.line([(22, 40), (24, 36)], (200, 180, 150)); c.line([(26, 40), (24, 36)], (200, 180, 150))


def at_aquila(c):
    c.ell((32, 36, 44, 47), (120, 84, 44))       # corpo
    c.ell((35, 31, 42, 38), (140, 100, 56))      # testa
    c.px(38, 33, EYE); c.poly([(42, 34), (45, 35), (42, 36)], GOLD)  # becco
    c.line([(32, 38), (30, 45)], shade((120, 84, 44), 0.7))


def at_leone(c):
    c.ell((31, 31, 46, 46), (190, 120, 50))      # criniera
    c.ell((34, 34, 43, 44), (226, 170, 80))      # muso
    c.px(36, 37, EYE); c.px(41, 37, EYE)
    c.rect((38, 40, 39, 41), (120, 70, 40))


def at_bue(c):
    c.ell((33, 34, 45, 46), (150, 100, 66))
    c.line([(33, 34), (31, 30)], (240, 230, 210)); c.line([(45, 34), (47, 30)], (240, 230, 210))  # corna
    c.px(36, 38, EYE); c.px(42, 38, EYE)
    c.ell((36, 41, 42, 45), (200, 150, 120))


def at_agnello(c):
    for (x, y) in ((34, 39), (38, 37), (42, 39), (36, 43), (40, 43)):
        c.ell((x - 3, y - 3, x + 3, y + 3), WHITE)
    c.ell((40, 33, 46, 39), (60, 56, 60)); c.px(44, 35, (250, 250, 250))  # testa


def at_ruota(c):
    c.ring((32, 32, 46, 46), WOOD_DARK); c.ring((33, 33, 45, 45), WOOD)
    c.line([(39, 33), (39, 45)], WOOD); c.line([(33, 39), (45, 39)], WOOD)
    c.line([(35, 35), (43, 43)], WOOD); c.line([(43, 35), (35, 43)], WOOD)
    for (x, y) in ((39, 31), (47, 39), (39, 47), (31, 39)):
        c.px(x, y, STEEL_LIGHT)


def at_graticola(c):
    c.rect((31, 34, 45, 45), (60, 56, 60))
    for x in range(33, 45, 3):
        c.line([(x, 35), (x, 44)], STEEL)
    c.line([(38, 45), (38, 47)], (60, 56, 60))


def at_coltello(c):
    c.line([(41, 22), (41, 35)], STEEL_LIGHT, 2)
    c.line([(41, 36), (41, 43)], WOOD, 2)


def at_scopa(c):  # San Martino de Porres's broom
    c.line([(34, 18), (40, 38)], WOOD, 2)
    c.poly([(37, 37), (44, 35), (47, 47), (39, 47)], (200, 160, 80))
    for x in (40, 42, 44):
        c.line([(x, 39), (x + 1, 47)], (150, 116, 56))


def at_bastone(c):
    c.line([(42, 8), (41, 47)], WOOD, 3)


def at_sega(c):
    c.rect((37, 18, 43, 40), STEEL)
    for y in range(19, 40, 2):
        c.px(36, y, STEEL_DARK)
    c.rect((38, 40, 42, 46), WOOD)


def at_ascia(c):
    c.line([(42, 14), (42, 47)], WOOD, 2)
    c.poly([(42, 14), (36, 12), (35, 20), (42, 20)], STEEL_LIGHT)


def at_penna(c):
    c.line([(30, 30), (36, 38)], WHITE, 2); c.px(37, 39, BLACK)


def at_vaso(c):
    c.ell((34, 34, 44, 46), (238, 230, 210)); c.rect((36, 31, 42, 35), GOLD)
    c.rect((37, 29, 41, 31), (238, 230, 210))


def at_pietre(c):
    for (x, y) in ((34, 42), (40, 40), (37, 37), (43, 44)):
        c.ell((x - 2, y - 2, x + 2, y + 2), (140, 136, 130))
        c.px(x - 1, y - 1, (180, 176, 170))


def at_drago(c):
    c.ell((30, 38, 46, 47), (70, 130, 60))
    c.ell((38, 33, 46, 41), (80, 150, 70))
    c.px(43, 36, (240, 200, 40)); c.poly([(46, 38), (47, 40), (44, 40)], RED)  # lingua


def at_tenaglia(c):
    c.line([(38, 24), (42, 44)], STEEL_DARK, 2); c.line([(44, 24), (40, 44)], STEEL_DARK, 2)
    c.ell((39, 21, 43, 25), WHITE)  # il dente


def at_torre(c):
    c.rect((35, 22, 45, 47), (170, 164, 156))
    for x in (35, 38, 41, 44):
        c.rect((x, 19, x + 1, 22), (170, 164, 156))
    c.rect((39, 28, 41, 32), BLACK); c.rect((39, 37, 41, 41), BLACK)
    c.recolor((42, 19, 45, 47), (170, 164, 156), (136, 130, 124))


def at_organo(c):
    for i, x in enumerate(range(34, 46, 2)):
        c.rect((x, 28 + abs(i - 3) * 2, x + 1, 44), GOLD if i % 2 else GOLD_LIGHT)
    c.rect((33, 44, 46, 47), WOOD)


def at_cane(c):
    c.ell((32, 40, 44, 47), (150, 110, 70))
    c.ell((38, 34, 46, 42), (170, 128, 84))
    c.px(43, 37, EYE); c.px(46, 39, BLACK)
    c.poly([(39, 34), (38, 38), (41, 36)], (110, 80, 50))  # orecchio


def at_bambino(c):  # Gesu' Bambino sulla spalla sinistra
    c.ell((4, 18, 16, 30), HALO)
    c.ell((6, 20, 14, 28), (246, 208, 176))
    c.px(8, 23, EYE); c.px(11, 23, EYE)
    c.ell((4, 27, 16, 38), WHITE)


def at_cuore(c):
    c.ell((33, 34, 39, 40), RED); c.ell((38, 34, 44, 40), RED)
    c.poly([(33, 38), (44, 38), (38, 45)], RED); c.px(35, 36, (240, 120, 120))


def at_palle(c):  # le tre palle d'oro di San Nicola, sul libro
    for x in (31, 34, 37):
        c.ell((x - 1, 32, x + 2, 35), GOLD)


def at_trifoglio(c):
    for (x, y) in ((33, 37), (37, 37), (35, 34)):
        c.ell((x - 2, y - 2, x + 2, y + 2), GREEN)
    c.line([(35, 39), (36, 43)], DARK_GREEN)


def at_frusta(c):  # lo staffile di Sant'Ambrogio
    c.line([(36, 26), (36, 34)], WOOD, 2)
    for dx in (-2, 0, 2):
        c.line([(36, 34), (36 + dx * 2, 44)], (90, 60, 40))


def at_citta(c):  # modellino di citta' (San Petronio)
    c.rect((31, 38, 45, 46), (200, 120, 80))
    c.rect((34, 31, 37, 38), (200, 120, 80)); c.rect((40, 33, 43, 38), (180, 100, 70))
    c.px(35, 30, (200, 120, 80)); c.rect((35, 41, 36, 43), BLACK); c.rect((40, 41, 41, 43), BLACK)


def at_pesce(c):
    c.ell((33, 40, 43, 45), (120, 150, 170)); c.poly([(43, 42), (46, 39), (46, 46)], (120, 150, 170))
    c.px(35, 42, EYE)


def at_candele(c):  # le candele incrociate di San Biagio
    c.line([(34, 44), (44, 28)], WHITE, 2); c.line([(44, 44), (34, 28)], WHITE, 2)
    c.px(44, 26, (250, 180, 50)); c.px(34, 26, (250, 180, 50))


def at_colomba(c):
    c.ell((33, 22, 43, 28), WHITE); c.ell((40, 19, 45, 24), WHITE)
    c.px(43, 21, EYE); c.px(46, 22, GOLD); c.poly([(33, 25), (29, 21), (36, 23)], (220, 220, 230))


def at_ostensorio(c):
    c.ell((33, 22, 45, 34), GOLD); c.ell((36, 25, 42, 31), WHITE)
    c.line([(39, 34), (39, 43)], GOLD, 2); c.rect((35, 43, 43, 45), GOLD)


def at_ihs(c):  # il trigramma nel sole di San Bernardino
    c.ell((32, 30, 46, 44), GOLD); c.ell((34, 32, 44, 42), (40, 70, 150))
    for x in (36, 39, 42):
        c.line([(x, 34), (x, 40)], GOLD_LIGHT)
    c.line([(39, 37), (42, 37)], GOLD_LIGHT)


def at_caritas(c):  # il sole con "CHARITAS" di San Francesco da Paola
    c.ell((32, 30, 46, 44), GOLD); c.ell((34, 32, 44, 42), GOLD_LIGHT)
    c.line([(36, 37), (42, 37)], DARK_RED)


def at_tau(c):  # il bastone a T di Sant'Antonio abate, con la campanella
    c.line([(42, 10), (42, 47)], WOOD, 2)
    c.line([(38, 10), (46, 10)], WOOD, 2)
    c.ell((43, 13, 46, 17), GOLD)


def at_maialino(c):
    c.ell((3, 39, 15, 47), (236, 170, 170))
    c.ell((12, 41, 17, 45), (226, 150, 150)); c.px(15, 43, (170, 90, 90))
    c.px(10, 41, EYE); c.poly([(6, 39), (8, 36), (9, 40)], (226, 150, 150))


def at_teschio(c):
    c.ell((33, 37, 41, 45), (236, 230, 214)); c.rect((35, 44, 39, 46), (236, 230, 214))
    c.px(35, 40, BLACK); c.px(38, 40, BLACK); c.px(37, 42, (120, 110, 100))


def at_rosario(c):
    for i in range(9):
        c.px(19 + i, 36 + abs(i - 4), (90, 60, 40))
    c.line([(24, 41), (24, 45)], (90, 60, 40)); c.line([(23, 43), (25, 43)], (90, 60, 40))


def at_arpa(c):  # l'arpa di re Davide
    c.line([(35, 46), (35, 26)], GOLD_DARK, 2)
    c.line([(35, 26), (45, 32)], GOLD, 2)
    c.line([(45, 32), (44, 46)], GOLD_DARK)
    for x in range(37, 44, 2):
        c.line([(x, 28 + (x - 35) // 2 + 1), (x, 45)], (240, 236, 220))


def at_striscione(c):  # "SANTO SUBITO": striscione bianco con righe rosse
    c.line([(32, 14), (32, 46)], WOOD); c.line([(46, 14), (46, 46)], WOOD)
    c.rect((32, 16, 46, 30), WHITE)
    c.line([(34, 20), (44, 20)], RED); c.line([(34, 23), (44, 23)], RED); c.line([(34, 26), (41, 26)], RED)


def at_ferro_cavallo(c):
    c.ell((32, 24, 45, 38), STEEL); c.d.ellipse((35, 27, 42, 37), fill=(0, 0, 0, 0))
    c.d.rectangle((35, 33, 42, 38), fill=(0, 0, 0, 0))
    for (x, y) in ((33, 29), (44, 29), (33, 33), (44, 33)):
        c.px(x, y, STEEL_DARK)


def at_quadrifoglio(c):
    for (x, y) in ((20, 37), (25, 37), (20, 41), (25, 41)):
        c.ell((x - 2, y - 2, x + 2, y + 2), GREEN)
    c.px(22, 39, DARK_GREEN); c.line([(23, 41), (25, 46)], DARK_GREEN)


def at_calendario_mano(c):
    c.rect((32, 30, 45, 45), (246, 242, 232)); c.rect((32, 30, 45, 33), RED)
    c.px(35, 29, STEEL_DARK); c.px(42, 29, STEEL_DARK)
    c.poly([(38, 35), (39, 38), (42, 38), (40, 40), (41, 43), (38, 41), (35, 43), (36, 40), (34, 38), (37, 38)], GOLD)


def at_server_fuoco(c):  # il server che va in fiamme il venerdi' alle 18
    c.rect((32, 28, 45, 46), (60, 64, 76))
    for y in (31, 36, 41):
        c.rect((34, y, 43, y + 2), (36, 38, 46)); c.px(42, y + 1, (90, 220, 90))
    c.poly([(36, 28), (35, 22), (38, 25), (39, 19), (41, 24), (43, 21), (43, 28)], (240, 130, 40))
    c.poly([(38, 28), (38, 25), (40, 23), (41, 28)], (255, 220, 90))


def at_terminale(c):  # portatile con il prompt verde
    c.rect((28, 34, 46, 44), (40, 42, 50)); c.rect((29, 35, 45, 42), (16, 20, 18))
    c.line([(30, 37), (32, 37)], (90, 230, 110)); c.px(34, 37, (90, 230, 110))   # "$ _"
    c.line([(30, 40), (38, 40)], (60, 170, 80))
    c.rect((26, 44, 47, 46), (110, 114, 124))


def at_sassofono(c):  # tenor sax held at the side: crook and mouthpiece up, body down, flared bell turned up
    BRASS, BRASS_DARK, BRASS_LIGHT = (226, 176, 64), (164, 116, 34), (250, 222, 140)
    c.line([(32, 21), (35, 24)], BRASS_DARK); c.px(31, 20, BLACK)                  # crook, mouthpiece
    c.line([(36, 24), (37, 41)], BRASS, 3)                                          # body
    c.line([(37, 43), (42, 42)], BRASS, 3)                                          # U-bend
    c.poly([(40, 42), (44, 42), (46, 31), (39, 31)], BRASS)                         # the bell, flaring upwards
    c.line([(39, 31), (46, 31)], BRASS_DARK); c.line([(40, 32), (45, 32)], (70, 50, 22))   # its rim and opening
    for y in (28, 32, 36, 40):
        c.px(35, y, BRASS_DARK)                                                     # keys
    c.line([(37, 25), (38, 40)], BRASS_LIGHT)                                       # lit edge


def at_clessidra(c):
    c.rect((33, 26, 45, 27), WOOD); c.rect((33, 45, 45, 46), WOOD)
    c.poly([(34, 28), (44, 28), (39, 36)], (220, 230, 240)); c.poly([(34, 44), (44, 44), (39, 36)], (220, 230, 240))
    c.poly([(36, 29), (42, 29), (39, 33)], (230, 200, 120)); c.poly([(35, 44), (43, 44), (39, 40)], (230, 200, 120))
    c.line([(39, 34), (39, 40)], (230, 200, 120))


def at_fulmine(c):  # "ti strafulmini": la saetta alzata
    c.poly([(40, 12), (34, 24), (38, 24), (33, 34), (44, 20), (40, 20), (44, 12)], GOLD_LIGHT)
    c.line([(40, 13), (35, 23)], WHITE)


def at_sfere(c):  # "bipalluta": due sfere d'oro in mano
    for x in (32, 39):
        c.ell((x, 37, x + 5, 42), GOLD); c.px(x + 1, 38, GOLD_LIGHT); c.px(x + 4, 41, GOLD_DARK)


ATTRIBUTI = {name[3:]: fn for name, fn in globals().items() if name.startswith("at_")}


def draw_attributes(c, t):
    for a in t.attributo.split("+"):
        if a != "nessuno":
            ATTRIBUTI[a](c)
    if "stigmate" in t.extra:
        c.px(24, 39, DARK_RED)


# --- Composizione -------------------------------------------------------------

def outline(layer, col=OUTLINE):
    """Dark 1-px outline (or [col]) around everything drawn (on transparent neighbours)."""
    src = layer.copy()
    out = layer.copy()
    w, h = layer.size
    for y in range(h):
        for x in range(w):
            if src.getpixel((x, y))[3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src.getpixel((nx, ny))[3]:
                    out.putpixel((x, y), col + (255,))
                    break
    return out


def categoria(t):
    if t.abito == "papa":
        return "papa"
    if t.abito in ("vescovo", "cardinale"):
        return "vescovo"
    if t.martire:
        return "martire"
    if t.abito in ("saio", "benedettino", "domenicano", "cistercense", "suora", "talare"):
        return "religioso"
    if t.abito == "regale":
        return "regale"
    if t.abito in ("armatura", "crociato"):
        return "guerriero"
    return None


# Skin set by hand: the name hash picks only among the 3 lightest SKINS, and Wikidata has no reliable
# data for it. Checked on the Wikidata images (2026-11-12); more come from the users' reports.
# Value: an index in SKINS or an RGB. These saints also get black hair, unless old or set in FAMOSI.
PELLE = {
    "Santa Giuseppina Bakhita": 5, "San Mosè l'Etiope": 5, "Beata Maria Clementina Anuarite Nengapeta": 5,
    "Beato Isidore Bakanja": 5, "Santa Sara la Nera": 4, "San Martino de Porres": 4, "Sant'Agostino d'Ippona": 3,
    # the martyrs of Uganda in the list
    "San Carlo Lwanga": 5, "San Kizito": 4, "San Joseph Mukasa": 5, "San Gyaviira Mayanja Musoke": 4,
    "Sant'Achilleo Kiwanuka": 5, "Sant'Ambrogio Kibuuka": 4, "Sant'Andrea Kaggwa": 5, "Beato Davide Okelo": 4,
    "Beato Gildo Irwa": 5,
    "Sant'Andrea Kim Taegon": (226, 180, 140), "San Paolo Miki": (220, 174, 132), "Sant'Agostino Zhao Rong": (216, 168, 126),
    "San Lorenzo Ruiz": (192, 138, 94), "Santa Kateri Tekakwitha": (176, 118, 80),
    "San Juan Diego Cuauhtlatoatzin": (168, 112, 74), "San Charbel Makhluf": (216, 168, 128),
    "San Kuriakose Elias Chavara": (154, 102, 68),
}


def pelle_di(name, t):
    p = PELLE.get(name, t.pelle)
    if p is None:
        p = [0, 1, 1, 2][h(name, "pelle") % 4]
    return SKINS[p] if isinstance(p, int) else p


def render(name, t):
    skin = pelle_di(name, t)
    hair = HAIRS[t.colore_capelli or ("nero" if name in PELLE else None)
                 or ["nero", "castano", "castano", "biondo", "rosso", "nero"][h(name, "capelli") % 6]]
    if t.eta == "anziano" and not t.colore_capelli:
        hair = HAIRS["grigio" if h(name, "grigio") % 2 else "bianco"]
    robe = t.colore_abito or {
        "saio": BROWN_HABIT, "benedettino": BLACK_HABIT, "domenicano": WHITE, "suora": BLACK_HABIT,
        "cardinale": RED, "papa": WHITE, "cistercense": WHITE, "talare": BLACK_HABIT,
        "dalmatica": (170, 40, 50), "camice": WHITE,
    }.get(t.abito) or ROBES[h(name, "abito") % len(ROBES)]
    bg = BG_CATEGORIA.get(categoria(t)) or BACKGROUNDS[h(name, "sfondo") % len(BACKGROUNDS)]

    halo = Canvas()
    draw_halo(halo, t)
    fig = Canvas()
    draw_body(fig, t, robe, skin)
    draw_cover_back(fig, t, robe)
    draw_head(fig, skin)
    draw_hair(fig, t, hair, skin)
    draw_cover_front(fig, t, skin)
    draw_face(fig, t, skin, name)
    draw_beard(fig, t, hair)
    draw_attributes(fig, t)

    img = Image.new("RGBA", (S, S), bg + (255,))
    ImageDraw.Draw(img).rectangle((0, 36, S, S), fill=shade(bg, 0.85) + (255,))
    img.alpha_composite(outline(halo.img))
    img.alpha_composite(outline(fig.img))
    return img


def decollato():
    """The secret back of San Giovanni Battista: only his head (no neck, no body) resting on a
    gold platter, as in the paintings with Salome; paler skin, cartoon "X" eyes and the tongue
    out, no blood. Same traits and seed as his front."""
    name = "San Giovanni Battista"
    t = FAMOSI[name]
    skin = mix(pelle_di(name, t), (236, 232, 226), 0.35)
    hair = HAIRS[t.colore_capelli]
    bg = BG_CATEGORIA.get(categoria(t)) or BACKGROUNDS[h(name, "sfondo") % len(BACKGROUNDS)]
    halo = Canvas()
    draw_halo(halo, t)
    fig = Canvas()
    fig.ell((16, 10, 32, 30), skin)                       # head, as draw_head but without the neck
    fig.recolor((29, 10, 33, 30), skin, shade(skin, 0.9))
    fig.ell((14, 18, 17, 23), skin); fig.ell((31, 18, 34, 23), shade(skin, 0.9))
    draw_hair(fig, t, hair, skin)
    draw_face(fig, t, skin, name)
    for x in (20, 27):                                    # cartoon "X" eyes
        fig.rect((x - 1, 19, x + 1, 21), skin)
        for dx, dy in ((-1, -1), (0, 0), (1, 1), (1, -1), (-1, 1)):
            fig.px(x + dx, 20 + dy, EYE)
    draw_beard(fig, t, hair)
    TONGUE = (226, 104, 120)                              # tongue out, raspberry style
    fig.rect((23, 27, 25, 30), TONGUE); fig.px(24, 31, TONGUE)
    fig.line([(24, 28), (24, 30)], shade(TONGUE, 0.8))
    img = Image.new("RGBA", (S, S), bg + (255,))
    ImageDraw.Draw(img).rectangle((0, 36, S, S), fill=shade(bg, 0.85) + (255,))
    img.alpha_composite(outline(halo.img), (0, 4))
    plate = Canvas()
    plate.ell((6, 36, 42, 46), GOLD_DARK); plate.ell((7, 36, 41, 44), GOLD_LIGHT); plate.ell((11, 37, 37, 43), GOLD)
    img.alpha_composite(outline(plate.img))
    img.alpha_composite(outline(fig.img).crop((0, 0, S, 43)), (0, 2))   # the head sits on the plate
    return img


# Gemme: scala di luminosita' della stessa tinta, dalla piu' scura alla piu' chiara.
GEM_RED = [(120, 20, 30), (178, 34, 44), (230, 70, 80), (255, 150, 150)]
GEM_BLUE = [(30, 60, 120), (60, 110, 190), (110, 160, 240), (190, 220, 255)]
FRAME_STEPS = 12  # fotogrammi dell'animazione: 12 x 167 ms = un giro ogni 2 secondi
FRAME_MS = 167


CORNERS = ((0, 0), (S - 5, 0), (S - 5, S - 5), (0, S - 5))


def _perimeter(inset=0):
    """Pixel coordinates along the ring [inset] px inside the edge, clockwise from the top-left corner."""
    a, b = inset, S - 1 - inset
    top = [(x, a) for x in range(a, b + 1)]
    right = [(b, y) for y in range(a + 1, b + 1)]
    bottom = [(x, b) for x in range(b - 1, a - 1, -1)]
    left = [(a, y) for y in range(b - 1, a, -1)]
    return top + right + bottom + left


def _gemma(c, x, y, palette, step, i):
    """Gem at (x, y). With [step] it cycles through the 4 light levels of [palette] with its
    own phase [i] (triangle wave 0,1,2,3,2,1, so gems don't blink together) and a white
    glint up-left at the peak; without it, the still gem palette[1]."""
    if step is None:
        c.px(x, y, palette[1])
        return
    k = (step + i * 3) % 6
    level = k if k < 4 else 6 - k
    c.px(x, y, palette[level])
    if level == 3:  # riflesso bianco al massimo della luce
        c.px(x - 1, y - 1, (255, 255, 255))


def _luccichio(c, step, plain, colours):
    """A short glint ([colours], 3 px) running once around the outer border per animation,
    only over the [plain] border colours (not over corners and gems)."""
    if step is None:
        return
    ring = _perimeter()
    start = step * len(ring) // FRAME_STEPS
    for j, col in enumerate(colours):
        x, y = ring[(start + j) % len(ring)]
        if c.img.getpixel((x, y))[:3] in plain:
            c.px(x, y, col)


def _schiarisci(col, f):
    """[col] moved a fraction [f] towards white."""
    return tuple(round(v + (255 - v) * f) for v in col)


def cornice(step=None):
    """Thin gold frame for legendary saints (transparent inside).

    With [step] (0..FRAME_STEPS-1) it is one frame of the sparkle animation: each gem
    cycles through the light levels of its colour with its own phase, and a short
    glint runs around the border. Without it, the still version.
    """
    c = Canvas()
    c.d.rectangle((0, 0, S - 1, S - 1), outline=GOLD_DARK + (255,))
    c.d.rectangle((1, 1, S - 2, S - 2), outline=GOLD_LIGHT + (255,))
    for i, (x, y) in enumerate(CORNERS):
        c.rect((x, y, x + 4, y + 4), GOLD)
        c.d.rectangle((x, y, x + 4, y + 4), outline=GOLD_DARK + (255,))
        _gemma(c, x + 2, y + 2, GEM_RED, step, i)
    for i, (x, y) in enumerate(((S // 2 - 1, 0), (S - 3, S // 2 - 1), (S // 2 - 1, S - 3), (0, S // 2 - 1))):
        c.rect((x, y, x + 2, y + 2), GOLD)
        _gemma(c, x + 1, y + 1, GEM_BLUE, step, i + 4)
    _luccichio(c, step, (GOLD_DARK, GOLD_LIGHT), (GOLD_LIGHT, (255, 250, 220), GOLD_LIGHT))
    return c.img

# Fiamme: dalla base (piu' calda, quasi bianca) alla punta (rosso scuro).
FUOCO = [(255, 250, 200), (255, 220, 80), (250, 150, 30), (220, 70, 20), (150, 30, 20)]


def cornice_fuoco(step=None):
    """Burning frame for Saint Joan of Arc, burned at the stake (transparent inside).

    Flames rise from the four edges, taller at the bottom, with a few sparks going up
    the sides. With [step] (0..FRAME_STEPS-1) it is one frame of the animation, which
    loops seamlessly; without it, the still version (step 0).
    """
    step = step or 0
    t = 2 * math.pi * step / FRAME_STEPS
    c = Canvas()
    c.d.rectangle((0, 0, S - 1, S - 1), outline=(60, 24, 16, 255))

    def fiamma(pos, base, alta):
        """Flame height at [pos] along an edge: two waves, both periodic over the loop."""
        v = math.sin(pos * 0.9 - 2 * t) + 0.7 * math.sin(pos * 0.37 + t)
        return max(1, round(base + alta * v))

    def colonna(pts):
        """One flame tongue, coloured from the base (pts[0]) to the tip."""
        n = len(pts)
        for k, (x, y) in enumerate(pts):
            c.px(x, y, FUOCO[min(len(FUOCO) - 1, (k * len(FUOCO)) // n + (1 if n < 3 else 0))])

    for x in range(S):
        colonna([(x, S - 1 - k) for k in range(fiamma(x, 4, 2.5))])        # sotto: il rogo
        colonna([(x, k) for k in range(fiamma(x + 100, 1.5, 1))])          # sopra
    for y in range(S):
        base = 2.5 if y > S // 2 else 1.8                                   # piu' alte in basso
        colonna([(k, y) for k in range(fiamma(y * 0.6 + 50, base, 1.4))])
        colonna([(S - 1 - k, y) for k in range(fiamma(y * 0.6 + 200, base, 1.4))])
    # Sparks going up the sides: one lap of S - 8 pixels per animation loop.
    for i in range(6):
        x0 = 4 + h(str(i), "scintilla") % (S - 8)
        sx = (3 + i % 3) if i % 2 == 0 else (S - 4 - i % 3)
        y = S - 4 - (step * (S - 8) // FRAME_STEPS + x0 * 3) % (S - 8)
        c.px(sx, y, FUOCO[1 if i % 3 else 0])
    return c.img


# --- Cornici premio (trofei dei doni e Ognissanti), scelte in Opzioni per i leggendari ---

def ring(d):
    """Pixels of the ring at depth d (0 = outer edge), clockwise from the top-left."""
    lo, hi = d, S - 1 - d
    top = [(x, lo) for x in range(lo, hi + 1)]
    right = [(hi, y) for y in range(lo + 1, hi + 1)]
    bottom = [(x, hi) for x in range(hi - 1, lo - 1, -1)]
    left = [(lo, y) for y in range(hi - 1, lo, -1)]
    return top + right + bottom + left


def put(c, x, y, col, alpha=255):
    c.img.putpixel((x, y), tuple(col) + (alpha,))


def mix(c1, c2, t):
    return tuple(round(p + (q - p) * t) for p, q in zip(c1, c2))


# --- Alloro: laurel sprigs along a thin stem, gold berries, a glint on the stem --
LEAF_D, LEAF, LEAF_L = (36, 84, 40), (72, 142, 60), (150, 206, 108)
STEM = (104, 96, 44)
BERRY, BERRY_L = (214, 160, 40), (252, 228, 132)
# One leaf, in (along the stem, away from it): base dark, then mid, tip light.
LEAF_PX = ((0, 1, LEAF_D), (1, 1, LEAF_D), (2, 1, LEAF), (1, 2, LEAF), (2, 2, LEAF), (3, 2, LEAF_L))
LEAF_STEP = 6                                            # one leaf out, then one in, every 6 px


def alloro(step=0):
    """Laurel wreath: on each side a stem at depth 2 with staggered leaves on both sides,
    pointing clockwise, and transparent gaps between them so they read as leaves."""
    c = Canvas()
    # Sides as (start, along, outward normal); the stem runs at depth 2.
    sides = (((2, 2), (1, 0), (0, -1)), ((S - 3, 2), (0, 1), (1, 0)),
             ((S - 3, S - 3), (-1, 0), (0, 1)), ((2, S - 3), (0, -1), (-1, 0)))
    length = S - 5
    for (ox, oy), (ux, uy), (nx, ny) in sides:
        for t in range(length):
            put(c, ox + ux * t, oy + uy * t, STEM)
        for t in range(2, length - 4):
            side = 1 if t % LEAF_STEP == 0 else (-1 if t % LEAF_STEP == LEAF_STEP // 2 else 0)
            if not side:
                continue
            for da, db, col in LEAF_PX:
                x = ox + ux * (t + da) + nx * db * side
                y = oy + uy * (t + da) + ny * db * side
                if 0 <= x < S and 0 <= y < S:
                    put(c, x, y, col)
    # Berries: a gold pair at each corner and in the middle of each side, pulsing in turn.
    spots = [(2, 2), (S - 3, 2), (S - 3, S - 3), (2, S - 3),
             (S // 2, 1), (S - 2, S // 2), (S // 2, S - 2), (1, S // 2)]
    for k, (x, y) in enumerate(spots):
        lit = (step + k * 3) % 6 < 2
        put(c, x, y, BERRY_L if lit else BERRY)
        put(c, x + (1 if x < S // 2 else -1), y, BERRY)
    stem = [(x, y) for (x, y) in ring(2)]                # glint running along the stem
    n = len(stem)
    for j, col in enumerate(((200, 190, 110), (250, 240, 190), (200, 190, 110))):
        x, y = stem[(step * n // FRAME_STEPS + j) % n]
        if c.img.getpixel((x, y))[:3] == STEM:
            put(c, x, y, col)
    return c.img


# --- Vetrata: stained glass segments, lead lines, light sweeping round ----------
GLASS = [(40, 80, 170), (170, 40, 50), (220, 170, 40), (50, 130, 70), (110, 50, 140)]
LEAD = (30, 26, 34)


def vetrata(step=0):
    c = Canvas()
    n = len(ring(0))
    for x, y in ring(0): put(c, x, y, LEAD)              # lead outline outside and inside
    for x, y in ring(3): put(c, x, y, LEAD)
    for d in (1, 2):
        r = ring(d)
        m = len(r)
        for i, (x, y) in enumerate(r):
            pos = i * n / m                              # same angle on every ring
            if pos % 6 < n / m:                          # lead between panes
                put(c, x, y, LEAD)
                continue
            base = GLASS[int(pos // 6) % len(GLASS)]
            wave = 0.5 + 0.5 * math.cos(2 * math.pi * (pos / n - step / FRAME_STEPS))
            put(c, x, y, mix(base, (255, 250, 230), 0.6 * wave ** 4) if d == 1 else
                mix(base, (0, 0, 0), 0.15))
    return c.img


# --- Gemme: gold frame studded with coloured gems twinkling ---------------------
GEMS = [GEM_RED, GEM_BLUE,
        [(20, 90, 40), (30, 140, 70), (80, 200, 120), (180, 255, 200)],
        [(70, 30, 100), (120, 50, 160), (170, 100, 220), (225, 190, 255)]]


def gemme(step=0):
    c = Canvas()
    for x, y in ring(0): put(c, x, y, GOLD_DARK)
    for x, y in ring(1): put(c, x, y, GOLD)
    for x, y in ring(2): put(c, x, y, GOLD_LIGHT)
    r = ring(1)
    n = len(r)
    for k in range(16):
        x, y = r[k * n // 16]
        pal = GEMS[k % 4]
        lvl = (step + k * 5) % 6
        lvl = lvl if lvl < 4 else 6 - lvl
        for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            if 0 <= x + dx < S and 0 <= y + dy < S and (dx, dy) != (0, 0):
                put(c, x + dx, y + dy, pal[0])
        put(c, x, y, pal[lvl])
        if lvl == 3:
            put(c, x, y, (255, 255, 255))
    return c.img


# --- Ognissanti: double gold frame, rays from corners and sides, sparkles -------
def ognissanti(step=0):
    c = Canvas()
    for x, y in ring(0): put(c, x, y, GOLD_DARK)
    for x, y in ring(1): put(c, x, y, GOLD_LIGHT)
    for x, y in ring(2): put(c, x, y, GOLD)
    for x, y in ring(3): put(c, x, y, (255, 236, 160), 150)   # soft glow, see-through
    # Rays: beams from the corners and the middle of each side, lighting up in turn.
    beams = []
    for (cx, cy, dx, dy) in ((2, 2, 1, 1), (S - 3, 2, -1, 1), (S - 3, S - 3, -1, -1), (2, S - 3, 1, -1)):
        beams.append([(cx + dx * i, cy + dy * i) for i in range(1, 8)])
    for (cx, cy, dx, dy) in ((S // 2, 2, 0, 1), (S - 3, S // 2, -1, 0), (S // 2, S - 3, 0, -1), (2, S // 2, 1, 0)):
        beams.append([(cx + dx * i, cy + dy * i) for i in range(1, 5)])
    for k, beam in enumerate(beams):
        bright = 0.5 + 0.5 * math.cos(2 * math.pi * (step / FRAME_STEPS - k / len(beams)))
        for i, (x, y) in enumerate(beam):
            fade = 1 - i / (len(beam) + 1)
            col = mix(GOLD_LIGHT, (255, 255, 255), bright)
            put(c, x, y, col, round(255 * min(1, fade * (0.6 + 0.6 * bright))))
            if i < 2 and (x + 1) < S - 3:                # a 2 px wide base
                put(c, x + 1 if beam[0][0] < S // 2 else x - 1, y, col, round(200 * fade))
    r = ring(1)                                          # two white sparkles chasing round
    n = len(r)
    for off in (0, n // 2):
        for j, col in enumerate(((255, 250, 220), (255, 255, 255), (255, 250, 220))):
            x, y = r[(step * n // FRAME_STEPS + off + j) % n]
            put(c, x, y, col)
    return c.img


# Cornici premio: nome (= prefisso dei file e valore in Opzioni) -> funzione. "cornice" e' l'oro.
# --- Canonica: a wooden parish frame, iron nails in the corners, two candles flickering --
CANDELA, CANDELA_OMBRA = (246, 242, 232), (214, 208, 196)
FIAMMA = [(255, 200, 70), (255, 150, 50), (255, 230, 120)]


def canonica(step=0):
    """Wooden frame with grain on the middle ring, nailed corner blocks, and two candles on
    gold holders along the bottom edge whose flames flicker."""
    c = Canvas()
    for d, col in ((0, WOOD_DARK), (1, WOOD), (2, (176, 124, 76))):
        c.d.rectangle((d, d, S - 1 - d, S - 1 - d), outline=col + (255,))
    for j, (x, y) in enumerate(ring(1)):
        if j % 9 < 2:
            put(c, x, y, WOOD_DARK)
    for (x, y) in CORNERS:
        c.rect((x, y, x + 4, y + 4), WOOD)
        c.d.rectangle((x, y, x + 4, y + 4), outline=WOOD_DARK + (255,))
        c.px(x + 2, y + 2, STEEL_LIGHT)
    for x in (6, S - 8):
        c.rect((x - 1, S - 5, x + 2, S - 4), GOLD)
        c.rect((x, S - 11, x + 1, S - 6), CANDELA)
        c.px(x + 1, S - 11, CANDELA_OMBRA)
        flame = FIAMMA[(step + x) % 3]
        c.px(x, S - 12, flame); c.px(x + 1, S - 12, flame)
        c.px(x + (step // 2) % 2, S - 13, (255, 250, 220))
    return c.img


CORNICI_PREMIO = {"alloro": alloro, "vetrata": vetrata, "gemme": gemme, "ognissanti": ognissanti,
                  "canonica": canonica}


# Cornici speciali per alcuni leggendari (al posto di quella d'oro): santo -> (nome, funzione).
# L'app trova il nome in cornici.txt e carica <nome>_00..11.png.
CORNICI = {
    "Santa Giovanna d'Arco": ("fuoco", cornice_fuoco),
}


def cornice_di(name):
    """The frame function of a legendary saint: gold, or the special one in CORNICI."""
    return CORNICI.get(name, ("cornice", cornice))[1]


def gif_leggendario(name, t, path, zoom=6, ms=FRAME_MS):
    """Animated preview: still avatar with its animated frame (gold, or from CORNICI) on top."""
    base = render(name, t)
    frames = []
    for step in range(FRAME_STEPS):
        f = base.copy()
        f.alpha_composite(cornice_di(name)(step))
        frames.append(f.convert("RGB").resize((S * zoom, S * zoom), Image.NEAREST))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0)


SILVER, SILVER_DARK, SILVER_LIGHT = (196, 202, 212), (120, 126, 140), (238, 242, 248)


def _cornice_semplice(dark, light, base, gem, step=None, grana=None):
    """Frame like the gold one: 2 px border (dark outside, light inside), 5x5 corners with a
    gem in the middle, transparent inside. [grana] recolours 2 light pixels every 7 (wood
    grain). With [step], one frame of the animation (gems and glint as on the gold one)."""
    c = Canvas()
    c.d.rectangle((0, 0, S - 1, S - 1), outline=dark + (255,))
    c.d.rectangle((1, 1, S - 2, S - 2), outline=light + (255,))
    if grana:
        for j, (x, y) in enumerate(_perimeter(1)):
            if j % 7 < 2:
                c.px(x, y, grana)
    gems = [shade(gem, 0.6), gem, _schiarisci(gem, 0.4), _schiarisci(gem, 0.75)]
    for i, (x, y) in enumerate(CORNERS):
        c.rect((x, y, x + 4, y + 4), base)
        c.d.rectangle((x, y, x + 4, y + 4), outline=dark + (255,))
        _gemma(c, x + 2, y + 2, gems, step, i)
    glint = _schiarisci(light, 0.3)
    _luccichio(c, step, (dark, light), (glint, _schiarisci(light, 0.7), glint))
    return c.img


def cornice_argento():
    """Still silver frame for the special (off-catalogue) cards."""
    return _cornice_semplice(SILVER_DARK, SILVER_LIGHT, SILVER, (90, 170, 230))


def cornice_bronzo(step=None):
    return _cornice_semplice((120, 70, 30), (236, 170, 100), (190, 120, 56), (60, 170, 110), step)


def cornice_smeraldo(step=None):
    return _cornice_semplice((20, 80, 50), (110, 200, 130), (40, 140, 80), GOLD, step)


def cornice_porpora(step=None):
    return _cornice_semplice((80, 20, 50), (200, 90, 140), (130, 36, 80), GOLD, step)


def cornice_lapislazzuli(step=None):
    return _cornice_semplice((24, 44, 104), (110, 150, 230), (38, 70, 150), GOLD, step)


def cornice_legno(step=None):
    """Wooden frame: grain on the light side, iron nails in the corners."""
    return _cornice_semplice(WOOD_DARK, (176, 124, 76), WOOD, STEEL_LIGHT, step, grana=WOOD)


def _hsv(f, s, v):
    return tuple(round(k * 255) for k in colorsys.hsv_to_rgb(f % 1, s, v))


def cornice_arcobaleno(step=None):
    """Rainbow frame: the hue goes once around the border and turns with [step]; white
    corners with a coloured gem."""
    giro = (step or 0) / FRAME_STEPS
    c = Canvas()
    for inset, v in ((0, 0.75), (1, 1.0)):
        ring = _perimeter(inset)
        for j, (x, y) in enumerate(ring):
            c.px(x, y, _hsv(j / len(ring) - giro, 0.75, v))
    for i, (x, y) in enumerate(CORNERS):
        c.rect((x + 1, y + 1, x + 3, y + 3), WHITE)
        c.px(x + 2, y + 2, _hsv(i / 4 + 1 / 8 - giro, 0.75, 0.9))
    return c.img


NEON_ROSA, NEON_CIANO = (255, 60, 200), (60, 240, 255)


def cornice_neon(step=None):
    """Neon sign frame: a pink tube with a soft glow on both sides and cyan corner bulbs.
    The tube hums (brightness pulse) and flickers off twice per loop, like a bad starter."""
    step = step or 0
    spento = step in (7, 9)
    c = Canvas()
    c.d.rectangle((0, 0, S - 1, S - 1), outline=(30, 16, 40, 255))      # the dark backing
    tubo = shade(NEON_ROSA, 0.35) if spento else _schiarisci(NEON_ROSA, 0.15 + 0.15 * math.sin(2 * math.pi * step / FRAME_STEPS))
    alone = 0 if spento else 110
    for x, y in _perimeter(2):
        c.img.putpixel((x, y), NEON_ROSA + (alone,))                        # glow inside
    for x, y in _perimeter(1):
        c.px(x, y, tubo)
    for i, (x, y) in enumerate(CORNERS):
        acceso = not spento or i % 2
        bulbo = _schiarisci(NEON_CIANO, 0.5) if acceso else shade(NEON_CIANO, 0.4)
        c.rect((x + 1, y + 1, x + 3, y + 3), (30, 16, 40))
        c.px(x + 2, y + 2, bulbo)
        if acceso:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                c.px(x + 2 + dx, y + 2 + dy, NEON_CIANO)
    return c.img


VAPOR = [(255, 113, 206), (185, 103, 255), (1, 205, 254), (5, 255, 161)]


def cornice_vaporwave(step=None):
    """Vaporwave frame: pastel pink, violet, cyan and mint flowing down the border, with a
    striped sunset in each corner whose stripes scroll down."""
    step = step or 0

    def tinta(f):
        """Colour at [f] (0..1, looping) along the VAPOR gradient."""
        f = (f % 1) * len(VAPOR)
        a, b = VAPOR[int(f)], VAPOR[(int(f) + 1) % len(VAPOR)]
        k = f - int(f)
        return tuple(round(a[n] + (b[n] - a[n]) * k) for n in range(3))

    c = Canvas()
    for inset, chiaro in ((0, 0.0), (1, 0.35)):
        for x, y in _perimeter(inset):
            c.px(x, y, _schiarisci(tinta(y / S - step / FRAME_STEPS), chiaro))
    sole = [(255, 230, 110), (255, 160, 90), (255, 90, 150), (150, 70, 200)]
    for (x, y) in CORNERS:
        for dy in range(5):
            c.line([(x, y + dy), (x + 4, y + dy)], sole[(dy - step) % len(sole)])
        c.d.rectangle((x, y, x + 4, y + 4), outline=(60, 30, 90, 255))
    return c.img


PALMA_ROSSO, PALMA_ROSSO_SCURO = (204, 46, 40), (104, 16, 22)


def cornice_palma(step=None):
    """Martyr's palm frame: liturgical red border, a green palm frond in each corner whose
    leaflets sway between two poses, and a glint running round the plain border."""
    step = step or 0
    c = Canvas()
    c.d.rectangle((0, 0, S - 1, S - 1), outline=PALMA_ROSSO_SCURO + (255,))
    c.d.rectangle((1, 1, S - 2, S - 2), outline=PALMA_ROSSO + (255,))
    swing = step % 6 >= 3                                   # two poses, twice per loop
    for flip_x, flip_y in ((False, False), (True, False), (True, True), (False, True)):
        def put_px(x, y, col):
            c.px(S - 1 - x if flip_x else x, S - 1 - y if flip_y else y, col)
        for k in range(1, 9):                               # the rib, from the corner inwards
            put_px(k, k, LEAF_D)
        for k in (2, 4, 6):                                 # leaflet pairs, shorter towards the tip
            n = 4 - k // 2
            for j in range(1, n + 1):
                col = LEAF_L if j == n else LEAF
                d = 1 if swing and j == n else 0            # the tips droop towards the frond's tip
                put_px(k + j, k + d, col)
                put_px(k + d, k + j, col)
    _luccichio(c, step, (PALMA_ROSSO_SCURO, PALMA_ROSSO),
               (_schiarisci(PALMA_ROSSO, 0.3), _schiarisci(PALMA_ROSSO, 0.7), _schiarisci(PALMA_ROSSO, 0.3)))
    return c.img


# Cornici dell'opzione "Colorful" dell'app: nome -> funzione (file <nome>_00..11.png).
# I leggendari tengono la loro cornice; ai martiri va la palma, agli altri una delle COLORATE
# (non l'argento, che resta il segno delle figurine speciali).
COLORATE = {"bronzo": cornice_bronzo, "legno": cornice_legno,
            "arcobaleno": cornice_arcobaleno, "smeraldo": cornice_smeraldo,
            "porpora": cornice_porpora, "lapislazzuli": cornice_lapislazzuli,
            "neon": cornice_neon, "vaporwave": cornice_vaporwave}


def cornice_colorata(name, t, leggendario):
    """Colorful frame name of [name]: none (None) for legendary saints, martyrs too, which
    keep theirs (gold, or CORNICI); "palma" for the other martyrs; otherwise one of
    COLORATE, random but fixed (it depends only on the name)."""
    if leggendario:
        return None
    if t.martire:
        return "palma"
    return list(COLORATE)[h(name, "cornice") % len(COLORATE)]


def _gira_base():
    """"Flip the card" icon: a gold ribbon ring seen in perspective, like a bracelet; on the front
    the arrow points right, on the back (its darker inner face) it comes back left. Drawn 4x
    bigger and scaled down without smoothing, dark gold edges."""
    k, n = 4, S * 4
    big = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy, rx, ry, h = n // 2, 78, 80, 26, 30
    back = shade(GOLD, 0.72)

    def pt(t, dy=0):
        r = math.radians(t)
        return (cx + rx * math.cos(r), cy + ry * math.sin(r) + dy)

    def band(t0, t1, height, col):
        step = 1 if t1 > t0 else -1
        ts = list(range(t0, t1 + step, step))
        d.polygon([pt(t) for t in ts] + [pt(t, height) for t in reversed(ts)],
                  fill=col + (255,), outline=GOLD_DARK + (255,), width=k)

    def head(t, height, col, pointing):
        x, y = pt(t)
        mid, half = y + height / 2, height / 2 + 4 * k
        d.polygon([(x + pointing * height * 1.15, mid), (x, mid - half), (x, mid + half)],
                  fill=col + (255,), outline=GOLD_DARK + (255,), width=k)

    hb = h * 0.55                                  # the back is seen from inside, narrower
    band(355, 262, hb, back); head(262, hb, back, -1)
    band(228, 185, hb, back)
    band(178, 72, h, GOLD); head(72, h, GOLD, +1)
    band(38, 2, h, GOLD)
    return big.resize((S, S), Image.NEAREST)


# Gothic (textura) lowercase for the pixel-art labels, 7 px x-height: thin and bold strokes.
# Rows past the 7th hang below the baseline (g); GLIFO_SU lifts a glyph above the x-height (i).
GOTICA_SOTTILE = {
    "u": ["X...X", "X...X", "X...X", "X...X", "X...X", "X..XX", ".XX.X"],
    "o": [".XXX.", "XX..X", "X...X", "X...X", "X...X", "X..XX", ".XXX."],
    "v": ["X...X", "X...X", "X...X", "X...X", ".X.X.", ".X.X.", "..X.."],
    "a": [".XXX.", "X...X", "...XX", ".XX.X", "X...X", "X..XX", ".XX.X"],
    "!": ["X", "X", "X", "X", "X", ".", "X"],
}
GOTICA_PIENA = {
    "u": ["XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX.XXX", ".XX.XX"],
    "o": [".XXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    "v": ["XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX.", ".XXXX.", "..XX.."],
    "a": [".XXXX.", "....XX", ".XXXXX", "XX..XX", "XX..XX", "XX.XXX", ".XX.XX"],
    "n": ["XXXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX"],
    "g": [".XXXXX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX.XXX", ".XX.XX",
          "....XX", "X...XX", ".XXXX."],
    "i": ["XX", "..", "XX", "XX", "XX", "XX", "XX", "XX", "XX"],
    "p": ["XXXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XXXXX.",
          "XX....", "XX....", "XX...."],
    "z": ["XXXXXX", "....XX", "...XX.", "..XX..", ".XX...", "XX....", "XXXXXX"],
    "f": ["..XXX", ".XX..", ".XX..", "XXXX.", ".XX..", ".XX..", ".XX..", ".XX..", ".XX..", ".XX.."],
    "!": ["XX", "XX", "XX", "XX", "XX", "..", "XX"],
}
GLIFO_SU = {"i": 2, "f": 3}
# Rubricated initials, 13 px tall: thick left stem, three-pixel diagonals.
CAPOLETTERA_N = [
    "XXXX....XXX",
    ".XXXX....X.",
    ".XXXXX...X.",
    ".XX.XXX..X.",
    ".XX..XXX.X.",
    ".XX...XXXX.",
    ".XX....XXX.",
    ".XX.....XX.",
    ".XX......X.",
    ".XX......X.",
    ".XX......X.",
    ".XX......X.",
    "XXXX.....X.",
]
CAPOLETTERA_M = [
    "XXX.......XXX",
    ".XXX.....XXX.",
    ".XXXX...XXXX.",
    ".XX.XX.XX.XX.",
    ".XX..XXX..XX.",
    ".XX...X...XX.",
    ".XX.......XX.",
    ".XX.......XX.",
    ".XX.......XX.",
    ".XX.......XX.",
    ".XX.......XX.",
    ".XX.......XX.",
    "XXXX.....XXXX",
]
CAPOLETTERA_O = [
    "...XXXXX...",
    ".XXX...XXX.",
    "XXX.....XXX",
    "XX.......XX",
    "XX.......XX",
    "XX.......XX",
    "XX.......XX",
    "XX.......XX",
    "XX.......XX",
    "XX.......XX",
    "XXX.....XXX",
    ".XXX...XXX.",
    "...XXXXX...",
]
CAPOLETTERA_I = [
    "XXXXXX",
    ".XXXX.",
    "..XX..",
    "..XX..",
    "..XX..",
    "..XX..",
    "..XX..",
    "..XX..",
    "..XX..",
    "..XX..",
    "..XX..",
    ".XXXX.",
    "XXXXXX",
]
PERGAMENA, PERGAMENA_OMBRA = (244, 232, 200), (214, 196, 156)
INCHIOSTRO = (40, 30, 34)


def _glifo(c, rows, x0, y0, col):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "X":
                c.px(x0 + dx, y0 + dy, col)


def etichetta(capolettera, parola, variante="piena", premuto=False):
    """A codex-style label: rubricated initial, then gothic lowercase on the same baseline.

    variante: "piena" (bold textura on parchment), "sottile" (thin strokes on parchment),
    "nastro" (parchment letters on a red ribbon, gold initial), "nudo" (gold initial and
    white letters with no background, outlined, e.g. on the red splash). [premuto] darkens the
    background and drops the content by 1 px (pressed button).
    """
    font = GOTICA_SOTTILE if variante == "sottile" else GOTICA_PIENA
    cap_w, cap_h = len(capolettera[0]), len(capolettera)
    word_w = sum(len(font[ch][0]) for ch in parola) + len(parola) - 1
    giu = max(len(font[ch]) - GLIFO_SU.get(ch, 0) - 7 for ch in parola)   # discendenti
    # 1 px transparent margin all round, so outline() draws the label's dark border.
    w, h = 1 + 3 + cap_w + 2 + word_w + 3 + 1, 1 + 2 + cap_h + giu + 2 + 1
    c = Canvas(w, h)
    nudo = variante == "nudo"                                # just the letters (e.g. on the red splash)
    nastro = variante == "nastro" or nudo
    fondo, ombra = (RED, DARK_RED) if nastro else (PERGAMENA, PERGAMENA_OMBRA)
    if premuto:
        fondo = shade(fondo, 0.7)
    if not nudo:
        c.rect((1, 1, w - 2, h - 2), fondo)
        c.rect((1, h - 3, w - 2, h - 2), ombra)             # bordo inferiore in ombra
        if not premuto:
            c.line([(2, 1), (w - 3, 1)], shade(fondo, 1.08))  # luce sul bordo superiore
        for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
            c.img.putpixel((x, y), (0, 0, 0, 0))            # angoli smussati
    dy = 1 if premuto else 0
    cx, cy = 4, 3 + dy
    # Initial: red with a lighter left edge (gold on the ribbon).
    _glifo(c, capolettera, cx, cy, GOLD if nastro else RED)
    luce = GOLD_LIGHT if nastro else shade(RED, 1.35)
    for r in range(1, cap_h - 1):                           # luce sul primo pixel di ogni riga
        x0 = capolettera[r].find("X")
        if x0 >= 0:
            c.px(cx + x0, cy + r, luce)
    if nudo:                                                # the splash title: the gold capital in relief (rich style)
        _capolettera_ricca(c.img, capolettera, cx, cy, ORO6)
    # Gothic lowercase, sitting on the baseline of the initial.
    ink = (250, 246, 236) if nudo else PERGAMENA if nastro else INCHIOSTRO
    base = cy + cap_h
    x = cx + cap_w + 2
    for ch in parola:
        _glifo(c, font[ch], x, base - 7 - GLIFO_SU.get(ch, 0), ink)
        x += len(font[ch][0]) + 1
    return outline(c.img)


PULSANTI = {
    "mannaggia": (CAPOLETTERA_M, "annaggia!"),
    "opzioni": (CAPOLETTERA_O, "pzioni"),
    "info": (CAPOLETTERA_I, "nfo"),
}


# Favourites bookmark: a swallow-tailed banner hanging from a gold rod (palette: cloth, border).
STENDARDI = {
    "lapislazzuli": ((38, 70, 150), GOLD),          # blue and gold of illuminated codices
    "porpora": ((120, 30, 70), GOLD),
    "smeraldo": ((30, 110, 70), SILVER),
}
SEGNALIBRO_W, SEGNALIBRO_H = 14, 22


def _segnalibro_base(attivo=True, colori="lapislazzuli"):
    """Bookmark of the favourite cards: full banner when [attivo], a faint outline otherwise."""
    drappo, bordo = STENDARDI[colori]
    w, h = SEGNALIBRO_W, SEGNALIBRO_H
    c = Canvas(w, h)
    # Gold rod with knobs.
    c.line([(1, 1), (w - 2, 1)], GOLD_DARK); c.line([(1, 2), (w - 2, 2)], GOLD)
    c.px(0, 1, GOLD_LIGHT); c.px(w - 1, 1, GOLD_LIGHT)
    # Cloth with a swallow tail: the notch goes up 5 px in the middle.
    cloth = [(2, 3), (w - 3, 3), (w - 3, h - 2), (w // 2, h - 8), (2, h - 2)]
    if attivo:
        c.poly(cloth, bordo)
        c.poly([(3, 3), (w - 4, 3), (w - 4, h - 4), (w // 2, h - 10), (3, h - 4)], drappo)
        c.line([(4, 4), (4, h - 6)], shade(drappo, 1.25))               # light on the left fold
        mx = w // 2                                                         # small cross
        c.line([(mx, 6), (mx, 11)], bordo); c.line([(mx - 2, 8), (mx + 1, 8)], bordo)
        return outline(c.img)
    c.d.polygon(cloth, fill=drappo + (50,), outline=bordo + (200,))
    return c.img


# The "#@!*" of the app icon, 7 px tall, for the pixel-art logo.
GRAWLIX = {
    "#": [".X..X.", "XXXXXX", ".X..X.", ".X..X.", "XXXXXX", ".X..X.", ".X..X."],
    "@": [".XXXX.", "X....X", "X.XX.X", "X.XX.X", "X.XXXX", "X.....", ".XXXX."],
    "!": ["XX", "XX", "XX", "XX", "XX", "..", "XX"],
    "*": ["..X..", "X.X.X", ".XXX.", "XXXXX", ".XXX.", "X.X.X", "..X.."],
}
LOGO_RED = (139, 0, 0)          # #8B0000, the red of the icon and of the store graphic


# --- Rich style for the logo, the labels and the main-screen icons (the user, 2026-11-19) -------------
# Six tones per material, light from the top left, as in the 96 px portraits (tools/ritratti96): each
# part is a set of pixels toned by _bevel() (lit top and left edges, dark bottom and right) or by its
# own tone function. The icons have a dark-gold outline instead of the dark one, so they read on the
# dark theme too.

def _hex(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


ORO6 = [_hex(c) for c in ("#7a4a14", "#a86c1c", "#d09a2c", "#eac050", "#fbe08a", "#fff6cc")]
ROSSO6 = [_hex(c) for c in ("#3a0a10", "#5c1018", "#82161e", "#a82028", "#c83a38", "#e26a58")]
PERG6 = [_hex(c) for c in ("#8a6a48", "#b4946a", "#d4bc8e", "#e8d8b0", "#f4e8c8", "#fdf6e2")]
CARTA6 = [_hex(c) for c in ("#8a8278", "#b0a89c", "#d0c8ba", "#e6e0d4", "#f4f0e6", "#fffdf6")]
CREMA6 = [_hex(c) for c in ("#7e6e60", "#a8988a", "#cdbfae", "#e6dccc", "#f6f0e4", "#fffcf6")]
CUOIO6 = [_hex(c) for c in ("#3a0e10", "#5a161a", "#7e2226", "#9a2e30", "#b84a46", "#d4706a")]
LEGNO6 = [_hex(c) for c in ("#3a2210", "#56341a", "#764a26", "#946034", "#b07a48", "#c89a68")]
ACCIAIO6 = [_hex(c) for c in ("#2a2a32", "#4a4a56", "#6a6e7c", "#9096a4", "#bcc2ce", "#eef0f6")]
LAPIS6 = [_hex(c) for c in ("#101a40", "#18285e", "#22387e", "#2e4a9a", "#4a68b8", "#7a94d4")]
ROSSO_LOGO6 = [_hex(c) for c in ("#2e0406", "#520a0c", "#780e10", "#8b0000", "#b42a20", "#dc5a3c")]
INCARNATO4 = [_hex(c) for c in ("#8a5040", "#b06a54", "#d08c6c", "#e8ac88")]
ORO_SCURO = _hex("#6a4012")          # the icons' outline (the user: the dark one disappears on the dark theme)
ORO_STELLA = _hex("#9a6620")         # the calendar star's edge on the white page


def _t(R, t):
    return R[max(0, min(len(R) - 1, round(t)))]


def _put(img, pix):
    for (x, y), c in pix.items():
        if 0 <= x < img.width and 0 <= y < img.height:
            img.putpixel((x, y), c + (255,))


def _bevel(mask, R, base=3.0, grad=None, lit=1.0, dark=1.0):
    """Tones for a set of pixels: the edges facing the light lighter, the others darker, plus grad(x, y)."""
    out = {}
    for (x, y) in mask:
        t = base + (grad(x, y) if grad else 0)
        if (x, y - 1) not in mask:
            t += lit * (1.3 if (x - 1, y) not in mask else 1)
        elif (x - 1, y) not in mask:
            t += lit * 0.7
        if (x, y + 1) not in mask:
            t -= dark * 1.4
        elif (x + 1, y) not in mask:
            t -= dark * 0.8
        out[(x, y)] = _t(R, t)
    return out


def _maschera_glifo(g, x0, y0):
    return {(x0 + k, y0 + r) for r, row in enumerate(g) for k, ch in enumerate(row) if ch == "X"}


def _ellisse(cx, cy, rx, ry, w=S, h=S):
    return {(x, y) for y in range(h) for x in range(w) if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1}


def _ricolora(img, mats):
    """Re-tones a drawing: mats maps one of its colours to (ramp, base, grad); the others stay."""
    px, (w, h) = img.load(), img.size
    gruppi = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c[3] and c[:3] in mats:
                gruppi.setdefault(c[:3], set()).add((x, y))
    out = img.copy()
    for col, mask in gruppi.items():
        R, base, grad = mats[col]
        _put(out, _bevel(mask, R, base=base, grad=grad))
    return out


def _capolettera_ricca(img, cap, x0, y0, R):
    """A capital in relief from ramp R, with a diagonal sheen across the strokes."""
    _put(img, _bevel(_maschera_glifo(cap, x0, y0), R, grad=lambda x, y: 1 if (x + y) % 7 == 0 else 0))


def logo():
    """The app icon, 64 px: a white speech bubble saying "#@!*" in red relief under a gold halo."""
    w, h = 64, 62
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    q = lambda x, y, cx, cy, rx, ry: ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
    # The halo: a gold ring seen from slightly above, the hole open.
    HX, HY = 32, 7.5
    anello = {(x, y) for y in range(h) for x in range(w) if q(x, y, HX, HY, 15.5, 6) <= 1 and q(x, y, HX, HY, 10.5, 3) > 1}

    def tono_anello(x, y):
        nx, ny = (x + 0.5 - HX) / 15.5, (y + 0.5 - HY) / 6
        t = 3.4 - nx * 1.2 if ny > 0 else 2 - nx * 0.8                     # the near side lit, the far one seen from inside
        if q(x, y, HX, HY, 15.5, 6) > 0.72:
            t -= 1.3 if ny > 0 else 0.5                                     # the outer rim turns away
        if ny > 0 and q(x, y, HX, HY, 11.6, 3.8) <= 1:
            t += 1.2                                                        # the inner lip catches the light
        if ny > 0.2 and -0.6 < nx < -0.2 and q(x, y, HX, HY, 13.4, 5) <= 1 and q(x, y, HX, HY, 12.4, 4.3) > 1:
            t = 5                                                           # the glint
        if ny > 0.3 and abs(nx) < 0.75 and x % 3 == 0 and q(x, y, HX, HY, 14.4, 5.4) <= 1 and q(x, y, HX, HY, 12.9, 4.5) > 1:
            t -= 2                                                          # the punched dots
        return _t(ORO6, t)
    # The bubble: a rounded box with the tail down on the left.
    X0, X1, Y0, Y1, R = 2, 61, 16, 47, 8

    def in_box(x, y):
        if not (X0 <= x <= X1 and Y0 <= y <= Y1):
            return False
        ax = X0 + R - x if x < X0 + R else x - (X1 - R) if x > X1 - R else 0
        ay = Y0 + R - y if y < Y0 + R else y - (Y1 - R) if y > Y1 - R else 0
        return ax * ax + ay * ay <= (R + 0.3) ** 2

    def in_coda(x, y):
        if not (Y1 - 3 < y <= 59):
            return False
        u = (y - (Y1 - 3)) / (59 - (Y1 - 3))
        return 12 - 6 * u <= x <= 24 - 18 * u ** 0.8
    nuvola = {(x, y) for y in range(h) for x in range(w) if in_box(x, y) or in_coda(x, y)}

    def tono_nuvola(x, y):
        t = 4 if q(x, y, 27, 27, 33, 17.5) <= 1 else 3                      # the lit body, the underside turning away
        if (x - 1, y) not in nuvola or (x, y - 1) not in nuvola:
            t += 1
        if (x + 1, y) not in nuvola or (x, y + 1) not in nuvola:
            t -= 1.4
        elif (x + 2, y) not in nuvola or (x, y + 2) not in nuvola:
            t -= 0.7
        if in_coda(x, y) and not in_box(x, y):
            t -= 0.6
        return _t(CREMA6, t)
    # "#@!*" in red relief: the glyphs at 2x.
    testo, word, gap = set(), "#@!*", 3
    x0 = (w - (sum(len(GRAWLIX[ch][0]) * 2 for ch in word) + gap * (len(word) - 1))) // 2
    for ch in word:
        for r, row in enumerate(GRAWLIX[ch]):
            for k, v in enumerate(row):
                if v == "X":
                    testo |= {(x0 + k * 2 + a, 25 + r * 2 + b) for a in (0, 1) for b in (0, 1)}
        x0 += len(GRAWLIX[ch][0]) * 2 + gap

    def tono_testo(x, y):
        t = 3
        if (x, y - 1) not in testo:
            t += 1.6
        elif (x - 1, y) not in testo:
            t += 0.8
        if (x, y + 1) not in testo:
            t -= 1.6
        elif (x + 1, y) not in testo:
            t -= 0.8
        return _t(ROSSO_LOGO6, t)
    _put(img, {(x, y): tono_testo(x, y) if (x, y) in testo else _t(CREMA6, 2.4) if (x - 1, y - 1) in testo else tono_nuvola(x, y)
               for (x, y) in nuvola})
    _put(img, {p: tono_anello(*p) for p in anello})
    # 1 px of transparent margin all round for the outline.
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    out.paste(img, (1, 1))
    return outline(out)


def _misure(cap, parola):
    word_w = sum(len(GOTICA_PIENA[ch][0]) for ch in parola) + len(parola) - 1
    giu = max(len(GOTICA_PIENA[ch]) - GLIFO_SU.get(ch, 0) - 7 for ch in parola)
    return 1 + 3 + len(cap[0]) + 2 + word_w + 3 + 1, 1 + 2 + len(cap) + giu + 2 + 1


def _scritta(img, cap, parola, x0, y0, cap_R, ink, ombra):
    """The capital in relief, the gothic lowercase in [ink] with a 1 px [ombra] under it."""
    _capolettera_ricca(img, cap, x0, y0, cap_R)
    base, x, lettere = y0 + len(cap), x0 + len(cap[0]) + 2, set()
    for ch in parola:
        lettere |= _maschera_glifo(GOTICA_PIENA[ch], x, base - 7 - GLIFO_SU.get(ch, 0))
        x += len(GOTICA_PIENA[ch][0]) + 1
    _put(img, {(a + 1, b + 1): ombra for (a, b) in lettere if (a + 1, b + 1) not in lettere})
    _put(img, {p: ink for p in lettere})


def pulsante(premuto=False, nome="mannaggia"):
    """Main-screen buttons ("Mannaggia!", "Opzioni", "Info"): a red ribbon of six tones with a gold
    edge, the gold capital in relief, parchment letters. Pressed: darker, the content 1 px down."""
    cap, parola = PULSANTI[nome]
    w, h = _misure(cap, parola)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    giu = -1 if premuto else 0
    corpo = {(x, y) for y in range(1, h - 1) for x in range(1, w - 1)} - {(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)}
    _put(img, _bevel(corpo, ROSSO6, base=3 + giu, grad=lambda x, y: (-0.7 if y >= h * 0.62 else 0) + (0.6 if y == 2 else 0)))
    bordo = {(x, y) for (x, y) in corpo if any(p not in corpo for p in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))}
    _put(img, {(x, y): _t(ORO6, (4.4 if y == 1 or x == 1 else 1.6) + giu) for (x, y) in bordo})
    _scritta(img, cap, parola, 4, 3 + (1 if premuto else 0), ORO6, PERGAMENA, ROSSO6[0])
    return outline(img)


def timbro():
    """"Nuova!" stamp for new cards: worn parchment, the N in red relief, dark ink."""
    cap, parola = CAPOLETTERA_N, "uova!"
    w, h = _misure(cap, parola)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    carta = {(x, y) for y in range(1, h - 1) for x in range(1, w - 1)} - {(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2), (w - 2, 2), (2, h - 2)}
    grana = lambda x, y: (-0.8 if y >= h - 3 else 0) + (-0.6 if (x * 7 + y * 13) % 17 == 0 and y > 2 else 0)   # the bottom in shade, worn specks
    _put(img, _bevel(carta, PERG6, base=3.6, grad=grana, lit=0.8))
    _scritta(img, cap, parola, 4, 3, ROSSO6, INCHIOSTRO, PERG6[2])
    return outline(img)


def coppa():
    """Trophy cup icon for the main screen: a gold cup shaded like a cylinder, on a wooden plinth."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for cx in (11.5, 36.5):                                                 # the handles, behind the bowl
        _put(img, _bevel(_ellisse(cx, 16, 5.6, 6.6) - _ellisse(cx, 16, 3, 4), ORO6, base=2.6))
    bowl = {(x, y) for y in range(8, 30) for x in range(S) if abs(x + 0.5 - 24) <= 12.5 - max(0, y - 18) ** 1.6 * 0.42}

    def tono_bowl(x, y):
        nx = (x + 0.5 - 24) / 12.5
        t = 5 if -0.62 < nx < -0.38 else 3.1 - nx * 1.8                     # lit left, dark right, a vertical glint
        if (x + 1, y) not in bowl:
            t -= 0.6
        if y >= 26:
            t -= 0.6
        return _t(ORO6, t)
    _put(img, {p: tono_bowl(*p) for p in bowl})
    lip, dentro = _ellisse(24, 8.5, 12.8, 2.8), _ellisse(24, 8.7, 10.6, 1.7)   # the rim from above, the inside in shadow
    _put(img, {(x, y): _t(ORO6, 4.6 - (x - 24) * 0.09) for (x, y) in lip - dentro})
    _put(img, {(x, y): _t(ORO6, 1 if y <= 8 else 0.4) for (x, y) in dentro})
    stelo = {(x, y) for y in range(29, 36) for x in range(22, 26)} | _ellisse(24, 32.5, 3.5, 1.5)
    _put(img, {(x, y): _t(ORO6, 3.2 - (x + 0.5 - 24) * 0.55 + (0.8 if y == 32 else 0)) for (x, y) in stelo})
    piede = {(x, y) for y in range(35, 39) for x in range(S) if abs(x + 0.5 - 24) <= 6 + (y - 35) * 1.6}
    _put(img, _bevel(piede, ORO6, base=3, grad=lambda x, y: -(x + 0.5 - 24) * 0.12))
    _put(img, _bevel({(x, y) for y in range(39, 45) for x in range(12, 36)}, LEGNO6, base=2.6, grad=lambda x, y: -(x + 0.5 - 24) * 0.05))
    _put(img, _bevel({(x, y) for y in range(40, 43) for x in range(19, 29)}, ORO6, base=3.2))
    _put(img, {(23, 16): (255, 250, 220), (22, 17): ORO6[5]})
    return outline(img, ORO_SCURO)


def calendario():
    """Saint-of-the-day icon: a calendar page with a red header, steel rings and a faceted gold star."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    _put(img, {(x, y): _t(CARTA6, 2.2 if y >= 42 else 2.8) for y in range(13, 45) for x in range(9, 41)})   # the pages under
    _put(img, {(x, 42): CARTA6[4] for x in range(10, 40)})
    piega = {(x, y) for y in range(34, 41) for x in range(33, 40) if x + y >= 74}   # the corner folded away
    pagina = {(x, y) for y in range(13, 41) for x in range(8, 40)} - piega
    _put(img, {(x, y): _t(CARTA6, 4 - (0.7 if x >= 38 else 0) - (0.9 if y >= 39 else 0) + (0.6 if x == 8 else 0)) for (x, y) in pagina})
    _put(img, {(x, y): _t(CARTA6, 2.6 + (x - 34) * 0.15) for y in range(35, 41) for x in range(34, 40)
               if 70 <= x + y <= 74 and x - 34 >= 40 - y - 6 and y - 35 >= 39 - x - 5})
    testata = {(x, y) for y in range(8, 17) for x in range(8, 41)}
    _put(img, _bevel(testata, ROSSO6, base=3, grad=lambda x, y: (0.8 if y == 9 else 0) - (0.8 if y >= 15 else 0)))
    for x0 in (13, 32):                                                     # the rings, steel cylinders
        _put(img, {(x, y): _t(ACCIAIO6, (4.6 if x == x0 else 3 if x == x0 + 1 else 1.4) - (0.8 if y == 11 else 0))
                   for y in range(3, 12) for x in range(x0, x0 + 3)})
        _put(img, {(x0 + 1, 12): ROSSO6[0]})
    cx, cy = 24, 28                                                         # the star: two facets per point
    pts = [(cx + (10 if i % 2 == 0 else 4.2) * math.sin(i * math.pi / 5), cy - (10 if i % 2 == 0 else 4.2) * math.cos(i * math.pi / 5))
           for i in range(10)]
    stella = set()
    for y in range(S):
        for x in range(S):
            px, py, dentro = x + 0.5, y + 0.5, False
            for i in range(10):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 10]
                if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
                    dentro = not dentro
            if dentro:
                stella.add((x, y))

    def tono_stella(x, y):
        a = math.atan2(x + 0.5 - cx, -(y + 0.5 - cy)) % (2 * math.pi)
        lato = (a / (math.pi / 5)) % 2                                      # the facet left or right of a point's axis
        return _t(ORO6, 3 + math.cos(a + math.radians(45)) * 1.2 + (0.7 if lato < 1 else -0.7))
    _put(img, {(x + dx, y + dy): ORO_STELLA for (x, y) in stella for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if (x + dx, y + dy) not in stella})                          # its edge, apart from the white
    _put(img, {p: tono_stella(*p) for p in stella})
    _put(img, {(cx, cy): ORO6[5]})
    return outline(img, ORO_SCURO)


def raccoglitore():
    """The card binder icon: a tooled leather cover with gold rings, corners and emblem, a card sticking out."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    _put(img, _bevel({(x, y) for y in range(2, 14) for x in range(20, 38)}, CARTA6, base=3.8, lit=0.6))   # the card, a tiny saint
    _put(img, {p: _t(ORO6, 4 - (p[1] - 5) * 0.6) for p in _ellisse(29, 5.5, 4.2, 1.8) - _ellisse(29, 5.5, 2.6, 0.9)})
    _put(img, {p: INCARNATO4[2 if p[0] < 30 else 1] for p in _ellisse(29, 10, 2.8, 3)})

    def tono_copertina(x, y):
        t = 3 - (0.7 if x >= 37 else 0) - (0.6 if y >= 43 else 0)
        if x <= 13:
            t = 1.8 + (0.8 if x == 9 else 0)                                # the spine
        if x == 14:
            t = 4                                                           # its ridge
        if (x in (17, 39) and 12 <= y <= 42) or (y in (12, 42) and 17 <= x <= 39):
            t -= 1                                                          # the blind-tooled frame
        if (x in (18, 40) and 13 <= y <= 42) or (y in (13, 43) and 18 <= x <= 39):
            t += 0.6
        return _t(CUOIO6, t)
    _put(img, {(x, y): tono_copertina(x, y) for y in range(9, 46) for x in range(8, 43)})
    for (x0, y0) in ((38, 9), (38, 41)):                                    # the gold corners
        _put(img, _bevel({(x, y) for y in range(y0, y0 + 5) for x in range(x0, x0 + 5)
                          if (y0 == 9 and x - x0 >= y - y0) or (y0 == 41 and x - x0 >= (y0 + 4) - y)}, ORO6, base=3.2))
    for y0 in (14, 26, 38):                                                 # the rings
        _put(img, {(x, y): _t(ORO6, (4.6 if y == y0 else 3 if y == y0 + 1 else 1.4) - (x - 8) * 0.15) for y in range(y0, y0 + 3) for x in range(5, 12)})
    _put(img, _bevel({(x, y) for y in range(21, 34) for x in range(20, 36)}, ORO6, base=3, grad=lambda x, y: -(x - 27) * 0.06))
    _put(img, _bevel(_ellisse(28, 27.5, 5, 5) - _ellisse(28, 27.5, 3, 3), ORO6, base=4, grad=lambda x, y: -((x - 28) + (y - 27.5)) * 0.15))
    _put(img, {(28, 27): ORO6[5]})
    return outline(img, ORO_SCURO)


def condividi():
    """Share icon: three gold spheres joined by bars, lit from the top left, a halo above the top one."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    nodi = [(33, 23), (14, 33), (33, 42)]
    aste = set()
    for (ax, ay), (bx, by) in ((nodi[1], nodi[0]), (nodi[1], nodi[2])):
        n = max(abs(bx - ax), abs(by - ay))
        for i in range(n + 1):
            x, y = round(ax + (bx - ax) * i / n), round(ay + (by - ay) * i / n)
            aste |= {(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)}
    _put(img, _bevel(aste, ORO6, base=2.4))
    for (cx, cy) in nodi:
        _put(img, {(x, y): _t(ORO6, 3 - ((x + 0.5 - cx) * 0.35 + (y + 0.5 - cy) * 0.45) + (1.3 if (x + 2.5 - cx) ** 2 + (y + 2.5 - cy) ** 2 < 2.2 else 0))
                   for (x, y) in _ellisse(cx, cy, 5.3, 5.3)})
    alone = _ellisse(33, 8, 10.5, 3.6) - _ellisse(33, 8, 7.5, 1.7)
    _put(img, {(x, y): _t(ORO6, (3.4 if y > 8 else 2) - (x - 33) * 0.08 + (1.5 if y > 8 and 26 <= x <= 29 else 0)) for (x, y) in alone})
    return outline(img, ORO_SCURO)


def gira():
    """"Flip the card" icon: the gold ribbon ring re-toned, the front band lit on top and to the left,
    the inside face in shade."""
    return _ricolora(_gira_base(), {GOLD: (ORO6, 3.2, lambda x, y: -(x - 24) * 0.05),
                                    shade(GOLD, 0.72): (ORO6, 1.6, lambda x, y: -(x - 24) * 0.03),
                                    GOLD_DARK: (ORO6, 0.6, None)})


def segnalibro(attivo=True, colori="lapislazzuli"):
    """Bookmark of the favourite cards, re-toned: the cloth with a lit fold on the left, the gold border
    and rod in relief, a dark-gold outline. Empty: a faint outline, as before."""
    img = _segnalibro_base(attivo, colori)
    if not attivo:
        return img
    drappo, bordo = STENDARDI[colori]
    R = LAPIS6 if colori == "lapislazzuli" else [shade(drappo, f) for f in (0.45, 0.65, 0.85, 1.0, 1.25, 1.5)]
    mats = {drappo: (R, 2.8, lambda x, y: -(x - 7) * 0.18 - (0.6 if y > 14 else 0)), shade(drappo, 1.25): (R, 4.2, None)}
    if bordo == GOLD:
        mats.update({GOLD: (ORO6, 3, None), GOLD_DARK: (ORO6, 1.5, None), GOLD_LIGHT: (ORO6, 5, None)})
    out = _ricolora(img, mats)
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y][3] and px[x, y][:3] == OUTLINE:
                px[x, y] = ORO_SCURO + (255,)
    return out


def banner(zoom=5):
    """The repo banner, 1024x500: the splash screen's logo, gothic title and subtitle on its red,
    with a gold frame around."""
    w, h = 1024, 500
    img = Image.new("RGBA", (w, h), LOGO_RED + (255,))
    big = lambda im: im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    mark, title = big(logo()), big(etichetta(CAPOLETTERA_M, "annaggia!", "nudo"))
    x = (w - (mark.width + 40 + title.width)) // 2
    img.alpha_composite(mark, (x, (h - mark.height) // 2))
    tx, ty = x + mark.width + 40, (h - title.height) // 2 - 34
    img.alpha_composite(title, (tx, ty))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(ROOT / "app/src/main/res/font/unifraktur_maguntia.ttf"), 40)
    d.text((tx + title.width // 2, ty + title.height + 44), "Un santo a caso, quando serve.",
           font=font, fill=(255, 193, 7), anchor="mm")          # the subtitle's colour on the splash
    for i, col in enumerate((GOLD_DARK, GOLD_LIGHT, GOLD_DARK)):
        p = 6 * (i + 2)
        d.rectangle((p, p, w - 1 - p, h - 1 - p), outline=col, width=6)
    return img.convert("RGB")


def icona_play(zoom=7):
    """The Play icon, 512x512: the logo on the red background."""
    img = Image.new("RGBA", (512, 512), LOGO_RED + (255,))
    mark = logo()
    mark = mark.resize((mark.width * zoom, mark.height * zoom), Image.NEAREST)
    img.alpha_composite(mark, ((512 - mark.width) // 2, (512 - mark.height) // 2))
    return img.convert("RGB")


def icona_launcher(zoom=4):
    """Foreground of the adaptive app icon, 432x432 (xxxhdpi): the logo filling the 72 dp a launcher shows
    (the bubble's sides go a little past the 66 dp safe zone, the user's choice: a bigger logo)."""
    img = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    mark = logo()
    mark = mark.resize((mark.width * zoom, mark.height * zoom), Image.NEAREST)
    img.alpha_composite(mark, ((432 - mark.width) // 2, (432 - mark.height) // 2))
    return img


def genera_grafica():
    """The banner (repo and Play feature graphic), the Play icon and the launcher icon."""
    (ROOT.parent / "docs/img").mkdir(parents=True, exist_ok=True)
    banner().save(ROOT.parent / "docs/img/banner.png", optimize=True)
    banner().save(ROOT / "store/feature-graphic.png", optimize=True)
    icona_play().save(ROOT / "store/icon-512.png", optimize=True)
    res = ROOT / "app/src/main/res/drawable-nodpi"
    res.mkdir(exist_ok=True)
    icona_launcher().save(res / "ic_launcher_foreground.png", optimize=True)


def anteprima_timbro(out, zoom=8):
    """Save the stamp variants and the button, enlarged, for review."""
    out.mkdir(parents=True, exist_ok=True)
    for v in ("piena", "sottile", "nastro"):
        img = timbro() if v == "piena" else etichetta(CAPOLETTERA_N, "uova!", v)
        img.resize((img.width * zoom, img.height * zoom), Image.NEAREST).save(out / f"timbro-{v}.png")
    for nome in PULSANTI:
        for premuto in (False, True):
            img = pulsante(premuto, nome)
            suffisso = "-premuto" if premuto else ""
            img.resize((img.width * zoom, img.height * zoom), Image.NEAREST).save(out / f"pulsante-{nome}{suffisso}.png")
    # Bookmarks: every palette, full and empty, on a light and a dark card.
    tile, tile_h = (SEGNALIBRO_W + 6) * zoom, (SEGNALIBRO_H + 4) * zoom
    sheet = Image.new("RGB", (tile * 2 * len(STENDARDI), tile_h * 2), (240, 226, 230))
    ImageDraw.Draw(sheet).rectangle((0, tile_h, sheet.width, sheet.height), fill=(36, 30, 38))
    for i, colori in enumerate(STENDARDI):
        for j, attivo in enumerate((True, False)):
            img = segnalibro(attivo, colori)
            big = img.resize((img.width * zoom, img.height * zoom), Image.NEAREST)
            for row in (0, 1):
                sheet.paste(big, ((i * 2 + j) * tile + 3 * zoom, row * tile_h + 2 * zoom), big)
    sheet.save(out / "segnalibri.png")
    print(f"anteprime del timbro, dei pulsanti e dei segnalibri in {out}", file=sys.stderr)


def render_final(name, t, leggendario):
    img = render(name, t)
    if leggendario:
        img.alpha_composite(cornice_di(name)())
    return img.convert("RGB")


def render_colorful(name, t, nome):
    """Avatar with its frame of the Colorful option ([nome] from cornice_colorata())."""
    img = render(name, t)
    if nome:
        img.alpha_composite((cornice_palma if nome == "palma" else COLORATE[nome])())
    return img.convert("RGB")


# --- Tratti da Wikidata -------------------------------------------------------

def wikidata_facts(names, cache=None):
    """santo -> {female, beato, labels, birth, sitelinks} from Wikidata, in batches.

    [cache] is a JSON file: when it exists it is used instead of the network, so the
    avatars can be regenerated identically (Wikidata changes over time).
    """
    import json
    if cache and Path(cache).exists():
        facts = json.loads(Path(cache).read_text(encoding="utf-8"))
        return {n: facts[n] for n in names if n in facts}
    spec = importlib.util.spec_from_file_location("gs", ROOT / "tools/genera_santi.py")
    gs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gs)
    people = gs.collect(gs.fetch())
    qids = {}
    for q, p in people.items():
        qids.setdefault(gs.display_name(p), q)  # same name, several items: keep the first
    wanted = {qids[n]: n for n in names if n in qids}
    facts = {n: {"female": people[q]["female"], "beato": not people[q]["saint"],
                 "labels": [], "birth": None, "sitelinks": 0} for q, n in wanted.items()}
    items = list(wanted)
    for i in range(0, len(items), 200):  # one big VALUES makes Wikidata time out
        query = """SELECT ?item ?valLabel ?birth ?sitelinks WHERE {
          VALUES ?item { %s }
          OPTIONAL { ?item wikibase:sitelinks ?sitelinks }
          OPTIONAL { ?item wdt:P569 ?birth }
          OPTIONAL { VALUES ?p { wdt:P39 wdt:P611 wdt:P106 wdt:P1196 wdt:P411 } ?item ?p ?val. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }""" % " ".join(
            "wd:" + q for q in items[i:i + 200])
        for row in gs.fetch(query):
            f = facts[wanted[row["item"]["value"].rsplit("/", 1)[1]]]
            if "valLabel" in row and row["valLabel"]["value"].lower() not in f["labels"]:
                f["labels"].append(row["valLabel"]["value"].lower())
            if "sitelinks" in row:
                f["sitelinks"] = int(row["sitelinks"]["value"])
            if "birth" in row and f["birth"] is None:
                try:
                    f["birth"] = int(row["birth"]["value"].lstrip("+").split("-")[0] or 0)
                except ValueError:
                    pass
        print(f"  Wikidata: {min(i + 200, len(items))}/{len(items)}", file=sys.stderr)
    if cache:
        Path(cache).write_text(json.dumps(facts, ensure_ascii=False, indent=0), encoding="utf-8")
    return facts


def wikidata_tratti(names, cache=None):
    """Tratti dalle regole, per santi non in FAMOSI."""
    facts = wikidata_facts(names, cache)
    return {n: regole(n, f["female"], f["beato"], " | ".join(f["labels"]), f["birth"])
            for n, f in facts.items()}


# Martyrs that neither the name nor Wikidata's labels say: San Raffaele di Lesbo (1463), once
# "San Raffaele martire" (renamed by LABELS in tools/genera_santi.py).
MARTIRI = {"San Raffaele di Lesbo"}


def regole(name, donna, beato, labels, birth):
    t = Tratti(donna=donna, beato=beato)
    has = lambda *ws: any(w in labels for w in ws)  # noqa: E731
    t.eta = ["giovane", "adulto", "adulto", "anziano"][h(name, "eta") % 4]
    if donna:
        t.capelli = "lunghi"
    else:
        t.capelli = ["corti", "corti", "ricci", "calvo"][h(name, "taglio") % 4]
        t.barba = ["nessuna", "corta", "lunga"][h(name, "barba") % 3] if (birth or 0) < 1600 else "nessuna"
    # Also by the name ("San Placido martire"), when Wikidata has no label for it, and MARTIRI.
    t.martire = has("martyr", "execution", "decapitation", "beheading", "killed", "homicide", "crucifixion",
                    "shot", "capital punishment", "burned at the stake", "stoning", "hanging") \
        or "martir" in name.lower() or name in MARTIRI
    if has("pope"):
        t.copricapo, t.abito, t.attributo = ("tiara" if (birth or 0) < 1900 else "zucchetto_bianco"), "papa", "croce"
    elif has("cardinal"):
        t.copricapo, t.abito, t.attributo = "zucchetto_rosso", "cardinale", "libro"
    elif has("bishop", "archbishop", "patriarch"):
        t.copricapo, t.abito, t.attributo = "mitra", "vescovo", "pastorale"
    elif has("franciscan", "capuchin", "friars minor", "poor clares", "conventual"):
        t.abito, t.capelli = "saio", ("tonsura" if not donna else t.capelli)
        if donna:
            t.copricapo, t.abito, t.colore_abito = "velo", "suora", BROWN_HABIT
    elif has("dominican", "order of preachers"):
        t.abito, t.capelli = "domenicano", ("tonsura" if not donna else t.capelli)
        if donna:
            t.copricapo, t.colore_velo, t.abito, t.colore_abito = "velo", BLACK, "suora", WHITE
    elif has("carmelite"):
        t.abito, t.colore_abito = ("suora", CARMEL) if donna else ("saio", CARMEL)
        if donna:
            t.copricapo, t.colore_velo = "velo", BLACK
    elif has("benedictine", "cistercian", "trappist", "carthusian", "abbot", "abbess", "monk", "nun"):
        if donna:
            t.copricapo, t.abito, t.colore_abito = "velo", "suora", BLACK_HABIT
        else:
            t.abito, t.capelli = ("cistercense" if has("cistercian", "trappist", "carthusian") else "benedettino"), "tonsura"
    elif donna and has("religious sister", "ursuline", "sisters", "missionary sisters"):
        t.copricapo, t.abito, t.colore_abito = "velo", "suora", BLACK_HABIT
    elif has("king", "monarch", "emperor", "prince", "queen", "duke", "empress", "princess"):
        t.copricapo, t.abito = "corona", "regale"
        t.colore_abito = (120, 40, 120) if h(name, "re") % 2 else (150, 40, 50)
    elif has("soldier", "knight", "military"):
        t.abito, t.attributo = "armatura", "spada"
    elif has("hermit", "anchorite", "stylite"):
        t.abito, t.colore_abito, t.attributo = "saio", (96, 78, 62), "bastone"
        if not donna:
            t.barba, t.eta = "lunga", "anziano"
    elif has("priest", "jesuit", "presbyter", "missionary", "deacon"):
        t.abito, t.attributo = "talare", "libro"
    if t.martire and t.attributo == "nessuno":
        t.attributo = "palma"  # only an empty hand: the red background, the label and the frame already say martyr
    elif t.attributo == "nessuno":
        t.attributo = ["nessuno", "libro", "croce", "giglio"][h(name, "attr") % 4]
    # The epithet wins over the age set above (e.g. the hermit's): "San Basilio il Giovane"
    # must not look older than "San Basilio il Vecchio". Grey hair comes with "anziano".
    if " il Giovane" in name or " la Giovane" in name:
        t.eta = "giovane"
        if not donna:
            t.barba = "corta" if t.barba == "lunga" else t.barba
            t.capelli = "corti" if t.capelli == "calvo" else t.capelli
    elif " il Vecchio" in name or " la Vecchia" in name:
        t.eta = "anziano"
        if not donna and t.barba == "nessuna":
            t.barba = "lunga"
    return t


def contact_sheet(tiles, path, zoom, cols):
    cell = S * zoom
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell + 10) + 10, rows * (cell + 26) + 10), (28, 28, 28))
    d = ImageDraw.Draw(sheet)
    for i, (n, img) in enumerate(tiles):
        x = 10 + (i % cols) * (cell + 10)
        y = 10 + (i // cols) * (cell + 26)
        sheet.paste(img.resize((cell, cell), Image.NEAREST), (x, y))
        d.text((x, y + cell + 5), n[:38], fill=(230, 230, 230))
    sheet.save(path)


def file_id(name):
    return hashlib.sha1(name.encode("utf-8")).hexdigest()[:12]


# Card numbers fixed after the first catalogue, so that the others don't change. A saint added later
# (EXTRA_PEOPLE of genera_santi.py) takes the number of one removed (EXCLUDE), new -> removed;
# None numbers him at the end. The removed one stays in tratti_wikidata.json for its place.
POSTO = {"Beato Bernardo II di Baden": "Sant'Ageltrude"}


def genera_tutti(santi_path, out, cache, n_leggendari, provini, seed=1, app=False):
    """All saints: <sha1>.png (no frame; not with [app]: the app's 96 px portraits come from tools/ritratti96), cornice_NN.png, the CORNICI frames with cornici.txt,
    the COLORATE frames with cornici_colorful.txt, leggendari.txt and, unless [app] (only
    what the app ships), tratti.tsv and review sheets."""
    import random
    names = [l.strip() for l in open(santi_path, encoding="utf-8") if l.strip() and not l.startswith("#")]
    facts = wikidata_facts(names, cache)
    tratti = {n: FAMOSI.get(n) or regole(n, f["female"], f["beato"], " | ".join(f["labels"]), f["birth"])
              for n, f in facts.items()}
    for n in names:  # not found on Wikidata (renamed item, ...): generic avatar from the name only
        tratti.setdefault(n, FAMOSI.get(n) or regole(n, n.startswith(("Santa", "Beata")),
                                                     n.startswith("Beat"), "", None))
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, n in enumerate(names, 1):
        t = tratti[n]
        if not app:   # the app's 96 px portraits come from tools/ritratti96 (installa.py), not from here
            render(n, t).convert("RGB").save(out / f"{file_id(n)}.png", optimize=True)
        rows.append((n, file_id(n), "tabella" if n in FAMOSI else ("regole" if n in facts else "solo nome"),
                     t.abito, t.copricapo, t.attributo))
        if i % 500 == 0:
            print(f"  avatar: {i}/{len(names)}", file=sys.stderr)
    for step in range(FRAME_STEPS):
        cornice(step).save(out / f"cornice_{step:02d}.png", optimize=True)
        for nome, disegna in list(CORNICI.values()) + list(CORNICI_PREMIO.items()):
            disegna(step).save(out / f"{nome}_{step:02d}.png", optimize=True)
        for nome, disegna in list(COLORATE.items()) + [("palma", cornice_palma)]:
            disegna(step).save(out / f"{nome}_{step:02d}.png", optimize=True)
    # Card numbers: N. 1 is the most famous saint (most Wikipedia sitelinks), ties by name; POSTO above.
    tolti = [v for k, v in POSTO.items() if v and k in names]
    fama = {**wikidata_facts(tolti, cache), **facts}
    by_fame = sorted([n for n in names if n not in POSTO] + tolti, key=lambda n: (-fama.get(n, {}).get("sitelinks", 0), n))
    by_fame = [next((k for k, v in POSTO.items() if v == n), n) for n in by_fame]
    by_fame += [n for n, v in POSTO.items() if not v and n in names]
    leggendari = by_fame[:n_leggendari]
    colorate = {n: cornice_colorata(n, tratti[n], n in leggendari) for n in names}
    (out / "cornici_colorful.txt").write_text(
        "# Cornici dell'opzione Colorful: santo<TAB>nome (file <nome>_NN.png). Palma ai martiri; i\n"
        "# leggendari non ci sono e tengono la loro cornice.\n"
        + "".join(f"{n}\t{c}\n" for n, c in colorate.items() if c), encoding="utf-8")
    (out / "catalogo.txt").write_text(
        "# Numero delle figurine: la riga N (senza contare i commenti) e' il santo N. 1 e' il piu' famoso\n"
        "# (piu' voci Wikipedia). I primi sono i leggendari, vedi leggendari.txt.\n"
        + "\n".join(by_fame) + "\n", encoding="utf-8")
    raccoglitore().convert("RGBA").save(out / "raccoglitore.png", optimize=True)
    calendario().convert("RGBA").save(out / "santo_del_giorno.png", optimize=True)
    coppa().convert("RGBA").save(out / "coppa.png", optimize=True)
    condividi().convert("RGBA").save(out / "condividi.png", optimize=True)
    timbro().save(out / "timbro_nuova.png", optimize=True)
    for nome in PULSANTI:
        pulsante(False, nome).save(out / f"pulsante_{nome}.png", optimize=True)
        pulsante(True, nome).save(out / f"pulsante_{nome}_premuto.png", optimize=True)
    cornice_argento().save(out / "cornice_argento.png", optimize=True)
    segnalibro(True).save(out / "segnalibro.png", optimize=True)
    logo().save(out / "logo.png", optimize=True)
    etichetta(CAPOLETTERA_M, "annaggia!", "nudo").save(out / "titolo.png", optimize=True)
    segnalibro(False).save(out / "segnalibro_vuoto.png", optimize=True)
    # specials and the Battista back: at 96 px, from tools/ritratti96 (installa.py)
    gira().save(out / "gira.png", optimize=True)
    (out / "speciali.txt").write_text(
        "# Figurine speciali fuori catalogo: la riga N e' la figurina SN (si sbloccano coi trofei).\n"
        + "\n".join(SPECIALI) + "\n", encoding="utf-8")
    # "Sant'" hides the gender: the app needs the female ones for the formulas ({maschile|femminile}).
    sante = sorted(n for n in names if n.startswith("Sant'") and facts.get(n, {}).get("female"))
    (out / "sante.txt").write_text(
        "# Sante il cui nome inizia con Sant' (genere da Wikidata): per le formule d'invocazione.\n"
        + "\n".join(sante) + "\n", encoding="utf-8")
    (out / "cornici.txt").write_text(
        "# Leggendari con una cornice speciale al posto di quella d'oro: santo<TAB>nome (file <nome>_NN.png).\n"
        + "".join(f"{n}\t{nome}\n" for n, (nome, _) in CORNICI.items()), encoding="utf-8")
    (out / "leggendari.txt").write_text(
        "# I santi con piu' voci Wikipedia (Wikidata sitelinks): cornice d'oro nell'album.\n"
        + "\n".join(leggendari) + "\n", encoding="utf-8")
    if app:
        print(f"{len(names)} avatar per l'app in {out}", file=sys.stderr)
        return
    with open(out / "tratti.tsv", "w", encoding="utf-8") as f:
        f.write("santo\tfile\torigine\tabito\tcopricapo\tattributi\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    # Review sheets: random rule-based saints, plus the legendary ones with their frame.
    regole_only = [n for n in names if n not in FAMOSI]
    random.Random(seed).shuffle(regole_only)
    for k in range(provini):
        chunk = regole_only[k * 48:(k + 1) * 48]
        contact_sheet([(n, render(n, tratti[n]).convert("RGB")) for n in chunk],
                      out / f"provino_regole_{k + 1}.png", zoom=4, cols=8)
    contact_sheet([(n, render_final(n, tratti[n], True)) for n in leggendari],
                  out / "provino_leggendari.png", zoom=4, cols=10)
    contact_sheet([(n, render_colorful(n, tratti[n], colorate[n])) for n in regole_only[:48]],
                  out / "provino_colorful.png", zoom=4, cols=8)
    print(f"{len(names)} avatar in {out}; tabella {sum(r[2] == 'tabella' for r in rows)}, "
          f"regole {sum(r[2] == 'regole' for r in rows)}, solo nome {sum(r[2] == 'solo nome' for r in rows)}",
          file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nomi", help="file con i santi (uno per riga)")
    ap.add_argument("--famosi", action="store_true", help="tutta la tabella FAMOSI")
    ap.add_argument("--tutti", action="store_true", help="tutti i santi di --santi, con leggendari e provini")
    ap.add_argument("--santi", default=str(ROOT / "app/src/main/assets/santi.txt"))
    ap.add_argument("--cache", help="JSON con i dati Wikidata (letto se esiste, scritto altrimenti)")
    ap.add_argument("--leggendari", type=int, default=50)
    ap.add_argument("--provini", type=int, default=5, help="con --tutti: provini casuali da 48 santi")
    ap.add_argument("--out", default=str(Path.home() / "mannaggia-avatar-prova"))
    ap.add_argument("--app", help="con --tutti: scrive solo gli asset dell'app in questa cartella "
                                  "(es. app/src/main/assets/avatar)")
    ap.add_argument("--zoom", type=int, default=5)
    ap.add_argument("--colonne", type=int, default=8)
    ap.add_argument("--anteprima-timbro", action="store_true", help="varianti del timbro \"Nuova!\" e il pulsante in --out")
    ap.add_argument("--grafica", action="store_true", help="banner del repo, icona del Play e icona dell'app")
    args = ap.parse_args()
    out = Path(args.out).expanduser()
    if args.anteprima_timbro:
        anteprima_timbro(out)
        return
    if args.grafica:
        genera_grafica()
        return
    if args.tutti:
        if args.app:
            genera_tutti(args.santi, Path(args.app), args.cache, args.leggendari, 0, app=True)
        else:
            genera_tutti(args.santi, out, args.cache, args.leggendari, args.provini)
        return
    names = list(FAMOSI) if args.famosi else []
    if args.nomi:
        names += [l.strip() for l in open(args.nomi, encoding="utf-8") if l.strip() and l.strip() not in names]
    tratti = {n: FAMOSI[n] for n in names if n in FAMOSI}
    others = [n for n in names if n not in FAMOSI]
    if others:
        tratti.update(wikidata_tratti(others, args.cache))
    out.mkdir(parents=True, exist_ok=True)

    tiles = []
    for n in names:
        if n not in tratti:
            print(f"  non trovato: {n}", file=sys.stderr)
            continue
        img = render_final(n, tratti[n], n in LEGGENDARI_PROVA)
        img.save(out / f"{file_id(n)}.png")
        tiles.append((n + ("" if n in FAMOSI else " *"), img))
    contact_sheet(tiles, out / "provino.png", args.zoom, args.colonne)
    print(f"{len(tiles)} avatar in {out} (* = tratti dalle regole Wikidata)", file=sys.stderr)


if __name__ == "__main__":
    main()
