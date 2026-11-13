# Generatore dei ritratti a 96 px

Ritratti pixel art a 96×96 per i 5420 santi di `santi.txt`, **senza occhi**: l'app li disegna sopra, animati (`Occhi.kt`).

In repo ci sono solo i file che servono a rigenerarli e a controllarli. Provini, test scartati e fogli di anteprima non vanno committati.

## Requisiti

- Node ≥ 22.18 e pxl (MIT, copia minima in `android/tools/pxl/`); nei comandi qui sotto è `PXL`.
- Il venv `~/venv/ritratti`, con pillow.
- Il repo in `~/Git/mannaggia-android/android`: i tratti dei santi vengono da `tools/ritratti/avatar.py`.

```sh
PXL="node $HOME/Git/mannaggia-android/android/tools/pxl/bin/pxl.js"
PY=~/venv/ritratti/bin/python
```

## Come si rigenera tutto

```sh
cd ~/Git/mannaggia-android/android/tools/ritratti96
$PY -I esporta.py --repo ~/Git/mannaggia-android/android        # tratti96.data.js + ripieghi.tsv
rm -rf ~/mannaggia-cache/ritratti96 ~/mannaggia-cache/buchi96
$PXL build ritratti96.px.js --no-preview --out ~/mannaggia-cache/ritratti96   # 5420 ritratti, ~40 s, ~1,2 GB RAM
$PXL build buchi96.px.js    --no-preview --out ~/mannaggia-cache/buchi96      # gli stessi su sfondo magenta
$PY -I verifica_occhi.py ~/mannaggia-cache/ritratti96   # deve dire 5420/5420 ok
$PY -I verifica_buchi.py                                # deve dire 5420/5420 ok
```

## Copia negli asset dell'app

Le figurine speciali (S1–S5, S7, senza occhi), Santa Pazienza (S6) e il retro del Battista si costruiscono a parte, poi `installa.py` copia tutto in `assets/avatar/` con i nomi dell'app (`<id>.png`, `decollato.png`):

```sh
$PXL build speciali96.px.js --no-preview --only s1,s2,s3,s4,s5,s7,decollato96 --out ~/mannaggia-cache/speciali_app96
$PXL build pazienza96px.px.js --no-preview --only pazienza96_base --out ~/mannaggia-cache/pazienza_app96
$PY -I installa.py --app ../../app/src/main/assets/avatar
```

## Dati degli occhi per l'app

`occhi96.py` scrive in `assets/avatar/` `occhi96.tsv` (per ogni ritratto: iride, sopracciglia, ciglia sotto, forma, occhiali) e `emozioni.txt` (le 6 emozioni di `occhi.px.js`, che sono la fonte unica). I colori li legge da ritratti con gli occhi aperti, a pixel fissi, quindi prima servono le anteprime:

```sh
$PXL build anteprima96.px.js --no-preview --out ~/mannaggia-cache/anteprima96
$PXL build speciali96.px.js --no-preview --only spec_s1_santo_subito,spec_s2_san_culo,spec_s3_san_calendario,spec_s4_san_deploy,spec_s5_san_sudo,spec_s7_santa_cunegonda --out ~/mannaggia-cache/speciali_occhi96
$PXL build pazienza96px.px.js --no-preview --only pazienza_96 --out ~/mannaggia-cache/pazienza_occhi96
$PY -I occhi96.py --app ../../app/src/main/assets/avatar
```

`Occhi.kt` disegna gli occhi sul ritratto senza occhi: è la copia in Kotlin di `occhi()` e `occhiali()` di `occhi.px.js`. Se cambi uno dei due, cambia anche l'altro (coordinate del ritratto: figura di 94 px + 1 di contorno).

Il risultato è `~/mannaggia-cache/ritratti96/sprites/p_<id>.png`, dove `<id>` sono i primi 12 caratteri dello sha1 del nome, come per gli avatar di oggi. Pesa in tutto circa 4,9 MB.

## Anteprime con gli occhi

- `anteprima96.px.js`: gli stessi ritratti con gli occhi aperti. Usa `--only p_<id>,...` per costruirne pochi.
- Per il campione di 30 santi per categoria: `$PY -I esporta.py --repo … --campione 30 --out campione96.data.js`. Poi costruisci con `--only` gli id del campione.
- I fogli per l'utente (`campione96_<categoria>.png`, ecc.) vanno fuori dal repo.

## I file

| File | Cosa fa |
|---|---|
| `esporta.py` | Legge da `avatar.py` (`FAMOSI`, `PELLE`, `regole()`, la cache di Wikidata, gli hash del nome) i tratti risolti di ogni santo e li scrive in `tratti96.data.js` nel vocabolario della libreria. Contiene anche: `VOLTO` (tratti del viso per i santi di altri popoli), le varianti del viso scelte dal nome, i martiri dell'Uganda (stoffa di corteccia, barba di Kaggwa). Scrive `ripieghi.tsv`: i tratti senza una parte disegnata. |
| `libreria96.px.js` | La libreria: geometria fissa, scale di colore, viso con le varianti, orecchie, capelli, barba, abiti, copricapi, alone, e la funzione `ritratto96(nome, d, {con_occhi, seq})`. Ogni attributo è uno sprite a sé con il suo contorno, appoggiato sopra la figura già contornata. |
| `parti96.px.js` | Le parti in più per i santi di `FAMOSI`: 36 attributi (chiavi, ruota, drago, lancia…), 6 abiti, 4 copricapi, gli extra (`EXTRA96`: stella, fiamma, medaglione…). |
| `occhi96.py` | Scrive `occhi96.tsv` e `emozioni.txt` negli asset (vedi sopra). |
| `installa.py` | Copia i ritratti generati in `assets/avatar/` con i nomi dell'app (vedi sopra). |
| `ritratti96.px.js` | Il generatore: un ritratto senza occhi per ogni santo di `tratti96.data.js`. |
| `anteprima96.px.js` | Come sopra, ma con gli occhi aperti. |
| `buchi96.px.js` | Come sopra, ma su sfondo magenta, per `verifica_buchi.py`. |
| `verifica_occhi.py` | Controllo: nelle zone di occhi e sopracciglia (x 32–41 e 54–63, y 34–46) deve esserci solo pelle. |
| `verifica_buchi.py` | Controllo: nessun buco nella figura da cui si veda lo sfondo, magenta anche se scurito dall'ombra. |
| `speciali96.px.js` | Provini delle figurine speciali S1–S7, del retro del Battista (`decollato96`) e degli occhiali sugli occhi animati. Le parti nuove (striscione, ferro di cavallo, server, terminale, fulmine, sfere, clessidra, cuffie) sono definite qui. |
| `pazienza96px.px.js` | Santa Pazienza: il provino approvato, con gli occhi spostati nella posizione fissa. `pazienza96_base` è la versione senza occhi. |
| `felpe96b.px.js` | La felpa di San Sudo. Approvata: `felpa2_aperta`. |
| `felpe96.px.js` | Il primo giro di felpe, scartato. |
| `combinazioni96.px.js` | Tutte le combinazioni di naso e bocca, per il foglio di controllo. |
| `provino_etnie.px.js` | Il primo provino dei tratti dei santi di altri popoli. |
| `*_vN.px.js`, `esporta_v1.py` | Copie delle versioni precedenti. |
| `occhi.px.js` | Occhi, sopracciglia, le 6 emozioni (`EMOZIONI`, 48 passi da 83 ms) e gli occhiali (`occhiali()`). Sono il modello per `Occhi.kt`. |

## Regole fisse (non cambiarle senza ricontrollare tutto)

- **Geometria:**
  - asse cx 47 nella figura di 94 px;
  - viso con centro y 43, larghezza 18–19, altezza 21–22;
  - collo largo 24 px;
  - alone di raggio 35, centro y 34;
  - spalle a tutta larghezza.
- **Occhi:** centri a cx−11 e cx+10, y 41; sopracciglia a y 36; lato in ombra da x > cx+12. Nella zona degli occhi non si disegna niente: gli attributi stanno a x ≥ 64 sopra y 47. Il controllo `verifica_occhi.py` lo verifica.
- **Tra naso e bocca:** la riga y 53 resta sempre pelle. Il naso non scende sotto y 52, la bocca sta a y 54 e gli angoli del sorriso a y 53.
- **Contorni:** un solo contorno da 1 px per ogni elemento. Gli attributi hanno il proprio e vengono appoggiati sopra la figura già contornata.
- **Due attributi non si sovrappongono:** il secondo va a sinistra, specchiato.
- **Cappuccio della felpa:** viene ridisegnato dopo il viso, e il suo bordo sopra i capelli è in ombra, mai chiaro.
