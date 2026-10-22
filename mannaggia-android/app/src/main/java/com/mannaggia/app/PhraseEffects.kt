package com.mannaggia.app

import android.animation.ArgbEvaluator
import android.animation.ValueAnimator
import android.graphics.Color
import android.text.StaticLayout
import android.text.TextPaint
import android.util.TypedValue
import android.view.View
import android.widget.TextView
import kotlin.random.Random

/**
 * Animated phrase effects, rewards of the trophies: "aureola" (pulsing glow),
 * "tremolio" (the phrase shakes), "fiamma" (red-orange-yellow flicker) and
 * "terminale" (the phrase is typed after a `$ ` prompt, then a block cursor
 * blinks). The running animation is kept in the view's tag, so starting a new
 * effect stops the previous one; it also stops when the view is detached.
 *
 * Set the phrase with [setText] rather than `view.text`: the Terminale effect
 * rewrites the text while typing and needs the original.
 */
object PhraseEffects {

    /**
     * Show [text] in [view]; with the Terminale effect on, it gets typed. Long saint names
     * get a smaller font so the phrase never takes more than two lines.
     */
    fun setText(view: TextView, text: CharSequence) {
        view.setTag(R.id.phrase_text, text)
        val terminale = view.getTag(R.id.phrase_effect) is Terminale
        fitTwoLines(view, if (terminale) Terminale.PROMPT + text + Terminale.CURSOR else text)
        if (terminale) {
            Terminale(view, text).start()
        } else {
            view.text = text
        }
    }

    fun start(view: TextView, effect: String, color: Int) {
        stop(view)
        val density = view.resources.displayMetrics.density
        if (effect == Prefs.EFFECT_TERMINALE) {
            // Text set in a layout (the Options preview) has no stored original yet.
            val original = view.getTag(R.id.phrase_text) as? CharSequence
                ?: view.text.also { view.setTag(R.id.phrase_text, it) }
            Terminale(view, original).start()
            stopOnDetach(view)
            return
        }
        val animator = when (effect) {
            Prefs.EFFECT_AUREOLA -> ValueAnimator.ofFloat(4f, 18f).apply {
                duration = 1_100
                repeatMode = ValueAnimator.REVERSE
                addUpdateListener { view.setShadowLayer((it.animatedValue as Float) * density, 0f, 0f, color) }
            }
            Prefs.EFFECT_TREMOLIO -> ValueAnimator.ofFloat(0f, 1f).apply {
                duration = 60
                addUpdateListener {
                    view.translationX = Random.nextFloat() * 3f * density - 1.5f * density
                    view.translationY = Random.nextFloat() * 3f * density - 1.5f * density
                }
            }
            Prefs.EFFECT_FIAMMA -> ValueAnimator.ofObject(ArgbEvaluator(), FLAME_RED, FLAME_ORANGE, FLAME_YELLOW).apply {
                duration = 900
                repeatMode = ValueAnimator.REVERSE
                addUpdateListener {
                    val c = it.animatedValue as Int
                    view.setTextColor(c)
                    view.setShadowLayer(12f * density, 0f, 0f, c)
                }
            }
            else -> return
        }
        animator.repeatCount = ValueAnimator.INFINITE
        view.setTag(R.id.phrase_effect, animator)
        stopOnDetach(view)
        animator.start()
    }

    private fun stopOnDetach(view: TextView) {
        view.addOnAttachStateChangeListener(object : View.OnAttachStateChangeListener {
            override fun onViewAttachedToWindow(v: View) = Unit
            override fun onViewDetachedFromWindow(v: View) {
                v.removeOnAttachStateChangeListener(this)
                stop(view)
            }
        })
    }

    fun stop(view: TextView) {
        when (val running = view.getTag(R.id.phrase_effect)) {
            is ValueAnimator -> running.cancel()
            is Terminale -> {
                running.cancel()
                (view.getTag(R.id.phrase_text) as? CharSequence)?.let { view.text = it }  // drop prompt and cursor
            }
        }
        view.setTag(R.id.phrase_effect, null)
        view.translationX = 0f
        view.translationY = 0f
    }

    /**
     * Types [text] one character at a time after a `$ ` prompt (human-like
     * timing: slightly irregular, a pause after spaces), then blinks a block cursor.
     */
    private class Terminale(private val view: TextView, private val text: CharSequence) : Runnable {
        private var typed = 0
        private var cursorOn = true
        private var cancelled = false

        fun start() {
            (view.getTag(R.id.phrase_effect) as? Terminale)?.cancel()
            view.setTag(R.id.phrase_effect, this)
            view.text = PROMPT + CURSOR
            if (text.isEmpty()) return
            view.postDelayed(this, FIRST_KEY_MS)
        }

        fun cancel() {
            cancelled = true
            view.removeCallbacks(this)
        }

        override fun run() {
            if (cancelled) return
            if (typed < text.length) {
                typed++
                view.text = PROMPT + text.subSequence(0, typed) + CURSOR
                val c = text[typed - 1]
                val delay = KEY_MS + Random.nextLong(-KEY_JITTER_MS, KEY_JITTER_MS) + if (c == ' ') SPACE_PAUSE_MS else 0
                view.postDelayed(this, delay)
            } else {
                // Done: blink the cursor (a space keeps the width steady).
                cursorOn = !cursorOn
                view.text = PROMPT + text + if (cursorOn) CURSOR else " "
                view.postDelayed(this, BLINK_MS)
            }
        }

        companion object {
            const val PROMPT = "$ "
            const val CURSOR = "█"
            const val FIRST_KEY_MS = 250L
            const val KEY_MS = 45L
            const val KEY_JITTER_MS = 20L
            const val SPACE_PAUSE_MS = 60L
            const val BLINK_MS = 530L
        }
    }

    /** The largest size, from [MAX_SP] down to [MIN_SP], at which [text] fits in two lines of [view]. */
    private fun fitTwoLines(view: TextView, text: CharSequence) {
        val width = view.width - view.totalPaddingLeft - view.totalPaddingRight
        if (width <= 0 || text.isEmpty()) return
        val metrics = view.resources.displayMetrics
        val paint = TextPaint(view.paint)
        var sp = MAX_SP
        while (sp > MIN_SP) {
            paint.textSize = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_SP, sp, metrics)
            if (StaticLayout.Builder.obtain(text, 0, text.length, paint, width).build().lineCount <= 2) break
            sp -= 1f
        }
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp)
    }

    /** The phrase size of activity_main.xml, and the smallest one for long names. */
    private const val MAX_SP = 28f
    private const val MIN_SP = 18f

    private val FLAME_RED = Color.parseColor("#E53935")
    private val FLAME_ORANGE = Color.parseColor("#FF8F00")
    private val FLAME_YELLOW = Color.parseColor("#FFD54F")
}
