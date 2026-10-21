#!/usr/bin/env python3
"""Avatar in pixel art dei santi (mezzo busto, 48x48), disegnati da zero.

Nessuna immagine esistente viene usata: ogni avatar e' composto da pezzi
disegnati qui (testa, capelli, barba, copricapo, abito, attributi, aureola),
scelti in base ai tratti del santo. I tratti vengono da una tabella fatta a
mano per i santi piu' famosi (FAMOSI) o, per gli altri, da regole sui dati
Wikidata (genere, cariche, ordine religioso, mestiere, martirio). Le piccole
variazioni (carnagione, colori, volto) sono deterministiche: dipendono dal nome.

I santi leggendari hanno in piu' una cornice d'oro (cornice()), disegnata come
livello separato cosi' l'app puo' applicarla sopra l'avatar.

Uso (venv con pillow; dalla cartella mannaggia-android):
    python tools/ritratti/avatar.py --nomi lista.txt --out ~/mannaggia-avatar-prova
    python tools/ritratti/avatar.py --famosi --out ~/mannaggia-avatar-prova   # tutta la tabella
"""

import argparse
import hashlib
import importlib.util
import sys
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
                   abito="tunica", colore_abito=(110, 80, 56), attributo="bordone+cane"),
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
}

# Leggendari per il provino (nell'app si calcoleranno dalle voci Wikipedia).
LEGGENDARI_PROVA = {"San Pietro", "San Paolo di Tarso", "San Francesco d'Assisi",
                    "Sant'Agostino d'Ippona", "San Giovanni Paolo II", "Santa Giovanna d'Arco",
                    "San Tommaso d'Aquino", "Santa Madre Teresa di Calcutta", "San Giovanni Battista",
                    "San Giovanni XXIII", "San Giorgio", "San Nicola di Bari"}


# --- Disegno ------------------------------------------------------------------

class Canvas:
    """48x48 RGBA layer drawn with aliased PIL primitives (pixel-exact)."""

    def __init__(self):
        self.img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
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
        if 0 <= x < S and 0 <= y < S:
            self.img.putpixel((x, y), c + (255,))

    def hole(self, box):
        """Clear pixels so the background shows through (e.g. a key ring)."""
        self.d.ellipse(box, fill=(0, 0, 0, 0))

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


ATTRIBUTI = {name[3:]: fn for name, fn in globals().items() if name.startswith("at_")}


def draw_attributes(c, t):
    for a in t.attributo.split("+"):
        if a != "nessuno":
            ATTRIBUTI[a](c)
    if "stigmate" in t.extra:
        c.px(24, 39, DARK_RED)


# --- Composizione -------------------------------------------------------------

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


def render(name, t):
    skin = SKINS[t.pelle if t.pelle is not None else [0, 1, 1, 2][h(name, "pelle") % 4]]
    hair = HAIRS[t.colore_capelli or ["nero", "castano", "castano", "biondo", "rosso", "nero"][h(name, "capelli") % 6]]
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


# Gemme: scala di luminosita' della stessa tinta, dalla piu' scura alla piu' chiara.
GEM_RED = [(120, 20, 30), (178, 34, 44), (230, 70, 80), (255, 150, 150)]
GEM_BLUE = [(30, 60, 120), (60, 110, 190), (110, 160, 240), (190, 220, 255)]
FRAME_STEPS = 8  # fotogrammi dell'animazione


def _perimeter():
    """Pixel coordinates along the outer ring, clockwise from the top-left corner."""
    top = [(x, 0) for x in range(S)]
    right = [(S - 1, y) for y in range(1, S)]
    bottom = [(x, S - 1) for x in range(S - 2, -1, -1)]
    left = [(0, y) for y in range(S - 2, 0, -1)]
    return top + right + bottom + left


def cornice(step=None):
    """Thin gold frame for legendary saints (transparent inside).

    With [step] (0..FRAME_STEPS-1) it is one frame of the sparkle animation: each gem
    cycles through the light levels of its colour with its own phase, and a short
    glint runs around the border. Without it, the still version.
    """
    c = Canvas()
    c.d.rectangle((0, 0, S - 1, S - 1), outline=GOLD_DARK + (255,))
    c.d.rectangle((1, 1, S - 2, S - 2), outline=GOLD_LIGHT + (255,))

    def gem(i, palette):
        if step is None:
            return palette[1], False
        # Triangle wave 0,1,2,3,2,1,... shifted per gem so they don't blink together.
        k = (step + i * 3) % 6
        level = k if k < 4 else 6 - k
        return palette[level], level == 3

    for i, (x, y) in enumerate(((0, 0), (S - 5, 0), (S - 5, S - 5), (0, S - 5))):
        c.rect((x, y, x + 4, y + 4), GOLD)
        c.d.rectangle((x, y, x + 4, y + 4), outline=GOLD_DARK + (255,))
        col, peak = gem(i, GEM_RED)
        c.px(x + 2, y + 2, col)
        if peak:  # riflesso bianco al massimo della luce
            c.px(x + 1, y + 1, (255, 255, 255))
    for i, (x, y) in enumerate(((S // 2 - 1, 0), (S - 3, S // 2 - 1), (S // 2 - 1, S - 3), (0, S // 2 - 1))):
        c.rect((x, y, x + 2, y + 2), GOLD)
        col, peak = gem(i + 4, GEM_BLUE)
        c.px(x + 1, y + 1, col)
        if peak:
            c.px(x, y, (255, 255, 255))
    if step is not None:
        ring = _perimeter()
        start = step * len(ring) // FRAME_STEPS
        for j, col in enumerate((GOLD_LIGHT, (255, 250, 220), GOLD_LIGHT)):
            x, y = ring[(start + j) % len(ring)]
            if c.img.getpixel((x, y))[:3] in (GOLD_DARK, GOLD_LIGHT):  # only on the plain border
                c.px(x, y, col)
    return c.img


def gif_leggendario(name, t, path, zoom=6, ms=110):
    """Animated preview: still avatar with the sparkling frame on top."""
    base = render(name, t)
    frames = []
    for step in range(FRAME_STEPS):
        f = base.copy()
        f.alpha_composite(cornice(step))
        frames.append(f.convert("RGB").resize((S * zoom, S * zoom), Image.NEAREST))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0)


def render_final(name, t, leggendario):
    img = render(name, t)
    if leggendario:
        img.alpha_composite(cornice())
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
    query = """SELECT ?item ?valLabel ?birth WHERE {
      VALUES ?item { %s }
      OPTIONAL { ?item wdt:P569 ?birth }
      OPTIONAL { VALUES ?p { wdt:P39 wdt:P611 wdt:P106 wdt:P1196 } ?item ?p ?val. }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }""" % " ".join("wd:" + q for q in wanted)
    facts = {n: {"labels": [], "birth": None} for n in wanted.values()}
    for row in gs.fetch(query):
        n = wanted[row["item"]["value"].rsplit("/", 1)[1]]
        if "valLabel" in row:
            facts[n]["labels"].append(row["valLabel"]["value"].lower())
        if "birth" in row and facts[n]["birth"] is None:
            try:
                facts[n]["birth"] = int(row["birth"]["value"].lstrip("+").split("-")[0] or 0)
            except ValueError:
                pass
    return {n: regole(n, people[q]["female"], not people[q]["saint"], " | ".join(facts[n]["labels"]),
                      facts[n]["birth"]) for q, n in wanted.items()}


def regole(name, donna, beato, labels, birth):
    t = Tratti(donna=donna, beato=beato)
    has = lambda *ws: any(w in labels for w in ws)  # noqa: E731
    t.eta = ["giovane", "adulto", "adulto", "anziano"][h(name, "eta") % 4]
    if donna:
        t.capelli = "lunghi"
    else:
        t.capelli = ["corti", "corti", "ricci", "calvo"][h(name, "taglio") % 4]
        t.barba = ["nessuna", "corta", "lunga"][h(name, "barba") % 3] if (birth or 0) < 1600 else "nessuna"
    t.martire = has("martyr", "execution", "decapitation", "killed", "homicide", "crucifixion", "shot")
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
    elif has("priest", "jesuit", "presbyter", "missionary", "deacon"):
        t.abito, t.attributo = "talare", "libro"
    if t.attributo == "nessuno" and t.martire:
        t.attributo = "palma"
    elif t.attributo == "nessuno":
        t.attributo = ["nessuno", "libro", "croce", "giglio"][h(name, "attr") % 4]
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nomi", help="file con i santi (uno per riga)")
    ap.add_argument("--famosi", action="store_true", help="tutta la tabella FAMOSI")
    ap.add_argument("--out", default=str(Path.home() / "mannaggia-avatar-prova"))
    ap.add_argument("--zoom", type=int, default=5)
    ap.add_argument("--colonne", type=int, default=8)
    args = ap.parse_args()
    names = list(FAMOSI) if args.famosi else []
    if args.nomi:
        names += [l.strip() for l in open(args.nomi, encoding="utf-8") if l.strip() and l.strip() not in names]
    tratti = {n: FAMOSI[n] for n in names if n in FAMOSI}
    others = [n for n in names if n not in FAMOSI]
    if others:
        tratti.update(wikidata_tratti(others))
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    tiles = []
    for n in names:
        if n not in tratti:
            print(f"  non trovato: {n}", file=sys.stderr)
            continue
        img = render_final(n, tratti[n], n in LEGGENDARI_PROVA)
        img.save(out / f"{hashlib.sha1(n.encode()).hexdigest()[:12]}.png")
        tiles.append((n + ("" if n in FAMOSI else " *"), img))

    z, cols = args.zoom, args.colonne
    cell = S * z
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cell + 10) + 10, rows * (cell + 26) + 10), (28, 28, 28))
    d = ImageDraw.Draw(sheet)
    for i, (n, img) in enumerate(tiles):
        x = 10 + (i % cols) * (cell + 10)
        y = 10 + (i // cols) * (cell + 26)
        sheet.paste(img.resize((cell, cell), Image.NEAREST), (x, y))
        d.text((x, y + cell + 5), n[:38], fill=(230, 230, 230))
    sheet.save(out / "provino.png")
    print(f"{len(tiles)} avatar in {out} (* = tratti dalle regole Wikidata)", file=sys.stderr)


if __name__ == "__main__":
    main()
