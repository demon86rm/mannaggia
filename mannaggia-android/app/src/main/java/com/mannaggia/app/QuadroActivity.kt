package com.mannaggia.app

import android.graphics.Bitmap
import android.graphics.drawable.AnimationDrawable
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import com.mannaggia.app.databinding.ActivityQuadroBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.OutputStream

/**
 * "I miei santi": the favourites chosen in the album (EXTRA_SAINTS, 1 to 9) in a picture with
 * an animated frame (the legendary frames unlocked, plus the Colorful ones once Parroco is won).
 * Saved with the system file picker (no storage permission) or shared, as a PNG or an animated GIF.
 */
class QuadroActivity : AppCompatActivity() {

    private lateinit var binding: ActivityQuadroBinding
    private lateinit var saints: List<String>
    private var frameName = Avatars.GOLD_FRAME
    private var quadro: Quadro? = null

    private val savePng = registerForActivityResult(ActivityResultContracts.CreateDocument("image/png")) { uri ->
        uri?.let { save(it, gif = false) }
    }
    private val saveGif = registerForActivityResult(ActivityResultContracts.CreateDocument("image/gif")) { uri ->
        uri?.let { save(it, gif = true) }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityQuadroBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.toolbar.setNavigationOnClickListener { finish() }
        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }
        saints = intent.getStringArrayListExtra(EXTRA_SAINTS).orEmpty().take(Quadro.MAX)
        if (saints.isEmpty()) return finish()
        frameName = savedInstanceState?.getString(KEY_FRAME) ?: Prefs.frame(this)
        binding.btnFrame.setOnClickListener { chooseFrame() }
        binding.btnSave.setOnClickListener {
            chooseFormat { gif -> (if (gif) saveGif else savePng).launch(getString(R.string.quadro_file) + if (gif) ".gif" else ".png") }
        }
        binding.btnShare.setOnClickListener {
            chooseFormat { gif ->
                val q = quadro ?: return@chooseFormat
                lifecycleScope.launch {
                    val bytes = withContext(Dispatchers.Default) { java.io.ByteArrayOutputStream().also { write(q, it, gif) }.toByteArray() }
                    Condividi.image(this@QuadroActivity, "quadro", if (gif) "image/gif" else "image/png", null) { it.write(bytes) }
                }
            }
        }
        show()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString(KEY_FRAME, frameName)
    }

    /** Build the picture in the current frame and play its preview. */
    private fun show() {
        binding.progress.visibility = View.VISIBLE
        lifecycleScope.launch {
            val q = withContext(Dispatchers.IO) { Quadro.of(this@QuadroActivity, saints, frameName) }
            val frames = withContext(Dispatchers.Default) { (0 until FRAMES).map { q.render(it, PREVIEW_ZOOM) } }
            quadro = q
            (binding.imgQuadro.drawable as? AnimationDrawable)?.stop()
            val anim = AnimationDrawable().apply {
                frames.forEach { addFrame(Avatars.pixelated(this@QuadroActivity, it), FRAME_MS) }
                isOneShot = false
            }
            binding.imgQuadro.setImageDrawable(anim)
            anim.start()
            binding.progress.visibility = View.GONE
        }
    }

    /** The legendary frames unlocked, then the Colorful ones once their switch is unlocked. */
    private fun frames(): List<Pair<String, String>> {
        val names = resources.getStringArray(R.array.frame_names)
        val values = resources.getStringArray(R.array.frame_values)
        val legendary = values.indices.filter { Trofei.rewardAvailable(this, Trofei.Tipo.CORNICE, values[it]) }
            .map { values[it] to names[it] }
        val colorful = BuildConfig.DEBUG || Trofei.rewardAvailable(this, Trofei.Tipo.OPZIONE, Prefs.KEY_COLORFUL)
        return legendary + if (colorful) resources.getStringArray(R.array.quadro_colorful_values)
            .zip(resources.getStringArray(R.array.quadro_colorful_names)) else emptyList()
    }

    private fun chooseFrame() {
        val options = frames()
        AlertDialog.Builder(this)
            .setTitle(R.string.quadro_frame)
            .setSingleChoiceItems(options.map { it.second }.toTypedArray(), options.indexOfFirst { it.first == frameName }) { d, i ->
                d.dismiss()
                if (options[i].first != frameName) {
                    frameName = options[i].first
                    show()
                }
            }
            .show()
    }

    private fun chooseFormat(then: (gif: Boolean) -> Unit) {
        AlertDialog.Builder(this)
            .setItems(arrayOf(getString(R.string.quadro_format_png), getString(R.string.quadro_format_gif))) { _, i -> then(i == 1) }
            .show()
    }

    private fun save(uri: Uri, gif: Boolean) {
        val q = quadro ?: return
        lifecycleScope.launch {
            val ok = withContext(Dispatchers.IO) {
                runCatching { contentResolver.openOutputStream(uri)!!.use { write(q, it, gif) } }.isSuccess
            }
            Toast.makeText(this@QuadroActivity, if (ok) R.string.quadro_saved else R.string.quadro_save_failed, Toast.LENGTH_SHORT).show()
        }
    }

    /** The PNG (first frame, big) or the GIF (all the frames, a little smaller to stay light). */
    private fun write(q: Quadro, out: OutputStream, gif: Boolean) {
        if (!gif) {
            q.render(0, PNG_ZOOM).also { it.compress(Bitmap.CompressFormat.PNG, 100, out) }.recycle()
            return
        }
        val w = q.width * GIF_ZOOM
        val h = q.height * GIF_ZOOM
        Gif.write(out, w, h, (0 until FRAMES).map { step ->
            {
                val b = q.render(step, GIF_ZOOM)
                IntArray(w * h).also { b.getPixels(it, 0, w, 0, 0, w, h); b.recycle() }
            }
        }, FRAME_MS)
    }

    companion object {
        const val EXTRA_SAINTS = "santi"
        private const val KEY_FRAME = "frame"
        private const val FRAMES = 12
        private const val FRAME_MS = 167
        private const val PREVIEW_ZOOM = 2
        private const val PNG_ZOOM = 4
        private const val GIF_ZOOM = 3
    }
}
