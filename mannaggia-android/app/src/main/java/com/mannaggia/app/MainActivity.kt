package com.mannaggia.app

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorManager
import android.os.Build
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.text.method.LinkMovementMethod
import android.text.util.Linkify
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.TooltipCompat
import androidx.core.content.ContextCompat
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

    private val requestNotifPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { /* no-op */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        applySystemBarInsets()

        binding.btnMannaggia.setOnClickListener { invokeSaint(Trofei.Fonte.PULSANTE) }
        binding.btnSaintOfDay.setOnClickListener {
            val saint = saintOfDay ?: return@setOnClickListener
            // One saint-of-the-day invocation a day; a busy tap doesn't use it up.
            if (Prefs.saintOfDayUsedToday(this) || !invokeSaint(Trofei.Fonte.CALENDARIO) { saint }) return@setOnClickListener
            Prefs.markSaintOfDayUsed(this)
            showSaintOfDay(saint)
        }
        binding.btnInfo.setOnClickListener { showAbout() }
        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        binding.btnAlbum.setOnClickListener {
            cardSlot.cancel()
            startActivity(Intent(this, AlbumActivity::class.java))
        }
        cardSlot = CardSlot(
            binding.cardSlot, binding.cardFit, binding.imgStamp, binding.imgGlow, binding.cardFx,
            binding.btnAlbum, lifecycleScope, above = binding.txtResult, below = binding.btnMannaggia,
        )
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
            // Debug builds only: long-press the binder to preview the legendary animation.
            binding.btnAlbum.setOnLongClickListener {
                lifecycleScope.launch {
                    val n = Avatars.number(this@MainActivity, "San Pietro")
                    cardSlot.show("San Pietro", n, isNew = true, legendary = true, special = false, animate = true)
                }
                true
            }
        }
        lifecycleScope.launch {
            binding.btnMannaggia.setImageDrawable(Avatars.ribbonButton(this@MainActivity, "mannaggia"))
            binding.btnSettings.setImageDrawable(Avatars.ribbonButton(this@MainActivity, "opzioni"))
            binding.btnInfo.setImageDrawable(Avatars.ribbonButton(this@MainActivity, "info"))
            binding.btnAlbum.setImageDrawable(Avatars.binder(this@MainActivity))
            binding.btnTrophies.setImageDrawable(Avatars.cup(this@MainActivity))
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

        tts = TextToSpeech(this) { status ->
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
        }

        askForNotificationPermissionIfNeeded()
    }

    override fun onResume() {
        super.onResume()
        // Options may have changed in SettingsActivity.
        Prefs.applyPhraseStyle(binding.txtResult, themeTextColor)
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
        trophyPop.show(Trofei.takePending(this))
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
    private fun invokeSaint(
        fonte: Trofei.Fonte = Trofei.Fonte.PULSANTE,
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

        currentJob = lifecycleScope.launch {
            val result = runCatching { pick() }
            binding.progress.visibility = View.GONE
            result.fold(
                onSuccess = { saint ->
                    // Special cards live in the trophies, not in the album file.
                    val isNew = !Trofei.isSpecial(saint) &&
                        runCatching { Album.record(this@MainActivity, saint) }.getOrDefault(false)
                    val choir = showCard(saint, isNew)
                    runCatching { Trofei.invocazione(this@MainActivity, fonte, saint, isNew) }
                    announceTrophies()
                    val phrase = Mannaggia.phraseOf(saint)
                    PhraseEffects.setText(binding.txtResult, phrase)
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
        }
        return true
    }

    // ---------------------------------------------------------------
    // System text-to-speech (offline, uses the device's Italian voice)
    // ---------------------------------------------------------------

    /** Speak [text] and suspend until it has been spoken (or [SPEECH_TIMEOUT_MS] at most). */
    private suspend fun speakAndWait(text: String) {
        if (!ttsReady) {
            Toast.makeText(this, R.string.tts_unavailable, Toast.LENGTH_SHORT).show()
            return
        }
        val done = CompletableDeferred<Unit>().also { speechDone = it }
        if (tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "mannaggia") != TextToSpeech.SUCCESS) return
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
    private fun showAbout() {
        val dialog = AlertDialog.Builder(this)
            .setTitle(getString(R.string.about_title, BuildConfig.VERSION_NAME))
            .setMessage(getString(R.string.about_text))
            .setPositiveButton(R.string.about_close, null)
            .show()
        dialog.findViewById<TextView>(android.R.id.message)?.apply {
            Linkify.addLinks(this, Linkify.WEB_URLS)
            movementMethod = LinkMovementMethod.getInstance()
        }
    }

    private fun askForNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) requestNotifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
    }

    companion object {
        /** Without speech, how long a phrase stays before the next one can be invoked. */
        private const val SHOW_ONLY_COOLDOWN_MS = 600L
        private const val GHOST_ALPHA = 0.5f
        /** Safety cap on waiting for the choir before speaking (it lasts about 3 s). */
        private const val CHOIR_MAX_WAIT_MS = 4_000L
        private const val SPEECH_TIMEOUT_MS = 15_000L
    }

    override fun onDestroy() {
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }
}
