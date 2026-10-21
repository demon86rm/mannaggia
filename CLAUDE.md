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

## Shell
- zsh: nei comandi da incollare niente `!` tra virgolette doppie (history expansion). Usa le virgolette singole e `'\''` per gli apostrofi.
- Metti tra virgolette singole i glob negli argomenti, ad es. `--include='*.kt'`.

## Play Store
- Pubblicazione gratuita, senza pubblicità.
- Le licenze accettabili per dipendenze e asset sono Apache-2.0, MIT, BSD, CC0, CC-BY e GPL. Niente licenze NC.
