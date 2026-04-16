package com.mannaggia.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorManager
import android.media.MediaPlayer
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.mannaggia.app.databinding.ActivityMainBinding
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.net.URLEncoder

/**
 * Main screen: tap the button (or shake the phone) to invoke a saint.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var mediaPlayer: MediaPlayer? = null

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
            val result = runCatching { Mannaggia.fetchRandomSaint() }
            result.fold(
                onSuccess = { saint ->
                    val phrase = Mannaggia.phraseOf(saint)
                    binding.txtResult.text = phrase
                    if (binding.chkAudio.isChecked) speakWithGoogleTts(phrase)
                },
                onFailure = { e -> binding.txtResult.text = "Errore: ${e.message}" }
            )
            binding.progress.visibility = View.GONE
            binding.btnMannaggia.isEnabled = true
        }
    }

    // ---------------------------------------------------------------
    // Google Translate TTS (same endpoint the bash `say()` uses)
    // ---------------------------------------------------------------

    private fun speakWithGoogleTts(text: String) {
        releasePlayer()
        val encoded = URLEncoder.encode(text, "UTF-8")
        val url =
            "https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=$encoded&tl=it"
        try {
            mediaPlayer = MediaPlayer().apply {
                val headers = mapOf("User-Agent" to "Mozilla/5.0")
                setDataSource(this@MainActivity, Uri.parse(url), headers)
                setOnPreparedListener { start() }
                setOnCompletionListener { releasePlayer() }
                setOnErrorListener { _, _, _ -> releasePlayer(); true }
                prepareAsync()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun releasePlayer() {
        mediaPlayer?.release()
        mediaPlayer = null
    }

    private fun askForNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) requestNotifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
    }

    override fun onDestroy() {
        releasePlayer()
        super.onDestroy()
    }
}
