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
$PY -I verifica_bocca.py ~/mannaggia-cache/ritratti96   # deve dire 5420/5420 ok
```

## Copia negli asset dell'app

Le figurine speciali (S1–S5, S7, senza occhi), Santa Pazienza (S6) e il retro del Battista si costruiscono a parte, poi `installa.py` copia tutto in `assets/avatar/` con i nomi dell'app (`<id>.png`, `decollato.png`):

```sh
$PXL build speciali96.px.js --no-preview --only s1,s2,s3,s4,s5,s7,decollato96 --out ~/mannaggia-cache/speciali_app96
$PXL build pazienza96px.px.js --no-preview --only pazienza96_base --out ~/mannaggia-cache/pazienza_app96
$PY -I installa.py --app ../../app/src/main/assets/avatar
```

## Dati degli occhi per l'app

`occhi96.py` scrive in `assets/avatar/` anche i dati della bocca: `bocca96.tsv` (forma a riposo, barba, cinque colori, letti dall'angolo in alto a sinistra delle anteprime, dove `ritratto96` li lascia) e `bocche.txt` (le forme di `bocca.px.js`), e la colonna bocca di `emozioni.txt`. Poi `occhi96.tsv` (per ogni ritratto, 9 colonne: iride, sopracciglia, pelle della piega e della palpebra sotto, forma, occhiali, coda delle sopracciglia, sopracciglia folte, donna) e `emozioni.txt` (le 6 emozioni di `occhi.px.js`, che sono la fonte unica). Tutti i colori li legge, a pixel fissi, da ritratti con gli occhi B aperti, quindi prima servono le anteprime. `Occhi.kt` legge anche i file vecchi a 6 e 8 colonne:

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
| `bocca.px.js` | Le bocche (2026-11-18): le forme a riposo per famiglia (donne W0–W2, anziani A0–A1, uomini M0–M2, barbuti B0–B2, barbuti anziani B3/B2: `bocca_f` in `esporta.py`, il nome sceglie la forma) e quelle delle emozioni (O, socchiusa, sbuffo, storta, broncio, mezzo sorriso). I ritratti con `bocca_f` non hanno la bocca: la disegna l'app (`Bocca.kt`, che legge `bocche.txt`). Le figurine speciali la tengono disegnata. |
| `verifica_bocca.py` | Controllo: nella zona della bocca (righe 53–58, dx −7…7; per i barbuti l'apertura sotto i baffi) un solo colore di pelle. |
| `occhi.px.js` | Occhi, sopracciglia, le 6 emozioni (`EMOZIONI`, 48 passi da 83 ms) e gli occhiali (`occhiali()`). Sono il modello per `Occhi.kt`. |

## Stile «ricco» (in corso)

Lo stile approvato sui provini a mano (sei toni per materiale, luce da in alto a sinistra, ogni parte una maschera più una funzione di tono) entra nella libreria una famiglia di parti alla volta. Finora:

- `rampa6(base, rif)`: scala a sei toni di un colore qualsiasi, presa da una scala scelta a mano dello stesso materiale (`PELLE6`, `ORO6`, `ORO6_BEATO`). Il tono 3 è il colore di base.
- `faccia6(d)` e `collo6(d)`: viso e collo, con le varianti di viso, naso e bocca, le rughe degli anziani e l'ombra che capelli e copricapi gettano sulla fronte (`ombra`, da disegnare dopo di loro). Nella zona degli occhi restano due soli toni.
- `aureola6(beato, legg)` e `sfondo6(d)`: i leggendari hanno l'aureola punzonata con i raggi e lo sfondo a losanghe, gli altri aureola e sfondo semplici.
- Gli occhi sono gli occhi B di `occhi()` in `occhi.px.js` (approvati animati il 2026-11-15): sopracciglia ad arco che si assottigliano (tre righe, «folte», per gli uomini anziani), piega della palpebra, iride a tre toni con pupilla e riflesso, ombra della palpebra sulla prima riga del bianco, angoli bassi arrotondati, ciglia all'esterno. Cinque palpebre: aperti, spalancati, abbassati, socchiusi, chiusi. Per genere (2026-11-17): sopracciglia delle donne sottili ad arco, una riga, e ciglia esterna più lunga; degli uomini spesse e più dritte, due righe; degli anziani folte, tre righe. L'occhio «mono» non ha la piega e tiene tutte le righe del bianco; con gli occhiali niente ciglia esterna. Le sopracciglia non salgono mai sopra y 33. `Occhi.kt` ne è la copia riga per riga.

- `capelli6(d, viso)` e `barba6(d, viso)`: capelli e barbe. Le sagome restano quelle di `capelliDietro`, `capelliDavanti` e `barba`, disegnate con colori segnaposto (`MARCA_C`, `MARCA_B`); poi una passata ridipinge ogni pixel segnato con uno dei sei toni di `chioma6(colore)`: ciocche a ventaglio, riflesso, bordo in luce, punte in ombra, frangia frastagliata; ricci e afro tengono le loro luci. I baffi sono una forma a due lobi, mai una riga attraverso la barba, e sotto c'è la bocca. `tara96` va per primo tra gli elementi della figura. Il bordo superiore della barba è una curva (guance, naso e dintorni della bocca liberi, basette fino a y 46); i baffi stanno sopra la bocca (righe 52–53), poi una riga di pelle, la bocca a y 55 e il labbro a y 56: con la barba la bocca la disegna `barba6`, non `faccia6`.
- `pieghe6(d, viso)`: acconciature delle donne con i capelli lunghi, scelte da `d.piega` (1 lunghi lisci sulle spalle, 2 mossi, 3 raccolti a crocchia, 4 treccia sulla spalla, 5 caschetto con la riga di lato; 0 o assente il taglio di sempre). `esporta.py` sceglie `piega` dal nome tra le cinque nuove, in parti uguali; sotto un copricapo la crocchia non si usa. Il taglio di sempre (0) non va più alle donne.

- `tagli6(d, viso)`: tagli degli uomini, scelti da `d.taglio` per famiglia `d.capelli`. Corti: 1 riga di lato e ciuffo, 2 all'indietro con la fronte alta, 3 frangia corta, 4 scompigliati, 5 a paggio. Ricci: 1 corti e fitti, 2 medi a ciocche, 3 ondulati. Tonsura: 1 corona stretta, 2 corona larga. Calvo: 1 del tutto, 2 capelli ai lati, 3 stempiato con il ciuffo. Restituisce `dietro` e `davanti` (maschere nel segnaposto, cranio nudo a sei toni di pelle), `stile` (come `capelli6` fa correre le ciocche: `riga`, `indietro`, `corto`, `onda`, `onde`, `ricci`, `tonsura`) e `coperte` (i capelli coprono le orecchie). `esporta.py` sceglie `taglio` dal nome con la tabella `TAGLI` (seme `taglio96`: `taglio` è già di `avatar.py`): la stempiatura (corti 2, calvo 3) e i capelli ai lati (calvo 2) pesano di più con l'età. Le sagome di sempre (`capelliDietro`, `capelliDavanti`) non vanno più agli uomini di queste quattro famiglie; restano per `afro`, `lisci`, `lunghi`, per le donne con i capelli corti e per le figurine speciali, che non hanno `taglio`. Sotto mitra e tiara calvi e tonsurati prendono corti 3 e nessun taglio disegna la frangia; sotto corona e zucchetto restano calvi o tonsurati, e il ciuffo di calvo 3 non esce dallo zucchetto.
- `ABITI.tunica` ridisegnata a mano (sagoma `spalle()` nel segnaposto `MARCA_V`), `d.tunica_v`: 0 girocollo con l'orlo a fascia e qualche piega sotto, 1 lo stesso con i clavi (porpora `PORPORA6`, oro sulle tuniche viola o scure) e la fascia del collo nel loro colore, 2 scollo largo con tre pieghe che pendono tra due fibule d'oro. `colloT(d, x, y)` dà il tono del collo dentro gli scolli. `esporta.py` sceglie `tunica_v` per epoca: clavi e drappeggio ai nati entro il 600 (anno di nascita di Wikidata), girocollo agli altri; senza anno metà e metà dal nome, ma i beati senza anno prendono il girocollo. Tra gli antichi i clavi vanno a due uomini su tre, il drappeggio a due donne su tre. Il mantello e le figurine speciali, che non hanno `tunica_v`, prendono il girocollo.
- `ABITI.talare` ridisegnata a mano, `d.talare_v`: 0 con la pellegrina abbottonata, 1 liscia con il crocifisso d'oro al cordone, 2 sotto la cotta bianca con la stola, 3 la casula del prete (stoffa liscia, una colonna stretta bordata d'oro, niente gemme, amitto al collo). Le prime tre hanno il colletto alto con la linguetta bianca. `d.stola` è il colore della stola o della casula. `esporta.py` assegna così: nati entro il 1500 la casula; poi i missionari (etichette di Wikidata) il crocifisso; i martiri cotta e stola rossa; degli altri uno su tre cotta e stola, due su tre la pellegrina. Il colore è rosso per i martiri, altrimenti dal nome tra verde, viola e oro (avorio per la casula). Le donne a cui le regole di `avatar.py` danno la talare (13) non la portano: le quattro religiose di `RELIGIOSE` hanno abito da suora e velo, le altre la tunica.
- `ECCEZIONI` in `esporta.py`: i casi che le regole per anno non possono sapere (San Hoel, Beata Nera Tolomei, San Cirillo VI di Alessandria), come campi imposti sopra le regole.
- La suora è ridisegnata a mano sul modello della Santa Chiara approvata. `COPRICAPI.velo`: pieghe a ventaglio, bordo sinistro in luce, striscia di profondità accanto al soggolo; per le suore (`d.abito` `suora`) l'apertura è il soggolo bianco con la benda sulla fronte, per le altre sante velate è in ombra. I veli e gli abiti scuri usano la scala `VELO6` (`veloR`). `ABITI.suora`, `d.suora_v`: 0 pettorina ampia con le pieghe a raggiera, 1 la stessa con un crocifisso di legno, 2 pettorina più corta e scapolare. `esporta.py` assegna: scapolare a benedettine, cistercensi, carmelitane e domenicane (etichette di Wikidata); crocifisso alle altre nate dopo il 1500; pettorina ampia al resto. L'opzione `velo_ombra_scura` non esiste più.
- `ABITI.benedettino` ridisegnato a mano, `d.benedettino_v`: 0 scapolare, 1 scapolare con la croce pettorale d'oro dell'abate, 2 cocolla da coro a pieghe fitte. `rotolo96(x, y, R)` è il cappuccio abbassato a rotolo intorno al collo, da riusare per gli altri abiti dei monaci; `croce96(dx, y, y0)` la croce d'oro sul petto, usata anche dalla talare. `esporta.py` assegna la croce agli abati (etichetta «abbot» di Wikidata), agli altri metà scapolare e metà cocolla dal nome.
- `ABITI.saio` ridisegnato a mano, `d.saio_v`: 0 il cordone bianco con i nodi, 1 il tau francescano di legno d'ulivo (bracci svasati, venatura, cordino), 2 rattoppato con due toppe cucite, 3 carmelitano con mantello e cappuccio bianchi sull'abito bruno e lo scapolare. Tutti con il cappuccio a rotolo (`rotolo96`). `esporta.py` assegna dalle etichette di Wikidata: carmelitano ai carmelitani, rattoppato agli eremiti; cordone e tau, metà e metà dal nome, solo a chi è di un ordine francescano o è nato dopo il 1200; gli altri (monaci più antichi, o senza anno né ordine) prendono il rattoppato.
- Re e regine sono ridisegnati a mano, veste e corona insieme (`d.regale_v` e `d.corona_v`, sempre uguali). `ABITI.regale`: 0 manto aperto sulla tunica con la banda d'oro a gemme e collo d'ermellino, 1 bizantino con collare gemmato bordato di perle e loros, 2 manto chiuso da un fermaglio tondo sul collo ricamato. `COPRICAPI.corona`: 0 cinque punte con le perle, 1 stemma bizantino con placca, croce e pendenti di perle, 2 cerchio con tre gigli. `d.secondo` è il colore del manto (`manto6`). `esporta.py` assegna: bizantino ai sovrani d'Oriente (etichette di Bisanzio, Kiev, Russia, Georgia, Armenia) e agli imperatori romani nati entro il 600; fermaglio e cerchio agli altri nati entro il 1000; ermellino e punte al resto.
- I papi sono ridisegnati a mano. `ABITI.papa`, `d.papa_v`: 0 talare bianca, mozzetta rossa con l'orlo di pelliccia e stola rossa bordata d'oro; 1 il piviale rosso e 2 la casula con il pallio, che sono quelli di `ABITI.vescovo` (colore in `d.stola`, altrimenti rosso e avorio). `COPRICAPI.tiara`, `d.tiara_v`: 0 triregno, 1 cono bianco a una corona. `esporta.py` assegna per anno di nascita: dopo il 1500 o con lo zucchetto la mozzetta; 601-1500 il piviale; entro il 600 o senza anno la casula con il pallio, rossa per i martiri. Tiara a una corona per i nati entro il 1250 o senza anno, triregno per gli altri.
- `ABITI.armatura` ridisegnata a mano, `d.armatura_v`: 0 piastre (quelle della Santa Giovanna approvata: pettorale con la costola, gorgiera, spallacci a tre lame, rivetti dorati), 1 corazza da centurione (corazza anatomica di bronzo `BRONZO6` con i pettorali, strisce di cuoio sulle spalle, fazzoletto al collo, mantello nel colore `d.veste` con la fibula), 2 cotta di maglia ad anelli di 4×3 px a file sfalsate, con la cuffia abbassata e il balteo, 3 uniforme moderna (`d.veste` scurito, mostrine, spalline, bottoni, medaglia). `esporta.py` assegna per anno di nascita: entro il 600 o senza anno la romana, 601-1300 la maglia, 1301-1700 le piastre, dopo il 1700 l'uniforme. `crociato` (San Giorgio) tiene le piastre sotto la sopravveste.
- Domenicano, cistercense e cardinale sono ridisegnati a mano. `tonaca96` è il busto dei monaci bianchi sotto il cappuccio (scapolare, abito ai lati, cappa sulle spalle dove c'è); `busto96(tono)` il pittore comune del busto. `ABITI.domenicano`, `d.domenicano_v`: 0 cappa e cappuccio neri sull'abito bianco, 1 tutto bianco; metà e metà dal nome. `ABITI.cistercense`, `d.cistercense_v`: 0 scapolare e cappuccio neri, 1 certosino tutto bianco (etichetta «carthusian» di Wikidata). `ABITI.cardinale`, `d.cardinale_v`: 0 mozzetta rossa con la croce pettorale al cordone (nati dopo il 1500), 1 mozzetta d'ermellino (nati entro il 1500 o senza anno).
- Abiti minori ridisegnati a mano. `ABITI.mantello`: il manto (`d.secondo`) su una spalla, con l'orlo arrotolato e le pieghe che lo seguono, sopra la tunica (`tunicaT(d)` ne dà il tono); `esporta.py` dà alla tunica sotto i clavi a tutti tranne i nati dopo il 1500 (i martiri dell'Uganda), che hanno il girocollo; la soglia è 1500 perché Wikidata dà a San Pietro l'anno 1260. `ABITI.moderno`, `d.moderno_v`: giacca con i revers sulla camicia bianca, 0 colletto aperto (nati dopo il 1970), 1 con la cravatta. `ABITI.dalmatica`: amitto, due clavi d'oro uniti da una fascia sul petto, una gemma agli incroci. Restano con il disegno di prima, per i ritratti a mano dei famosi: `crociato` (sopravveste), `pelliccia`, `tilma`, `righe`, `nudo`, `hanbok`, `camice`, `coperta`, `sari`, `felpa`.
- `zucchetto6(d, col)`: lo zucchetto, rosso o bianco. È una calotta simmetrica calcolata sulla testa già disegnata: la più bassa che copre la sommità (cranio nudo o capelli) in ogni colonna, 1 px sopra. Sei toni, filetto chiaro sull'orlo, ombra dell'orlo su capelli o cranio. Va tra i `davanti` del copricapo, quindi dopo i capelli.
- `stoffe6(d, mat)`: abiti, copricapi ed extra. Mentre `ritratto96` elenca le parti di `ABITI`, `COPRICAPI` ed `EXTRA96`, `rampa()` restituisce colori segnaposto (rosso `f2`, verde il numero del materiale, blu `10` + tono); l'ultima passata della figura dà a ogni pixel uno dei sei toni del suo materiale (`ORO6`, `BIANCO6`, `NERO6`, `STOFFA6`): bordi in luce e in ombra, pieghe oblique sui panni grandi del busto, volume e bordo in luce sui copricapi, pieghe su veli e cappucci. La mitra ha la fascia con le gemme, le pietre sul titulus e una croce ricamata per lato; il soggolo le pieghe a raggiera. I colori scritti a mano nelle parti (amitto, colletti, cordone) e le scale fatte all'inclusione di `parti96.px.js` (`ORO`, `ARG`, `BIANCO`…) restano come prima.

- `COPRICAPI.mitra` ridisegnata a mano, `d.mitra_v`: 0 preziosa a punta, fascia e titulus con gemme, ai lati il ricamo di `vescovo_v` (croce, losanga, borchie); 1 bassa e semplice, lino bianco con fasce d'oro strette; 2 la corona dei vescovi d'Oriente, cupola d'oro con coste di perle, smalto e croce; 3 alta e tonda, tessuto d'oro chiaro bordato d'oro. `esporta.py` assegna: nati entro il 1000 o senza anno la bassa; dopo il 1000 la corona agli orientali (etichette di Wikidata, esclusi i patriarchi latini); agli altri la preziosa fino al 1500, poi l'alta.
- Attributi tenuti in mano: `mano96` (pugno chiuso su un'asta a x 80-82, nel colore della pelle) e `manica96` (manica larga nel colore della veste); nell'attributo l'ordine è manica, asta, mano. `ATTR_MANO` dice da cosa dipende lo sprite (pelle, veste, variante), per la chiave di `attrSprite`. `ATTRIBUTI96.croce`, `d.croce_v`: 0 di legno; 1 d'oro con estremità svasate, pietra e nodo (papi, cardinali, sovrani); 2 crocifisso con titulus e figura d'avorio (nati dopo il 1500); 3 orientale d'oro a tre bracci (etichette orientali). `ATTRIBUTI96.bastone`, `d.bastone_v`: 0 pomo e due nodi; 1 a tau (nati entro il 600). `ATTRIBUTI96.giglio`, `d.giglio_v`: 0 stelo con tre gigli a tromba; 1 un giglio e due boccioli; 2 scettro d'oro col giglio araldico. `ATTRIBUTI96.palma`, `d.palma_v`: 0 fronda che si apre a ventaglio verso la punta; 1 la stessa con la ghirlanda d'alloro d'oro sopra la mano (ai sovrani mai, hanno già la corona; agli altri uno su tre, dal nome). `ATTRIBUTI96.spada`, `d.spada_v`: 0 medievale, lama con la scanalatura, elsa e pomo d'oro, impugnatura di cuoio; 1 gladio, corto e largo, guardia e pomo di bronzo; 2 sciabola lunga quanto la medievale, curva, dorso piatto e filo lucido, elsa a staffa d'oro. `esporta.py` la lega a `armatura_v`: centurione gladio, uniforme sciabola, il resto (e San Paolo, col mantello) medievale. `ATTRIBUTI96.libro`, `d.libro_v`, senza mano (l'utente: la mano aperta sotto il libro era innaturale), sospeso in basso a destra come il vecchio: 0 codice di cuoio con cornice impressa, nervature e fermagli, colore `d.libro_c` dal nome (rosso, bruno, verde, blu); 1 evangeliario d'oro con croce e gemme (cardinali, vescovi, papi, sovrani); 2 aperto, due pagine scritte (etichette `writer`, `theologian`, `doctor of the church`). Fiori, boccioli e giglio araldico sono disegnati a righe (`FIORE96`, `BOCCIOLO96`, `GIGLIO_ARALDICO`, con `righe96`; i fiori laterali con `ruota96` e `specchio96`). `esporta.py` assegna: scettro ai sovrani d'Occidente (non `regale_v` 1); agli altri due su tre i tre fiori, uno su tre i boccioli, dal nome. `ATTRIBUTI96.pastorale` segue `d.mitra_v`: 1 bastone e gancio aperto tutti di legno; 0 gotico d'oro, riccio a voluta, nodo con pietra; 2 orientale, due teste di serpente rivolte a una croce; 3 moderno, riccio con gattoni e due nodi.
- Abiti ridisegnati a mano (maschera più funzione di tono, come nei provini; la sagoma è `spalle()` in un colore segnaposto): finora `ABITI.vescovo`, con tre varianti scelte dal nome (`vescovo_v` in `esporta.py`): 0 piviale aperto sul camice, con stoloni gemmati e fermaglio; 1 casula con stolone a Y gemmato; 2 casula con colonna d'oro e pallio. La stoffa è seminata di crocette; il ricamo della mitra segue la variante. `panno96` e `rampaMat` servono agli abiti che verranno.

Gli attributi sono ancora a quattro toni. Le figurine speciali S1–S4 e S7 passano da `ritratto96` e hanno il nuovo stile (riviste con l'utente il 2026-11-15: tagli e tunica a clavi fissati in `SPEC`).

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

## Viso e capelli per genere (2026-11-17)

- `VISI`: 0 ovale morbido e 3 mento affusolato (si stringe dolcemente da y 46) per le donne; 2 mento squadrato e 4 mascella larga squadrata per gli uomini, tagliati in piano a y 62, due righe sopra il colletto. 1 non si assegna più.
- Rossore sulle guance solo alle donne (`guance` in `esporta.py`).
- Taglio a paggio (corti 5) solo agli uomini nati fra il 1300 e il 1500; caschetto (piega 5) solo alle donne nate dopo il 1900, ridisegnato senza frangia, con la riga di lato profonda e le punte che girano sotto la mascella.
