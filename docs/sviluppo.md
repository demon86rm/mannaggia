# Sviluppo

Come compilare Mannaggia e come è fatta. La mappa dei componenti è in [`architettura-app.html`](architettura-app.html): scaricala e aprila nel browser.

## Struttura del repository

| Cartella | Contenuto |
| --- | --- |
| `android/app/` | L'app: Kotlin, target SDK 36, minimo Android 7.0 (API 24) |
| `android/store/` | Testi e grafica del Play Store |
| `android/tools/` | Script Python che generano gli asset: lista dei santi, ritratti, suoni |
| `docs/` | Questa guida e la mappa dell'architettura |
| `legacy/` | `mannaggia.sh` e la versione Python, da cui tutto è partito |

## Compilare

Serve un JDK da 17 in su (va bene il JBR di Android Studio) e Gradle 9.8 o superiore: il repo non include `gradlew`.

```sh
cd android
gradle assembleDebug
# APK in app/build/outputs/apk/debug/app-debug.apk
```

Con Android Studio: **File → Open**, scegli la cartella `android`, poi **Build → Build APK(s)**.

La build debug ha il suffisso `.debug` nel package: si installa accanto a quella del Play, col nome «Mannaggia debug».

## Compilare la release

Le release sono firmate con una chiave di upload che non entra mai nel repo.

1. Crea il keystore una volta sola, fuori dal repo, e conservalo con le sue password:

   ```sh
   keytool -genkeypair -v -keystore ~/keystores/mannaggia-upload.jks \
     -alias upload -keyalg RSA -keysize 4096 -validity 10000
   ```

2. Aggiungi a `~/.gradle/gradle.properties`:

   ```properties
   MANNAGGIA_STORE_FILE=/percorso/assoluto/mannaggia-upload.jks
   MANNAGGIA_STORE_PASSWORD=...
   MANNAGGIA_KEY_ALIAS=upload
   MANNAGGIA_KEY_PASSWORD=...
   ```

3. Compila il bundle per Play Console:

   ```sh
   gradle bundleRelease
   # AAB in app/build/outputs/bundle/release/app-release.aab
   ```

Senza queste proprietà la release resta non firmata.

## Asset generati

Questi file non si modificano a mano: si cambia lo script e si rigenera, dalla cartella `android`.

- `app/src/main/assets/santi.txt` e `feste.tsv`: santi, beati e feste da [Wikidata](https://www.wikidata.org) (CC0), con `tools/genera_santi.py`. I nomi sono la chiave di album, preferiti e ritratti: non vanno rigenerati senza motivo.
- `app/src/main/assets/avatar/`: ritratti, cornici e icone in pixel art, con `tools/ritratti/avatar.py`.
- `app/src/main/res/raw/`: coro e jingle, sintetizzati da `tools/suoni/`.

I comandi esatti sono in testa a ciascuno script.

## Note

- La pronuncia usa la sintesi vocale del telefono: serve una voce italiana, altrimenti l'app avvisa e resta solo testo. Le correzioni stanno in `Pronuncia.kt` e cambiano solo ciò che sente la voce, non il testo a schermo.
- L'app non ha il permesso di rete: niente di ciò che aggiungi può parlare con internet.

## Licenza

GPL-3.0, vedi [`LICENSE`](../LICENSE). Privacy: [`PRIVACY.md`](../PRIVACY.md).
