# Mannaggia

Generatore di "Mannaggia <santo>!". Nella root ci sono lo script bash (`mannaggia.sh`) e quello Python (`mannaggia_py.py`); l'app Android sta in `mannaggia-android/`.

## Build Android
- Il repo non ha `gradlew`: usa Gradle 9.8.1 installato a parte (AGP 9.4.1).
- JDK: il JBR di Android Studio, con `JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"`.
- Su WSL (desktop Windows): `JAVA_HOME=/snap/android-studio/current/jbr`, `ANDROID_HOME=~/Android/Sdk`, Gradle in `~/opt/gradle-9.8.1/bin/gradle`. Il debug keystore di WSL è diverso da quello del Mac: per installare sopra un APK compilato sul Mac va copiato `~/.android/debug.keystore` dal Mac.
- Esegui i comandi da `mannaggia-android/`: `gradle assembleDebug` / `gradle bundleRelease`.
- La firma release legge `MANNAGGIA_STORE_FILE`, `MANNAGGIA_STORE_PASSWORD`, `MANNAGGIA_KEY_ALIAS` e `MANNAGGIA_KEY_PASSWORD` da `~/.gradle/gradle.properties`. Mai metterli nel repo.
- Package `io.github.demon86rm.mannaggia`, target/compile SDK 36, min 24.

## Git
- Prima di ogni commit controlla `git status`: non vanno committati `build/`, `.gradle/`, `.kotlin/`, `local.properties` o `*.apk`.
- L'APK si distribuisce solo con le GitHub Releases (asset `mannaggia.apk`), mai nel repo.
- Le funzioni nuove si sviluppano su un branch; il merge su `main` si fa solo dopo che l'utente le ha provate.

## Lista santi
- `app/src/main/assets/santi.txt` è generato da `tools/genera_santi.py` (Wikidata, CC0): non modificarlo a mano.
- Rigenera con `python3 -I tools/genera_santi.py > app/src/main/assets/santi.txt`.
- Dopo ogni modifica ai filtri (santo/beato, religione) controlla a campione prefissi, numero di righe ed esclusioni.
- `app/src/main/assets/feste.tsv` (santo del giorno) è generato dallo stesso script, solo per i santi già in `santi.txt`: `python3 -I tools/genera_santi.py --feste app/src/main/assets/feste.tsv --solo app/src/main/assets/santi.txt`. Non modificarlo a mano. Le correzioni (feste mancanti su Wikidata, santo del giorno imposto) vanno in `EXTRA_FEASTS` e `SAINT_OF_DAY` nello script.
- `app/src/main/assets/avatar/` (ritratti pixel art dell'album, cornice animata, cornici speciali di alcuni leggendari elencate in `cornici.txt` e definite in `CORNICI`, come le fiamme di Giovanna d'Arco, timbro "Nuova!", pulsanti "Mannaggia!", "Opzioni" e "Info", segnalibro dei preferiti, logo e titolo dello splash, `leggendari.txt`) è generato da `tools/ritratti/avatar.py`: `python tools/ritratti/avatar.py --tutti --app app/src/main/assets/avatar --cache tools/ritratti/tratti_wikidata.json` (venv `~/venv/ritratti` con pillow). Non modificarlo a mano: l'iconografia dei santi famosi sta in `FAMOSI`, le regole per gli altri in `regole()`. Va rigenerato se cambia `santi.txt`.
- `app/src/main/res/raw/coro.ogg` (coro dei leggendari, ~3 s) è sintetizzato da `tools/suoni/coro.py`: `python tools/suoni/coro.py --out app/src/main/res/raw/coro.ogg` (venv `~/venv/ritratti`, ffmpeg). Nessun campione registrato: è originale, GPL.
- `app/src/main/res/raw/trofeo.ogg` (jingle dei trofei) è sintetizzato da `tools/suoni/jingle.py`: `python tools/suoni/jingle.py --out app/src/main/res/raw/trofeo.ogg`.
- Il testo della frase va impostato con `PhraseEffects.setText()`, non con `txtResult.text`: l'effetto Terminale lo riscrive mentre lo batte.
- Le correzioni di pronuncia del TTS del telefono stanno in `Pronuncia.kt`: i numeri romani diventano ordinali, le parole lette male vanno in `PAROLE`. Cambia solo il testo passato alla voce, non quello a schermo. Per provare un caso, nella build debug: `adb shell am start -n io.github.demon86rm.mannaggia.debug/com.mannaggia.app.MainActivity -e santo "<santo>"` (la build debug ha il suffisso `.debug` e si installa accanto a quella del Play), poi `adb logcat -s Pronuncia:D`.
- Trofei e ricompense sono in `Trofei.kt` (`TUTTI`). Le ricompense di tipo colore, carattere ed effetto usano gli stessi valori di `arrays.xml`. Le figurine speciali stanno nella tabella `SPECIALI` di `avatar.py`, nello stesso ordine delle ricompense `FIGURINA`, che corrisponde ai numeri S1…S6.
- Non rigenerare `santi.txt` senza motivo: i nomi sono la chiave dei file audio (`sha1`), dei ritratti, della cache `tratti_wikidata.json`, dell'album e dei preferiti.
- Per correggere solo i titoli dei nomi (es. "San Saint Amun" → "Sant'Amun") senza ripescare da Wikidata, che nel tempo cambia: `python3 -I tools/genera_santi.py --correggi app/src/main/assets/santi.txt > nuovo.txt`. Le coppie vecchio → nuovo che stampa vanno in `Rinominati.kt` (migrazione di album e preferiti) e nelle chiavi di `tratti_wikidata.json`; poi rigenera feste e ritratti e cancella i ritratti dei nomi vecchi.

## Doni (link)
- I link dei doni (`Dono.kt`) sono App Link verificati da `https://demon86rm.github.io/.well-known/assetlinks.json`, nel repo `demon86rm/demon86rm.github.io`, che contiene anche la pagina di ripiego `mannaggia/dono/`. Ci sono le impronte SHA-256 della firma di Play, della chiave di upload e della chiave di debug di WSL (package `.debug`): se cambia una chiave, va aggiornato quel file.
- Il link è input non fidato: si accettano solo nomi di `santi.txt`. Il santo sta nel frammento `#` (il pulsante della pagina usa la query, perché `intent://` occupa il frammento).
- Non rinominare l'account GitHub: il dominio dei link è `demon86rm.github.io`.

## Shell
- zsh: nei comandi da incollare niente `!` tra virgolette doppie (history expansion). Usa le virgolette singole e `'\''` per gli apostrofi.
- Metti tra virgolette singole i glob negli argomenti, ad es. `--include='*.kt'`.

## Play Store
- Pubblicazione gratuita, senza pubblicità.
- Le licenze accettabili per dipendenze e asset sono Apache-2.0, MIT, BSD, CC0, CC-BY e GPL. Niente licenze NC.
- Solo per i font è ammessa anche la SIL OFL 1.1: il file `.ttf` va in `res/font/` senza modifiche, la licenza originale in `assets/licenze/OFL-<font>.txt` e i crediti in `about_text`.
