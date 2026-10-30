package com.mannaggia.app

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorManager
import android.os.Build
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.TooltipCompat
import androidx.core.content.ContextCompat
import androidx.core.view.drawToBitmap
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import com.mannaggia.app.databinding.ActivityMainBinding
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull
import java.util.Locale

/**
 * Main screen: tap the button (or shake the phone) to invoke a saint.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var tts: TextToSpeech? = null
    private var ttsReady = false
    /** Completed by the TTS engine when the current phrase has been spoken. */
    private var speechDone: CompletableDeferred<Unit>? = null

    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private lateinit var shakeDetector: ShakeDetector
    private var currentJob: Job? = null
    private var themeTextColor = 0
    private var saintOfDay: String? = null
    private lateinit var cardSlot: CardSlot
    private lateinit var trophyPop: TrophyPop

    /** Whatever the answer, then the "what's new" popup (never on top of the permission dialog). */
    private val requestNotifPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { showNewsIfUpdated() }

    /** Opened by a gift link: no "what's new" popup this time (it waits for the next launch). */
    private var giftLaunch = false
    /**
     * The launch intent's gift link or debug saint has been handled. Saved across recreation:
     * right after a cold start the activity can be recreated, and checking only for a null
     * savedInstanceState lost the gift.
     */
    private var launchHandled = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        // Pixel-art splash at start, until it has been seen once: if the activity is recreated
        // mid-splash (a configuration change right after the first start) it starts again; after
        // that, rotations and theme changes don't show it. The notification permission is asked
        // after it, so the dialog doesn't cover it.
        splashDone = savedInstanceState?.getBoolean(KEY_SPLASH_DONE) == true
        // A gift link (Dono) opened the app: its card appears once the splash is gone.
        launchHandled = savedInstanceState?.getBoolean(KEY_LAUNCH_HANDLED) == true
        val gift = if (launchHandled) null else intent.data
        giftLaunch = gift != null
        if (!splashDone) Splash.show(this, afterRecreation = savedInstanceState != null) {
            splashDone = true
            askForNotificationPermissionIfNeeded()
            receiveGift(gift)
        } else {
            askForNotificationPermissionIfNeeded()
            receiveGift(gift)
        }
        // Debug builds only: start with a given saint, e.g.
        // adb shell am start -n io.github.demon86rm.mannaggia.debug/com.mannaggia.app.MainActivity -e santo "San Carlo I di Fiandra"
        // Debug builds only: pretend today is a given day for Retro, e.g. -e data 10-31.
        if (BuildConfig.DEBUG) intent.getStringExtra("data")?.let { Retro.debugOggi = it }
        if (BuildConfig.DEBUG && !launchHandled) intent.getStringExtra("santo")?.let { santo ->
            binding.root.post { launchHandled = true; invokeSaint(Trofei.Fonte.PULSANTE) { santo } }
        }
        applySystemBarInsets()

        binding.btnMannaggia.setOnClickListener { invokeSaint(Trofei.Fonte.PULSANTE) }
        binding.btnSaintOfDay.setOnClickListener {
            val saint = saintOfDay ?: return@setOnClickListener
            // One saint-of-the-day invocation a day; a busy tap doesn't use it up.
            if (Prefs.saintOfDayUsedToday(this) || !invokeSaint(Trofei.Fonte.CALENDARIO) { saint }) return@setOnClickListener
            Prefs.markSaintOfDayUsed(this)
            showSaintOfDay(saint)
        }
        binding.btnInfo.setOnClickListener { startActivity(Intent(this, InfoActivity::class.java)) }
        binding.btnShare.setOnClickListener { shareInvocation() }
        binding.txtResult.setOnLongClickListener { copyPhrase(); true }
        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        binding.btnAlbum.setOnClickListener {
            cardSlot.cancel()
            startActivity(Intent(this, AlbumActivity::class.java))
        }
        cardSlot = CardSlot(
            binding.cardSlot, binding.cardFit, binding.imgStamp, binding.imgGlow, binding.cardFx,
            binding.btnAlbum, lifecycleScope,
            root = binding.root, topLimit = binding.btnSettings, phrase = binding.txtResult, button = binding.btnMannaggia,
            flip = binding.btnFlip,
        ) { saint, back ->
            // San Giovanni Battista's secret back has its own phrase; the front gets his again.
            // Each turn says it, when Pronuncia is on.
            lifecycleScope.launch {
                val phrase = if (back) Retro.FRASE else Mannaggia.phraseOf(this@MainActivity, saint)
                PhraseEffects.setText(binding.txtResult, phrase)
                shown(if (back) Retro.NOME else saint, phrase)
                if (Prefs.ttsEnabled(this@MainActivity)) speakAndWait(phrase)
            }
        }
        // Trophy banners wait while a legendary card (with its choir) is on stage.
        trophyPop = TrophyPop(binding.trophyPop, lifecycleScope) { cardSlot.isHolding }
        binding.btnTrophies.setOnClickListener {
            startActivity(Intent(this, TrofeiActivity::class.java))
        }
        if (BuildConfig.DEBUG) {
            // Debug builds only: long-press the cup to unlock the next trophy.
            binding.btnTrophies.setOnLongClickListener {
                if (Trofei.debugUnlockNext(this)) announceTrophies()
                true
            }
            // Debug builds only: long-press the binder to preview the legendary animation, in turn
            // with the fire frame (Santa Giovanna d'Arco) and the gold one (San Pietro).
            binding.btnAlbum.setOnLongClickListener {
                val saint = DEBUG_LEGENDS[debugLegend++ % DEBUG_LEGENDS.size]
                lifecycleScope.launch {
                    val n = Avatars.number(this@MainActivity, saint)
                    cardSlot.show(saint, n, isNew = true, legendary = true, special = false, animate = true)
                }
                true
            }
            // Debug builds only: long-press the ribbon to unlock San Giovanni Battista's back (with
            // its hint) and draw him, so the flip icon and the turn can be tried at once.
            binding.btnMannaggia.setOnLongClickListener {
                Trofei.debugUnlockRetro(this)
                invokeSaint(Trofei.Fonte.PULSANTE) { Retro.FRONTE }
                true
            }
        }
        lifecycleScope.launch {
            binding.btnMannaggia.setImageDrawable(Avatars.ribbonButton(this@MainActivity, "mannaggia"))
            binding.btnSettings.setImageDrawable(Avatars.ribbonButton(this@MainActivity, "opzioni"))
            binding.btnInfo.setImageDrawable(Avatars.ribbonButton(this@MainActivity, "info"))
            binding.btnAlbum.setImageDrawable(Avatars.binder(this@MainActivity))
            binding.btnTrophies.setImageDrawable(Avatars.cup(this@MainActivity))
            binding.btnShare.setImageDrawable(Avatars.shareIcon(this@MainActivity))
            binding.btnSaintOfDay.setImageDrawable(Avatars.saintOfDayIcon(this@MainActivity))
            binding.btnSaintOfDay.visibility = View.VISIBLE
        }
        themeTextColor = binding.txtResult.currentTextColor

        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        shakeDetector = ShakeDetector {
            Trofei.scossa(this)
            if (!invokeSaint(Trofei.Fonte.SCUOTIMENTO)) announceTrophies()  // a busy shake can still unlock
        }

        initTts()

    }

    /** The engine the voice was started with: when Options change it, the voice restarts (onResume). */
    private var ttsEngine: String? = null

    private fun initTts() {
        tts?.shutdown()
        ttsReady = false
        ttsEngine = Prefs.ttsEngine(this)
        tts = TextToSpeech(this, { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.ITALIAN)
                ttsReady = result != TextToSpeech.LANG_MISSING_DATA &&
                    result != TextToSpeech.LANG_NOT_SUPPORTED
                tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(utteranceId: String?) = Unit
                    override fun onDone(utteranceId: String?) { speechDone?.complete(Unit) }
                    @Deprecated("Deprecated in Java")
                    override fun onError(utteranceId: String?) { speechDone?.complete(Unit) }
                    override fun onError(utteranceId: String?, errorCode: Int) { speechDone?.complete(Unit) }
                    override fun onStop(utteranceId: String?, interrupted: Boolean) { speechDone?.complete(Unit) }
                })
            }
        }, ttsEngine)
    }

    override fun onResume() {
        super.onResume()
        // Options may have changed in SettingsActivity.
        Prefs.applyPhraseStyle(binding.txtResult, themeTextColor)
        if (Prefs.ttsEngine(this) != ttsEngine) initTts()
        // Refreshed on every resume, so it is right even after midnight.
        lifecycleScope.launch { showSaintOfDay(runCatching { Mannaggia.saintOfDay(this@MainActivity) }.getOrNull()) }
        // Trophies unlocked elsewhere (widget, tile, options, album) are announced here.
        announceTrophies()
        if (Prefs.shakeEnabled(this)) {
            accelerometer?.let {
                sensorManager.registerListener(shakeDetector, it, SensorManager.SENSOR_DELAY_UI)
            }
        }
    }

    override fun onPause() {
        super.onPause()
        sensorManager.unregisterListener(shakeDetector)
        cardSlot.cancel()
        PhraseEffects.stop(binding.txtResult)  // restarted by applyPhraseStyle in onResume
    }

    /** Show the banners of the trophies unlocked since the last call. */
    private fun announceTrophies() {
        val unlocked = Trofei.takePending(this)
        trophyPop.show(unlocked)
        if (Trofei.takeRetroNotice(this)) Toast.makeText(this, R.string.retro_notice, Toast.LENGTH_LONG).show()
        // A special card won with a trophy is "unwrapped": shown and spoken right away,
        // after the phrase in progress if there is one (see invokeSaint).
        newSpecials += unlocked.filter { it.ricompensa.tipo == Trofei.Tipo.FIGURINA }.map { it.ricompensa.valore }
        if (newSpecials.isNotEmpty() && currentJob?.isActive != true) {
            currentJob = lifecycleScope.launch { unwrapNewSpecials() }
        }
    }

    /** Special cards just won, waiting to be unwrapped. */
    private val newSpecials = ArrayDeque<String>()

    /**
     * Show each special card just won as a new card, with its invocation as the phrase,
     * spoken when Pronuncia is on. Runs inside the invocation job, so nothing else starts
     * meanwhile.
     */
    private suspend fun unwrapNewSpecials() {
        while (newSpecials.isNotEmpty()) {
            val special = newSpecials.removeFirst()
            delay(UNWRAP_PAUSE_MS)
            binding.btnMannaggia.isEnabled = false
            cardSlot.show(special, Trofei.specialNumber(special), isNew = true, legendary = false,
                special = true, animate = Prefs.cardAnimEnabled(this))
            val phrase = Mannaggia.phraseOf(this@MainActivity, special)
            PhraseEffects.setText(binding.txtResult, phrase)
            shown(special, phrase)
            if (Prefs.ttsEnabled(this)) speakAndWait(phrase) else delay(SHOW_ONLY_COOLDOWN_MS)
            binding.btnMannaggia.isEnabled = true
        }
    }

    /**
     * Show the card of [saint] under the phrase: new ones pop in with the "NUOVA!" stamp
     * and fly into the binder, the others just appear. Returns true for a new legendary
     * saint (its card comes with the choir).
     */
    private suspend fun showCard(saint: String, isNew: Boolean): Boolean {
        val special = Trofei.isSpecial(saint)
        val legendary = !special && Avatars.isLegendary(this, saint)
        val number = if (special) Trofei.specialNumber(saint) else Avatars.number(this, saint)
        cardSlot.show(saint, number, isNew, legendary, special, Prefs.cardAnimEnabled(this))
        return isNew && legendary
    }

    /** The saint and phrase on screen, for sharing and copying (null while an invocation starts). */
    private var shownSaint: String? = null
    private var shownPhrase: String? = null

    private fun shown(saint: String?, phrase: String?) {
        shownSaint = saint
        shownPhrase = phrase
        binding.btnShare.visibility = if (phrase != null) View.VISIBLE else View.INVISIBLE
    }

    /** Share the card on screen (portrait and frame, without the bookmark) with the phrase. */
    private fun shareInvocation() {
        val saint = shownSaint ?: return
        val phrase = shownPhrase ?: return
        val bookmark = binding.cardSlot.btnBookmark
        val was = bookmark.visibility
        bookmark.visibility = View.INVISIBLE
        val image = binding.cardSlot.cardImage.drawToBitmap()
        bookmark.visibility = was
        Condividi.card(this, saint, image, phrase)
    }

    /** Long press on the phrase: copy it (Android 13+ confirms on its own). */
    private fun copyPhrase() {
        val phrase = shownPhrase ?: return
        getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("Mannaggia", phrase))
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) Toast.makeText(this, R.string.phrase_copied, Toast.LENGTH_SHORT).show()
    }

    private fun showSaintOfDay(saint: String?) {
        saintOfDay = saint
        val used = Prefs.saintOfDayUsedToday(this)
        val available = saint != null && !used
        val btn = binding.btnSaintOfDay
        // "Ghost" when there is no saint today or today's invocation was used.
        btn.alpha = if (available) 1f else GHOST_ALPHA
        btn.isEnabled = available
        btn.isClickable = available
        val label = when {
            saint == null -> getString(R.string.saint_of_day_none)
            used -> getString(R.string.saint_of_day_used, saint)
            else -> getString(R.string.saint_of_day, saint)
        }
        btn.contentDescription = label
        TooltipCompat.setTooltipText(btn, label)
    }

    /** Show (and optionally speak) the phrase for the saint returned by [pick]: random by default. */
    /** Returns false (and does nothing) while a previous invocation is still in flight. */
    /** Show the card of a gift link, if [uri] is a valid one (invalid links are ignored). */
    private fun receiveGift(uri: Uri?) {
        if (uri == null) return
        launchHandled = true
        lifecycleScope.launch {
            val saint = Dono.parse(this@MainActivity, uri) ?: return@launch
            invokeSaint(gift = true) { saint }
        }
    }

    /** [gift]: the saint comes from a gift link, which is not an invocation for the trophies. */
    private fun invokeSaint(
        fonte: Trofei.Fonte = Trofei.Fonte.PULSANTE,
        gift: Boolean = false,
        pick: suspend () -> String = { Mannaggia.randomSaint(this) },
    ): Boolean {
        // Ignore button, shake and saint-of-the-day triggers until the previous phrase
        // has been spoken (or shown for a moment): the job stays active until then.
        if (currentJob?.isActive == true) return false
        // A legendary card is waiting for its tap: no new curse on top of it.
        if (cardSlot.isHolding) return false

        binding.progress.visibility = View.VISIBLE
        binding.btnMannaggia.isEnabled = false
        PhraseEffects.setText(binding.txtResult, "")
        shown(null, null)

        currentJob = lifecycleScope.launch {
            val result = runCatching { pick() }
            binding.progress.visibility = View.GONE
            result.fold(
                onSuccess = { saint ->
                    // Special cards live in the trophies, not in the album file.
                    val isNew = !Trofei.isSpecial(saint) &&
                        runCatching { Album.record(this@MainActivity, saint) }.getOrDefault(false)
                    val choir = showCard(saint, isNew)
                    runCatching {
                        if (gift) Trofei.dono(this@MainActivity, saint, isNew)
                        else Trofei.invocazione(this@MainActivity, fonte, saint, isNew)
                    }
                    announceTrophies()
                    val phrase = Mannaggia.phraseOf(this@MainActivity, saint)
                    PhraseEffects.setText(binding.txtResult, phrase)
                    shown(saint, phrase)
                    if (Prefs.ttsEnabled(this@MainActivity)) {
                        if (choir) cardSlot.awaitChoir(CHOIR_MAX_WAIT_MS)  // first the choir, then the voice
                        speakAndWait(phrase)
                    } else {
                        delay(SHOW_ONLY_COOLDOWN_MS)
                    }
                },
                onFailure = { e -> PhraseEffects.setText(binding.txtResult, "Errore: ${e.message}") }
            )
            binding.btnMannaggia.isEnabled = true
            unwrapNewSpecials()   // special cards won with this invocation
        }
        return true
    }

    // ---------------------------------------------------------------
    // System text-to-speech (offline, uses the device's Italian voice)
    // ---------------------------------------------------------------

    /** Speak [text] and suspend until it has been spoken (or [SPEECH_TIMEOUT_MS] at most). */
    private suspend fun speakAndWait(text: String) {
        if (BuildConfig.DEBUG) Log.d("Pronuncia", "$text -> ${Pronuncia.perVoce(this, text)}")
        if (!ttsReady) {
            Toast.makeText(this, R.string.tts_unavailable, Toast.LENGTH_SHORT).show()
            return
        }
        val done = CompletableDeferred<Unit>().also { speechDone = it }
        if (tts?.speak(Pronuncia.perVoce(this, text), TextToSpeech.QUEUE_FLUSH, null, "mannaggia") != TextToSpeech.SUCCESS) return
        // Safety net: some engines never report the end of an utterance.
        withTimeoutOrNull(SPEECH_TIMEOUT_MS) { done.await() }
    }

    // ---------------------------------------------------------------
    // Edge-to-edge (enforced from targetSdk 35) and the "Info" dialog
    // ---------------------------------------------------------------

    /** Keep content clear of the status and navigation bars, on top of the layout padding. */
    private fun applySystemBarInsets() {
        val root = binding.root
        val left = root.paddingLeft
        val top = root.paddingTop
        val right = root.paddingRight
        val bottom = root.paddingBottom
        ViewCompat.setOnApplyWindowInsetsListener(root) { view, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
            )
            view.setPadding(left + bars.left, top + bars.top, right + bars.right, bottom + bars.bottom)
            insets
        }
    }

    /** License, source link and credits (GPLv3 asks for them to be visible). */
    /** Asks for the notification permission if needed; otherwise goes on to the "what's new" popup. */
    private fun askForNotificationPermissionIfNeeded() {
        val granted = Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU || ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
        if (granted) showNewsIfUpdated() else requestNotifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
    }

    /**
     * After an update, once: the changelog block of this version, with "Tutte le novità" to Info.
     * A fresh install only records the version; testers coming from 2.1.0 have no record yet,
     * so the install times tell the two apart.
     */
    private fun showNewsIfUpdated() {
        if (giftLaunch || isFinishing) return
        val seen = Prefs.seenVersion(this)
        if (seen >= BuildConfig.VERSION_CODE) return
        val info = packageManager.getPackageInfo(packageName, 0)
        val block = Novita.blocco(this, BuildConfig.VERSION_NAME)
        Prefs.setSeenVersion(this, BuildConfig.VERSION_CODE)
        if ((seen < 0 && info.firstInstallTime == info.lastUpdateTime) || block == null) return
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.news_title, BuildConfig.VERSION_NAME.substringBefore('-')))
            .setMessage(block.joinToString("\n"))
            .setPositiveButton(android.R.string.ok, null)
            .setNeutralButton(R.string.news_all) { _, _ -> startActivity(Intent(this, InfoActivity::class.java)) }
            .show()
    }

    companion object {
        /** Debug: the legendary cards previewed in turn by a long press on the binder. */
        private val DEBUG_LEGENDS = listOf("Santa Giovanna d'Arco", "San Pietro")
        /** Without speech, how long a phrase stays before the next one can be invoked. */
        private const val SHOW_ONLY_COOLDOWN_MS = 600L
        private const val GHOST_ALPHA = 0.5f
        /** Safety cap on waiting for the choir before speaking (it lasts about 3 s). */
        private const val CHOIR_MAX_WAIT_MS = 4_000L
        private const val SPEECH_TIMEOUT_MS = 15_000L
        private const val KEY_SPLASH_DONE = "splash_done"
        private const val KEY_LAUNCH_HANDLED = "launch_handled"
        /** Pause between the invoked saint and the special card it won, so both get seen. */
        private const val UNWRAP_PAUSE_MS = 1_200L
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putBoolean(KEY_SPLASH_DONE, splashDone)
        outState.putBoolean(KEY_LAUNCH_HANDLED, launchHandled)
    }

    /** True once the splash has been shown to the end (kept across recreations). */
    private var splashDone = false
    private var debugLegend = 0

    override fun onDestroy() {
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }
}
