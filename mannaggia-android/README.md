# Mannaggia — Android port

Android port of [`mannaggia.sh`](https://github.com/LegolasTheElf/mannaggia/blob/master/mannaggia.sh) —
the automatic saint-invoker for depressed Veteran Unix Admins.

Tap the button → the app scrapes **santiebeati.it**, picks a random saint,
and shows you `Mannaggia <Saint>!`. Flip the **Pronuncia** toggle to also
hear it spoken via Google Translate TTS in Italian.

## Ways to invoke a saint

- **In-app button** — tap `Mannaggia!` on the main screen.
- **Shake the phone** — sharp movement (>2.7 G) while the app is in the
  foreground triggers a new invocation. 1.5 s cooldown prevents spam.
- **Quick Settings tile** — long-press the notification shade, edit tiles,
  drag **Mannaggia** into your active tiles. One tap from anywhere in the
  system fetches a saint and shows it as a notification.
- **Home screen widget** — long-press the home screen → **Widgets** →
  find **Mannaggia** → drag it somewhere. Tap it to re-roll; the text
  updates in place.

## What was ported

| bash | Kotlin/Android |
| --- | --- |
| `curl` | `HttpURLConnection` |
| `iconv -f ISO-8859-1` | `String(bytes, Charsets.ISO_8859_1)` |
| `awk -F'…'` | `line.split(Regex("…"))` |
| `shuf -n1` | `List<String>.random()` |
| `mplayer <tts url>` | `MediaPlayer` pointed at the same Google TTS URL |
| CLI flags (`--spm`, `--nds`, `--wall`, `--shutdown` …) | **Not ported** — they don't make sense on a phone |

## Requirements

- **Android Studio** Hedgehog (2023.1) or newer — easiest path
- OR: JDK 17 + Android command-line tools + a local `gradle` ≥ 8.5

Target: Android 7.0 (API 24) and up.

## Build — easy path (Android Studio)

1. Unzip the project.
2. **File → Open** → select the `mannaggia-android` folder.
3. Let Gradle sync (first time downloads ~500 MB of Android deps).
4. **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
5. When done, click **locate** in the toast — you'll find
   `app/build/outputs/apk/debug/app-debug.apk`.
6. Copy it to your phone and install (enable "Install unknown apps" first).

## Build — command-line path

From inside the project folder:

```sh
# one-time: generate the gradle wrapper (requires a system gradle ≥ 8.5)
gradle wrapper --gradle-version 8.5

# then every build:
./gradlew assembleDebug
# APK ends up at: app/build/outputs/apk/debug/app-debug.apk
```

For a signed release build:

```sh
./gradlew assembleRelease
# you'll need to configure a keystore in app/build.gradle.kts first
```

## Build — CI path (no local setup)

1. Create a new GitHub repo and push this folder.
2. Add `.github/workflows/build.yml`:

   ```yaml
   name: Build APK
   on: [push, workflow_dispatch]
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-java@v4
           with: { distribution: temurin, java-version: '17' }
         - uses: gradle/actions/setup-gradle@v3
         - run: gradle wrapper --gradle-version 8.5
         - run: ./gradlew assembleDebug
         - uses: actions/upload-artifact@v4
           with:
             name: app-debug
             path: app/build/outputs/apk/debug/app-debug.apk
   ```

3. Push → go to **Actions** tab → download the APK artifact.

## Install on your phone

1. Transfer the APK to the device (USB, email, Drive, whatever).
2. On the phone, tap the APK file.
3. Android will ask you to allow "Install unknown apps" for that source
   (Settings → Apps → Special access → Install unknown apps).
4. Done.

## Known caveats

- **Parsing fragility.** The script (and this port) parse
  `santiebeati.it`'s HTML using very specific `<FONT>` tag patterns.
  If the site ever redesigns, both the original script AND this app
  break. There's a `"Sant'Anonimo"` fallback if nothing is found.
- **Cleartext traffic allowed** (`usesCleartextTraffic="true"`) in case
  the site ever drops to HTTP. It currently serves over HTTPS.
- **Google TTS** is an unofficial, undocumented endpoint. If Google
  changes it (again), audio will silently fail — text-only still works.
- Dropped CLI features: `--audio` (replaced by the in-app toggle),
  `--spm` / `--nds` / `--wall` / `--shutdown` / `--off`
  (nonsensical on a phone).

## License

Same as the upstream script: **GPL-3.0**.
