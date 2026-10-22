package com.mannaggia.app

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.media.AudioManager
import android.util.AttributeSet
import android.util.TypedValue
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Splash screen shown for a moment when the app starts: the pixel-art logo (speech bubble
 * with a halo), "Mannaggia!" in the gothic letters of the buttons and the subtitle, on red
 * inside a gold illuminated-page frame, with the angelic choir (see [choirAllowed]).
 * It covers the whole window, fades out (with the choir) after [SHOW_MS] and goes away
 * at once when tapped.
 */
object Splash {

    private const val SHOW_MS = 1_500L
    private const val FADE_MS = 300L
    /** Share of the screen width for the logo and the title (as in the approved mock-up). */
    private const val LOGO_WIDTH = 0.46f
    private const val TITLE_WIDTH = 0.74f
    private const val SUBTITLE_SIZE = 0.062f

    fun show(activity: AppCompatActivity) {
        val content = activity.findViewById<FrameLayout>(android.R.id.content)
        val splash = LayoutInflater.from(activity).inflate(R.layout.view_splash, content, false)
        content.addView(splash)
        var gone = false
        fun dismiss() {
            if (gone) return
            gone = true
            choir?.fadeOut(FADE_MS)
            choir = null
            splash.animate().alpha(0f).setDuration(FADE_MS).withEndAction { content.removeView(splash) }.start()
        }
        splash.setOnClickListener { dismiss() }
        activity.lifecycleScope.launch {
            val logo = Avatars.splashLogo(activity)
            val title = Avatars.splashTitle(activity)
            splash.post {
                val w = splash.width
                size(splash.findViewById(R.id.imgSplashLogo), logo, w * LOGO_WIDTH)
                size(splash.findViewById(R.id.imgSplashTitle), title, w * TITLE_WIDTH)
                splash.findViewById<TextView>(R.id.txtSplashSubtitle)
                    .setTextSize(TypedValue.COMPLEX_UNIT_PX, w * SUBTITLE_SIZE)
                splash.findViewById<View>(R.id.splashContent).visibility = View.VISIBLE
                // The time on screen (and the choir) starts now that the splash is shown,
                // not when the app process started: a slow cold start must not eat it.
                choir = if (choirAllowed(activity)) Suono(activity, R.raw.coro).also { it.start() } else null
                activity.lifecycleScope.launch {
                    delay(SHOW_MS)
                    dismiss()
                }
            }
        }
    }

    private var choir: Suono? = null

    /** The choir plays if enabled in Options and the phone is not on silent or vibrate. */
    private fun choirAllowed(context: Context): Boolean {
        val audio = context.getSystemService(AudioManager::class.java)
        return Prefs.splashChoirEnabled(context) && audio?.ringerMode == AudioManager.RINGER_MODE_NORMAL
    }

    /** Show [bitmap] scaled by the largest whole factor that fits [maxWidth]: crisp pixels. */
    private fun size(view: ImageView, bitmap: android.graphics.Bitmap?, maxWidth: Float) {
        bitmap ?: return
        val k = (maxWidth / bitmap.width).toInt().coerceAtLeast(1)
        view.layoutParams = view.layoutParams.apply {
            width = bitmap.width * k
            height = bitmap.height * k
        }
        view.setImageDrawable(Avatars.pixelated(view.context, bitmap))
    }
}

/**
 * The gold frame of the splash, drawn as big pixels (about 1/120 of the screen width each):
 * a double gold border with little studs and square corner bosses.
 */
class CorniceSplash(context: Context, attrs: AttributeSet?) : View(context, attrs) {

    private val paint = Paint()
    private val gold = Color.rgb(232, 184, 56)
    private val goldDark = Color.rgb(176, 124, 28)
    private val goldLight = Color.rgb(252, 228, 132)

    override fun onDraw(canvas: Canvas) {
        val u = maxOf(4, width / 120)                 // one "pixel" of the frame
        val lw = width / u
        val lh = height / u
        val m = 3
        fun px(x: Int, y: Int, color: Int) {
            paint.color = color
            canvas.drawRect((x * u).toFloat(), (y * u).toFloat(), ((x + 1) * u).toFloat(), ((y + 1) * u).toFloat(), paint)
        }
        fun box(x0: Int, y0: Int, x1: Int, y1: Int, color: Int) {
            for (x in x0..x1) { px(x, y0, color); px(x, y1, color) }
            for (y in y0..y1) { px(x0, y, color); px(x1, y, color) }
        }
        box(m, m, lw - 1 - m, lh - 1 - m, gold)
        box(m + 1, m + 1, lw - 2 - m, lh - 2 - m, goldDark)
        box(m + 3, m + 3, lw - 4 - m, lh - 4 - m, goldDark)
        for (x in m + 8 until lw - m - 8 step 6) { px(x, m + 1, goldLight); px(x, lh - m - 2, goldLight) }
        for (y in m + 8 until lh - m - 8 step 6) { px(m + 1, y, goldLight); px(lw - m - 2, y, goldLight) }
        for ((x, y) in listOf(m - 1 to m - 1, lw - m - 4 to m - 1, m - 1 to lh - m - 4, lw - m - 4 to lh - m - 4)) {
            for (dx in 0..4) for (dy in 0..4) px(x + dx, y + dy, gold)
            box(x, y, x + 4, y + 4, goldDark)
            px(x + 2, y + 2, goldLight)
        }
    }
}
