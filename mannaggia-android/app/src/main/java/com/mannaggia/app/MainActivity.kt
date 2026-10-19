package com.mannaggia.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorManager
import android.os.Build
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.mannaggia.app.databinding.ActivityMainBinding
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.util.Locale

/**
 * Main screen: tap the button (or shake the phone) to invoke a saint.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var tts: TextToSpeech? = null
    private var ttsReady = false

    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private lateinit var shakeDetector: ShakeDetector
    private var currentJob: Job? = null

    private val requestNotifPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { /* no-op */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnMannaggia.setOnClickListener { invokeSaint() }

        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        shakeDetector = ShakeDetector { invokeSaint() }

        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.ITALIAN)
                ttsReady = result != TextToSpeech.LANG_MISSING_DATA &&
                    result != TextToSpeech.LANG_NOT_SUPPORTED
            }
        }

        askForNotificationPermissionIfNeeded()
    }

    override fun onResume() {
        super.onResume()
        accelerometer?.let {
            sensorManager.registerListener(shakeDetector, it, SensorManager.SENSOR_DELAY_UI)
        }
    }

    override fun onPause() {
        super.onPause()
        sensorManager.unregisterListener(shakeDetector)
    }

    private fun invokeSaint() {
        // Ignore re-entrant triggers while an invocation is still in flight.
        if (currentJob?.isActive == true) return

        binding.progress.visibility = View.VISIBLE
        binding.btnMannaggia.isEnabled = false
        binding.txtResult.text = ""

        currentJob = lifecycleScope.launch {
            val result = runCatching { Mannaggia.randomSaint(this@MainActivity) }
            result.fold(
                onSuccess = { saint ->
                    val phrase = Mannaggia.phraseOf(saint)
                    binding.txtResult.text = phrase
                    if (binding.chkAudio.isChecked) speak(phrase)
                },
                onFailure = { e -> binding.txtResult.text = "Errore: ${e.message}" }
            )
            binding.progress.visibility = View.GONE
            binding.btnMannaggia.isEnabled = true
        }
    }

    // ---------------------------------------------------------------
    // System text-to-speech (offline, uses the device's Italian voice)
    // ---------------------------------------------------------------

    private fun speak(text: String) {
        if (!ttsReady) {
            Toast.makeText(this, "Voce italiana non disponibile", Toast.LENGTH_SHORT).show()
            return
        }
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "mannaggia")
    }

    private fun askForNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) requestNotifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
    }

    override fun onDestroy() {
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }
}
