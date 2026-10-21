package com.mannaggia.app

import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.graphics.drawable.AnimationDrawable
import android.graphics.drawable.GradientDrawable
import android.view.View
import android.view.animation.AccelerateInterpolator
import android.view.animation.OvershootInterpolator
import androidx.lifecycle.LifecycleCoroutineScope
import com.mannaggia.app.databinding.ViewCardPopBinding
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * The "new card" animation on the main screen: the card of a saint just added to
 * the album pops up in the middle, then shrinks and flies into the binder [target],
 * which bounces. Legendary saints stay on screen longer, with the sparkling gold
 * frame and a pulsing glow behind the card.
 */
class CardPop(
    private val pop: ViewCardPopBinding,
    private val target: View,
    private val scope: LifecycleCoroutineScope,
) {

    private var job: Job? = null
    private var glowPulse: ValueAnimator? = null

    init {
        // Soft gold glow: radial gradient from warm gold to transparent.
        pop.imgGlow.setImageDrawable(GradientDrawable().apply {
            gradientType = GradientDrawable.RADIAL_GRADIENT
            gradientRadius = 480f
            colors = intArrayOf(0xCCFFE27A.toInt(), 0x66F2B632, 0x00F2B632)
        })
    }

    /** Show the card of [saint], card number [number]. A new call replaces a running one. */
    fun show(saint: String, number: Int?, legendary: Boolean) {
        val context = pop.root.context
        cancel()
        job = scope.launch {
            pop.txtSaint.text = saint
            pop.txtNumber.text = number?.let { context.getString(R.string.card_number, it) } ?: ""
            pop.txtLabel.text = context.getString(if (legendary) R.string.card_new_legendary else R.string.card_new)
            pop.imgAvatar.setImageDrawable(Avatars.load(context, saint)?.let { Avatars.pixelated(context, it) })
            if (legendary) {
                val sparkle = Avatars.frameDrawable(context)
                pop.imgFrame.setImageDrawable(sparkle)
                pop.imgFrame.visibility = View.VISIBLE
                sparkle.start()
                pop.imgGlow.visibility = View.VISIBLE
                glowPulse = ValueAnimator.ofFloat(0.85f, 1.15f).apply {
                    duration = GLOW_PULSE_MS
                    repeatMode = ValueAnimator.REVERSE
                    repeatCount = ValueAnimator.INFINITE
                    addUpdateListener {
                        val v = it.animatedValue as Float
                        pop.imgGlow.scaleX = v
                        pop.imgGlow.scaleY = v
                        pop.imgGlow.alpha = 0.55f + (v - 0.85f) * 1.5f
                        pop.imgGlow.rotation += 0.6f
                    }
                    start()
                }
            } else {
                pop.imgFrame.visibility = View.GONE
                pop.imgGlow.visibility = View.GONE
            }

            // 1. Pop in.
            val card = pop.popCard
            card.translationX = 0f; card.translationY = 0f
            card.scaleX = 0.2f; card.scaleY = 0.2f; card.alpha = 0f
            pop.root.visibility = View.VISIBLE
            card.animate().scaleX(1f).scaleY(1f).alpha(1f)
                .setDuration(POP_IN_MS).setInterpolator(OvershootInterpolator(1.6f)).start()

            // 2. Stay on screen (longer for a legend).
            delay(POP_IN_MS + if (legendary) HOLD_LEGENDARY_MS else HOLD_MS)

            // 3. Fly into the binder.
            pop.imgGlow.animate().alpha(0f).setDuration(FLY_MS).start()
            val cardPos = IntArray(2).also { card.getLocationOnScreen(it) }
            val targetPos = IntArray(2).also { target.getLocationOnScreen(it) }
            val dx = targetPos[0] + target.width / 2f - (cardPos[0] + card.width / 2f)
            val dy = targetPos[1] + target.height / 2f - (cardPos[1] + card.height / 2f)
            card.animate().translationX(dx).translationY(dy).scaleX(0.12f).scaleY(0.12f).alpha(0.4f)
                .setDuration(FLY_MS).setInterpolator(AccelerateInterpolator(1.4f))
                .setListener(object : AnimatorListenerAdapter() {
                    override fun onAnimationEnd(animation: Animator) {
                        card.animate().setListener(null)
                        hide()
                        bump()
                    }
                }).start()
        }
    }

    fun cancel() {
        job?.cancel()
        pop.popCard.animate().setListener(null).cancel()
        hide()
    }

    private fun hide() {
        glowPulse?.cancel()
        glowPulse = null
        (pop.imgFrame.drawable as? AnimationDrawable)?.stop()
        pop.root.visibility = View.GONE
    }

    /** The binder "swallows" the card. */
    private fun bump() {
        ObjectAnimator.ofFloat(target, View.SCALE_X, 1f, 1.25f, 1f).setDuration(BUMP_MS).start()
        ObjectAnimator.ofFloat(target, View.SCALE_Y, 1f, 1.25f, 1f).setDuration(BUMP_MS).start()
    }

    companion object {
        private const val POP_IN_MS = 220L
        private const val HOLD_MS = 600L
        private const val HOLD_LEGENDARY_MS = 3000L
        private const val FLY_MS = 480L
        private const val BUMP_MS = 260L
        private const val GLOW_PULSE_MS = 700L
    }
}
