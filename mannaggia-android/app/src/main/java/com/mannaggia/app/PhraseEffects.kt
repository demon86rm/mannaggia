package com.mannaggia.app

import android.animation.ArgbEvaluator
import android.animation.ValueAnimator
import android.graphics.Color
import android.view.View
import android.widget.TextView
import kotlin.random.Random

/**
 * Animated phrase effects, rewards of the trophies: "aureola" (pulsing glow),
 * "tremolio" (the phrase shakes) and "fiamma" (red-orange-yellow flicker).
 * The animator is kept in the view's tag, so starting a new effect stops the
 * previous one; it also stops when the view is detached.
 */
object PhraseEffects {

    fun start(view: TextView, effect: String, color: Int) {
        stop(view)
        val density = view.resources.displayMetrics.density
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
        view.addOnAttachStateChangeListener(object : View.OnAttachStateChangeListener {
            override fun onViewAttachedToWindow(v: View) = Unit
            override fun onViewDetachedFromWindow(v: View) {
                v.removeOnAttachStateChangeListener(this)
                stop(view)
            }
        })
        animator.start()
    }

    fun stop(view: TextView) {
        (view.getTag(R.id.phrase_effect) as? ValueAnimator)?.cancel()
        view.setTag(R.id.phrase_effect, null)
        view.translationX = 0f
        view.translationY = 0f
    }

    private val FLAME_RED = Color.parseColor("#E53935")
    private val FLAME_ORANGE = Color.parseColor("#FF8F00")
    private val FLAME_YELLOW = Color.parseColor("#FFD54F")
}
