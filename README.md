<p align="center">
  <img src="android/store/feature-graphic.png" alt="Mannaggia" width="640">
</p>

<h1 align="center">Mannaggia</h1>

<p align="center">
  <b>Il tool apotropaico e imprecante che vi accompagnerà nei momenti più bui.</b><br>
  Un santo a caso, con un tocco. Per Android.
</p>

<p align="center">
  <a href="https://github.com/demon86rm/mannaggia/releases/latest"><img src="https://img.shields.io/github/v/release/demon86rm/mannaggia?label=versione" alt="Ultima versione"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licenza-GPLv3-blue" alt="Licenza GPLv3"></a>
  <a href="https://ko-fi.com/demon86rm"><img src="https://img.shields.io/badge/Ko--fi-offrimi%20un%20caff%C3%A8-ff5e5b?logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
</p>

> 🇬🇧 **In short:** Mannaggia is a free, open-source, ad-free Android app that curses on your behalf by summoning a random Catholic saint ("Mannaggia San Pietro!") whenever things go wrong. It is the mobile heir of `mannaggia.sh`, a cult script among Italian sysadmins. It works fully offline, needs no network permission and collects no data. The app is in Italian. Want to help it reach Google Play? [Join the closed test](https://forms.gle/wHWbGGDAmRQnpswL7).

## Scarica

**[⬇️ Scarica l'APK](https://github.com/demon86rm/mannaggia/releases/latest/download/mannaggia.apk)** · [tutte le versioni](https://github.com/demon86rm/mannaggia/releases)

**Sul Google Play Store manca poco**: Google chiede un test chiuso con almeno 12 tester per 14 giorni. Hai un telefono Android e un account Google? **[Diventa tester](https://forms.gle/wHWbGGDAmRQnpswL7)**: ti aggiungo alla lista e ti scrivo quando puoi installarla.

## Cosa fa

Server giù? Deploy del venerdì andato male? Mannaggia invoca per te uno degli oltre **5000 santi e beati** del calendario.

- **Pulsante "Mannaggia!"**, oppure **scuoti il telefono** con l'app aperta.
- **Widget** per la schermata Home e **riquadro nelle Impostazioni rapide**, per imprecare da qualunque schermata.
- **Santo del giorno**: l'icona col calendario in basso a destra invoca il santo festeggiato oggi, una volta al giorno.
- **Album dei santi**: ogni santo invocato diventa una figurina in pixel art, disegnata a mano col suo abito e i suoi attributi. I 50 più famosi sono leggendari, con una cornice d'oro che scintilla. Riuscirai a trovarli tutti?
- **Trofei segreti**: certi gesti, orari e costanze vengono premiati. Cosa sblocca cosa non lo diciamo: colori, caratteri, effetti animati e qualche figurina che nel calendario non troverai.
- **Pronuncia** della frase con la sintesi vocale del telefono.
- **Stile a piacere**: tema chiaro o scuro, carattere, colore ed effetto, con anteprima dal vivo.
- **Rispetta la tua privacy**: funziona offline, non chiede permessi di rete, niente pubblicità, account o tracciamento ([informativa](PRIVACY.md)).

## Prossimamente

- 🎙️ **Voce "Mannaggia"**: un pacchetto vocale opzionale con voce neurale, in alternativa alla sintesi del telefono.

La lista aggiornata è anche nell'app, in Info → Prossimamente.

## Contribuisci

Mannaggia è gratuita e senza sponsor, e così resterà. Puoi aiutarla così:

- **[Segnala un problema o proponi un'idea](https://github.com/demon86rm/mannaggia/issues/new/choose)**, anche dall'app (Opzioni → Progetto).
- **Fai fork e apri una pull request**: santi dimenticati, achievement da inventare, correzioni.
- **Curioso di come è fatta?** La mappa dei componenti è in [`docs/architettura-app.html`](docs/architettura-app.html): scaricala e aprila nel browser. Ogni blocco porta alle righe di codice da cui viene.
- **[Offrimi un caffè su Ko-fi](https://ko-fi.com/demon86rm)**: aiuta a coprire i costi (account sviluppatore, ore di GPU per la voce) o è semplicemente un grazie.

## Compilare da sorgente

L'app sta in [`android/`](android): Kotlin, Android SDK 36, minimo Android 7.0.

```sh
cd android
gradle assembleDebug
```

Servono Gradle 9.8 o superiore (il repo non include `gradlew`) e un JDK 17 o superiore, per esempio il JBR di Android Studio. L'elenco dei santi (`app/src/main/assets/santi.txt`) è generato da Wikidata con [`tools/genera_santi.py`](android/tools/genera_santi.py).

## Le origini

Tutto è cominciato con `incazzatore.sh` di Alexiobash, poi ampliato e riscritto da Pietro "Legolas" Suffritti in **[`mannaggia.sh`](https://github.com/LegolasTheElf/mannaggia)**: uno script bash che invoca i santi al posto vostro, nato nel gruppo Facebook *Veteran Unix Admins*. Questo repository è un fork di quel progetto. Lo script è ancora qui, insieme a una versione Python con interfaccia grafica, e l'app Android ne è l'evoluzione.

<details>
<summary><b>mannaggia.sh</b>: lo script originale</summary>

Lo script nomina tutti i santi per voi quando vi sentite depressi.

Prerequisiti: `mplayer`, per il parametro `--audio`.

Parametri da riga di comando:
- `--audio`: usa mplayer per pronunciare i santi
- `--spm <n>`: numero di santi al minuto
- `--wall`: invia l'output a tutte le console. Attenzione: se non siete root o sudoers, disattivate il flag `-n`.
- `--shutdown`: se siete root, spegne il computer dopo aver finito di invocare i santi (dipende da `--nds`)
- `--off`: equivale a `--nds 1 --shutdown`

</details>

<details>
<summary><b>mannaggia_py.py</b>: la versione Python con interfaccia grafica</summary>

Conversione di `mannaggia.sh` in un'applicazione Python con Tkinter. Requisiti, installazione e uso sono in [`legacy/readme-py.md`](legacy/readme-py.md).

</details>

## Crediti

- **Idea originale**: Alexiobash, dallo script `incazzatore.sh`
- **Ampliata, riscritta e mantenuta da**: Pietro "Legolas" Suffritti, fino a `mannaggia.sh` rel 0.2
- **Collaboratori**: Enrico "Henryx" Bianchi, Alessandro "Aleskandro" Di Stefano, Davide "kk0nrad" Corrado
- **Patcher e contributori**: Marco Placidi, Maurizio "Tannoiser" Lemmo, Matteo Panella, Mattia Munari, Paolo Fabbri
- **App Android**: Demon86RM (Marco Placidi)
- **Elenco dei santi**: [Wikidata](https://www.wikidata.org), dati CC0
- **Grazie a**: il gruppo Facebook *Veteran Unix Admins*

## Licenza

Software libero, rilasciato sotto [GNU GPL v3](LICENSE) come lo script originale.
