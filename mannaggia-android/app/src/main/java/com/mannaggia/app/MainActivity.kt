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
    private lateinit var cardPop: CardPop

    private val requestNotifPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { /* no-op */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        applySystemBarInsets()

        binding.btnMannaggia.setOnClickListener { invokeSaint() }
        binding.txtSaintOfDay.setOnClickListener {
            saintOfDay?.let { saint -> invokeSaint { saint } }
        }
        binding.btnInfo.setOnClickListener { showAbout() }
        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        binding.btnAlbum.setOnClickListener {
            cardPop.cancel()
            startActivity(Intent(this, AlbumActivity::class.java))
        }
        cardPop = CardPop(binding.cardPop, binding.btnAlbum, lifecycleScope)
        if (BuildConfig.DEBUG) {
            // Debug builds only: long-press the binder to preview the legendary animation.
            binding.btnAlbum.setOnLongClickListener {
                lifecycleScope.launch { cardPop.show("San Pietro", Avatars.number(this@MainActivity, "San Pietro"), true) }
                true
            }
        }
        lifecycleScope.launch { binding.btnAlbum.setImageDrawable(Avatars.binder(this@MainActivity)) }
        themeTextColor = binding.txtResult.currentTextColor

        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        shakeDetector = ShakeDetector { invokeSaint() }

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
        if (Prefs.shakeEnabled(this)) {
            accelerometer?.let {
                sensorManager.registerListener(shakeDetector, it, SensorManager.SENSOR_DELAY_UI)
            }
        }
    }

    override fun onPause() {
        super.onPause()
        sensorManager.unregisterListener(shakeDetector)
        cardPop.cancel()
    }

    /** A saint just entered the album: show its card flying into the binder. */
    private suspend fun showNewCard(saint: String) {
        val legendary = Avatars.isLegendary(this, saint)
        if (legendary || Prefs.cardAnimEnabled(this)) {
            cardPop.show(saint, Avatars.number(this, saint), legendary)
        }
    }

    private fun showSaintOfDay(saint: String?) {
        saintOfDay = saint
        binding.txtSaintOfDay.text = saint?.let { getString(R.string.saint_of_day, it) }
        binding.txtSaintOfDay.visibility = if (saint == null) View.GONE else View.VISIBLE
    }

    /** Show (and optionally speak) the phrase for the saint returned by [pick]: random by default. */
    private fun invokeSaint(pick: suspend () -> String = { Mannaggia.randomSaint(this) }) {
        // Ignore button, shake and saint-of-the-day triggers until the previous phrase
        // has been spoken (or shown for a moment): the job stays active until then.
        if (currentJob?.isActive == true) return

        binding.progress.visibility = View.VISIBLE
        binding.btnMannaggia.isEnabled = false
        binding.txtResult.text = ""

        currentJob = lifecycleScope.launch {
            val result = runCatching { pick() }
            binding.progress.visibility = View.GONE
            result.fold(
                onSuccess = { saint ->
                    val isNew = runCatching { Album.record(this@MainActivity, saint) }.getOrDefault(false)
                    if (isNew) showNewCard(saint)
                    val phrase = Mannaggia.phraseOf(saint)
                    binding.txtResult.text = phrase
                    if (Prefs.ttsEnabled(this@MainActivity)) speakAndWait(phrase) else delay(SHOW_ONLY_COOLDOWN_MS)
                },
                onFailure = { e -> binding.txtResult.text = "Errore: ${e.message}" }
            )
            binding.btnMannaggia.isEnabled = true
        }
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
        private const val SPEECH_TIMEOUT_MS = 15_000L
    }

    override fun onDestroy() {
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }
}
