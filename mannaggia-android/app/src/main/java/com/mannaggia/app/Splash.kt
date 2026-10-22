package com.mannaggia.app

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.os.Build
import android.util.AttributeSet
import android.util.TypedValue
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.ViewTreeObserver
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
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
    /** Without the Android 12+ system splash signal, start this long after the window focus. */
    private const val SYSTEM_SPLASH_FALLBACK_MS = 2_500L
    /** Share of the screen width for the logo and the title (as in the approved mock-up). */
    private const val LOGO_WIDTH = 0.46f
    private const val TITLE_WIDTH = 0.74f
    private const val SUBTITLE_SIZE = 0.062f

    /**
     * Show the splash; [onGone] runs once it has gone (e.g. to ask for permissions then).
     * [afterRecreation]: the activity was recreated, so the system splash is already gone.
     */
    fun show(activity: AppCompatActivity, afterRecreation: Boolean = false, onGone: () -> Unit = {}) {
        val content = activity.findViewById<FrameLayout>(android.R.id.content)
        val splash = LayoutInflater.from(activity).inflate(R.layout.view_splash, content, false)
        content.addView(splash)
        var gone = false
        var choir: Suono? = null
        // The activity can be recreated mid-splash (a configuration change on the first start):
        // MainActivity shows a new splash then, so this one's choir must not keep playing.
        activity.lifecycle.addObserver(object : DefaultLifecycleObserver {
            override fun onDestroy(owner: LifecycleOwner) { choir?.stop() }
        })
        fun dismiss() {
            if (gone) return
            gone = true
            choir?.fadeOut(FADE_MS)
            choir = null
            splash.animate().alpha(0f).setDuration(FADE_MS).withEndAction {
                content.removeView(splash)
                onGone()
            }.start()
        }
        splash.setOnClickListener { dismiss() }

        // The time on screen (and the choir) starts once the pixel art is ready AND the user can
        // see it: on Android 12+ when the system splash goes away (slow on the first start after
        // an install), otherwise when the window gets the focus. Fallback: 2.5 s after the focus,
        // in case no system splash was shown.
        var ready = false
        var visible = false
        var started = false
        fun maybeStart() {
            if (!ready || !visible || started || gone) return
            started = true
            choir = if (choirAllowed(activity)) Suono(activity, R.raw.coro).also { it.start() } else null
            activity.lifecycleScope.launch {
                delay(SHOW_MS)
                dismiss()
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !afterRecreation) {
            activity.splashScreen.setOnExitAnimationListener { systemSplash ->
                systemSplash.remove()
                visible = true
                maybeStart()
            }
        }
        fun onFocus() {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S || afterRecreation) {
                visible = true
                maybeStart()
            } else {
                activity.lifecycleScope.launch {
                    delay(SYSTEM_SPLASH_FALLBACK_MS)
                    visible = true
                    maybeStart()
                }
            }
        }
        if (splash.hasWindowFocus()) onFocus() else {
            splash.viewTreeObserver.addOnWindowFocusChangeListener(object : ViewTreeObserver.OnWindowFocusChangeListener {
                override fun onWindowFocusChanged(hasFocus: Boolean) {
                    if (!hasFocus) return
                    splash.viewTreeObserver.removeOnWindowFocusChangeListener(this)
                    onFocus()
                }
            })
        }

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
                ready = true
                maybeStart()
            }
        }
    }


    /**
     * The choir plays if enabled in Options, at the media volume like the voice and the other
     * sounds (whatever the ringer mode): with the media volume down it is simply not heard.
     */
    private fun choirAllowed(context: Context) = Prefs.splashChoirEnabled(context)

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
