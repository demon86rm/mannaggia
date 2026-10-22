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
import android.widget.FrameLayout
import android.widget.ImageView
import androidx.core.view.drawToBitmap
import androidx.lifecycle.LifecycleCoroutineScope
import com.mannaggia.app.databinding.ViewCardBinding
import com.mannaggia.app.databinding.ViewCardFxBinding
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

/**
 * The card of the last saint invoked, always on the main screen above the phrase.
 *
 * - A saint new to the album pops in with the pixel-art "Nuova!" stamp, then a copy of the card
 *   flies into the binder [target], which bounces; the card itself stays.
 * - A saint already in the album just fades in, labelled "Già nell'album".
 * - New legendary saints also get the angelic choir, a pulsing gold glow and wait for
 *   a tap before their copy flies. Legendary cards always keep the sparkling frame,
 *   special cards (S1–S6) the silver one.
 */
class CardSlot(
    private val card: ViewCardBinding,
    /** Wrapper of the card and its stamp, scaled down when the space is short. */
    private val fit: View,
    private val stamp: ImageView,
    private val glow: ImageView,
    private val fx: ViewCardFxBinding,
    private val target: View,
    private val scope: LifecycleCoroutineScope,
    /** The card fits between the bottom of [above] and the top of [below]. */
    private val above: View,
    private val below: View,
) {

    private var job: Job? = null
    private var glowPulse: ValueAnimator? = null
    private var coro: Suono? = null

    /** True while a new legendary card waits for the tap that puts it in the album. */
    var isHolding = false
        private set

    init {
        // Soft gold glow: radial gradient from warm gold to transparent.
        glow.setImageDrawable(GradientDrawable().apply {
            gradientType = GradientDrawable.RADIAL_GRADIENT
            gradientRadius = 480f
            colors = intArrayOf(0xCCFFE27A.toInt(), 0x66F2B632, 0x00F2B632)
        })
        scope.launch { stamp.setImageDrawable(Avatars.newStamp(stamp.context)) }
        // Refit whenever the top buttons, the card or the phrase (typing, 2 lines) move.
        val refit = View.OnLayoutChangeListener { _, _, _, _, _, _, _, _, _ -> fitToSpace() }
        above.addOnLayoutChangeListener(refit)
        fit.addOnLayoutChangeListener(refit)
        below.addOnLayoutChangeListener(refit)
    }

    /**
     * Show the card of [saint] (card [number]). [animate] is the "new card animation"
     * option; new legendary saints are always animated. A new call replaces a running one.
     */
    fun show(saint: String, number: Int?, isNew: Boolean, legendary: Boolean, special: Boolean, animate: Boolean) {
        val context = card.root.context
        cancel()
        val newLegend = isNew && legendary
        // The choir starts with the card (synchronously, so awaitChoir() sees it).
        if (newLegend) coro = Suono(context, R.raw.coro).also { it.start() }
        stamp.visibility = View.GONE
        job = scope.launch {
            card.txtSaint.text = saint
            card.txtNumber.text = number?.let {
                context.getString(if (special) R.string.card_number_special else R.string.card_number, it)
            } ?: ""
            card.txtLabel.text = context.getString(when {
                special -> R.string.card_special
                newLegend -> R.string.card_new_legendary
                isNew -> R.string.card_new
                else -> R.string.card_owned
            })
            card.imgAvatar.setImageDrawable(Avatars.load(context, saint)?.let { Avatars.pixelated(context, it) })
            (card.imgFrame.drawable as? AnimationDrawable)?.stop()
            when {
                special -> {
                    card.imgFrame.setImageDrawable(Avatars.silverFrame(context))
                    card.imgFrame.visibility = View.VISIBLE
                }
                legendary -> {
                    val sparkle = Avatars.frameDrawable(context)
                    card.imgFrame.setImageDrawable(sparkle)
                    card.imgFrame.visibility = View.VISIBLE
                    sparkle.start()
                }
                else -> card.imgFrame.visibility = View.GONE
            }

            val view = card.root
            view.visibility = View.VISIBLE
            if (!isNew) {
                // Already in the album: a quick fade, nothing else.
                view.scaleX = 1f; view.scaleY = 1f; view.alpha = 0f
                view.animate().alpha(1f).setDuration(FADE_MS).start()
                return@launch
            }

            // 1. Pop in (or just appear when the animation is off), then the stamp.
            val animated = newLegend || animate
            if (animated) {
                view.scaleX = 0.2f; view.scaleY = 0.2f; view.alpha = 0f
                view.animate().scaleX(1f).scaleY(1f).alpha(1f)
                    .setDuration(POP_IN_MS).setInterpolator(OvershootInterpolator(1.6f)).start()
                delay(POP_IN_MS)
            } else {
                view.scaleX = 1f; view.scaleY = 1f; view.alpha = 1f
            }
            showStamp()
            if (!animated) return@launch

            // 2. Stay a moment, or until tapped for a legend.
            if (newLegend) {
                startGlow()
                isHolding = true
                val tapped = CompletableDeferred<Unit>()
                fx.root.visibility = View.VISIBLE
                fx.root.setOnClickListener { tapped.complete(Unit) }
                launch {
                    delay(HINT_DELAY_MS)
                    fx.txtHint.alpha = 0f
                    fx.txtHint.visibility = View.VISIBLE
                    fx.txtHint.animate().alpha(1f).setDuration(300).start()
                }
                tapped.await()
                fx.root.setOnClickListener(null)
                fx.root.isClickable = false
                fx.txtHint.visibility = View.GONE
                isHolding = false
                glow.animate().alpha(0f).setDuration(FLY_MS).start()
            } else {
                delay(HOLD_MS)
            }

            // 3. A copy flies into the binder; the card stays.
            flyCopy()
        }
    }

    /** Wait (at most [timeoutMs]) for the choir to end, e.g. before speaking the phrase. */
    suspend fun awaitChoir(timeoutMs: Long) {
        val c = coro ?: return
        withTimeoutOrNull(timeoutMs) { c.done.await() }
    }

    /** Stop the effects. The card stays on screen as it is. */
    fun cancel() {
        job?.cancel()
        coro?.stop()
        coro = null
        isHolding = false
        val view = card.root
        view.animate().cancel()
        view.scaleX = 1f; view.scaleY = 1f; view.alpha = 1f
        stamp.animate().cancel()
        stamp.scaleX = 1f; stamp.scaleY = 1f; stamp.alpha = 1f
        stopGlow()
        fx.imgFly.animate().setListener(null).cancel()
        fx.imgFly.visibility = View.GONE
        fx.root.setOnClickListener(null)
        fx.root.isClickable = false
        fx.txtHint.visibility = View.GONE
        fx.root.visibility = View.GONE
    }

    private fun showStamp() {
        stamp.visibility = View.VISIBLE
        stamp.scaleX = 2.2f; stamp.scaleY = 2.2f; stamp.alpha = 0f
        stamp.animate().scaleX(1f).scaleY(1f).alpha(1f)
            .setDuration(STAMP_MS).setInterpolator(OvershootInterpolator(2f)).start()
    }

    private fun startGlow() {
        glow.alpha = 0.55f
        glow.visibility = View.VISIBLE
        glowPulse = ValueAnimator.ofFloat(0.85f, 1.15f).apply {
            duration = GLOW_PULSE_MS
            repeatMode = ValueAnimator.REVERSE
            repeatCount = ValueAnimator.INFINITE
            addUpdateListener {
                val v = it.animatedValue as Float
                glow.scaleX = v
                glow.scaleY = v
                glow.alpha = 0.55f + (v - 0.85f) * 1.5f
                glow.rotation += 0.6f
            }
            start()
        }
    }

    private fun stopGlow() {
        glowPulse?.cancel()
        glowPulse = null
        glow.animate().cancel()
        glow.visibility = View.GONE
    }

    /** A snapshot of the card shrinks into the binder, which "swallows" it. */
    private fun flyCopy() {
        val view = card.root
        if (view.width == 0 || view.height == 0) return
        val scale = fit.scaleX
        val fly = fx.imgFly
        fly.setImageBitmap(view.drawToBitmap())
        fly.layoutParams = (fly.layoutParams as FrameLayout.LayoutParams).apply {
            width = (view.width * scale).toInt()
            height = (view.height * scale).toInt()
        }
        val rootPos = IntArray(2).also { fx.root.getLocationOnScreen(it) }
        val cardPos = IntArray(2).also { view.getLocationOnScreen(it) }
        val targetPos = IntArray(2).also { target.getLocationOnScreen(it) }
        val startX = (cardPos[0] - rootPos[0]).toFloat()
        val startY = (cardPos[1] - rootPos[1]).toFloat()
        val w = view.width * scale
        val h = view.height * scale
        fly.translationX = startX; fly.translationY = startY
        fly.scaleX = 1f; fly.scaleY = 1f; fly.alpha = 1f
        fly.visibility = View.VISIBLE
        fx.root.visibility = View.VISIBLE
        val dx = targetPos[0] - rootPos[0] + target.width / 2f - w / 2f
        val dy = targetPos[1] - rootPos[1] + target.height / 2f - h / 2f
        fly.animate().translationX(dx).translationY(dy).scaleX(0.12f).scaleY(0.12f).alpha(0.4f)
            .setDuration(FLY_MS).setInterpolator(AccelerateInterpolator(1.4f))
            .setListener(object : AnimatorListenerAdapter() {
                override fun onAnimationEnd(animation: Animator) {
                    fly.animate().setListener(null)
                    fly.visibility = View.GONE
                    fly.setImageDrawable(null)
                    if (!isHolding) fx.root.visibility = View.GONE
                    stopGlow()
                    bump()
                }
            }).start()
    }

    /** The binder bounces as the copy lands. */
    private fun bump() {
        ObjectAnimator.ofFloat(target, View.SCALE_X, 1f, 1.25f, 1f).setDuration(BUMP_MS).start()
        ObjectAnimator.ofFloat(target, View.SCALE_Y, 1f, 1.25f, 1f).setDuration(BUMP_MS).start()
    }

    /** Scale the card down (never up) to fit between the top buttons and the phrase. */
    private fun fitToSpace() {
        val h = fit.height
        if (h == 0) return
        val space = below.top - above.bottom
        val s = if (space <= 0) MIN_SCALE else (space.toFloat() / h).coerceIn(MIN_SCALE, 1f)
        if (fit.scaleX != s) {
            fit.scaleX = s
            fit.scaleY = s
        }
    }

    companion object {
        private const val POP_IN_MS = 220L
        private const val STAMP_MS = 260L
        private const val FADE_MS = 150L
        private const val HOLD_MS = 700L
        /** The "tap to put it in the album" hint appears after this. */
        private const val HINT_DELAY_MS = 1000L
        private const val FLY_MS = 480L
        private const val BUMP_MS = 260L
        private const val GLOW_PULSE_MS = 700L
        private const val MIN_SCALE = 0.5f
    }
}
