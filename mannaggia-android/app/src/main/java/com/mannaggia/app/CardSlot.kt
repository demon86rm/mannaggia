package com.mannaggia.app

import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.graphics.drawable.AnimationDrawable
import android.graphics.drawable.GradientDrawable
import android.view.View
import android.view.ViewGroup
import android.view.animation.AccelerateInterpolator
import android.view.animation.OvershootInterpolator
import android.widget.FrameLayout
import android.widget.ImageView
import androidx.constraintlayout.widget.ConstraintLayout
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
 * The card of the last saint invoked, centred on the main screen between the phrase and the button.
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
    /** Wrapper of the card and its stamp, centred on the screen. */
    private val fit: View,
    private val stamp: ImageView,
    private val glow: ImageView,
    private val fx: ViewCardFxBinding,
    private val target: View,
    private val scope: LifecycleCoroutineScope,
    /** The screen layout: the card is centred in it, with [phrase] above and [button] below. */
    private val root: View,
    /** Nothing goes above the bottom of this view (the top buttons). */
    private val topLimit: View,
    private val phrase: View,
    private val button: View,
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
        // Refit whenever the phrase (typing, 2 lines), the card or the button move.
        // Refit (after the layout pass) whenever the phrase grows, the card changes or the screen does.
        val refit = View.OnLayoutChangeListener { _, _, _, _, _, _, _, _, _ -> fit.post { fitToSpace() } }
        root.addOnLayoutChangeListener(refit)
        phrase.addOnLayoutChangeListener(refit)
        fit.addOnLayoutChangeListener(refit)
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
                    val sparkle = Avatars.frameDrawable(context, saint)
                    card.imgFrame.setImageDrawable(sparkle)
                    card.imgFrame.visibility = View.VISIBLE
                    sparkle.start()
                }
                else -> card.imgFrame.visibility = View.GONE
            }

            showBookmark(context, saint)

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
                    placeHintUnderCard()
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

    /**
     * The favourite bookmark, a toggle: a tap adds [saint], another removes it. Not a favourite
     * yet, it is the coloured banner half transparent (the empty outline of the album passed
     * unnoticed on the card).
     */
    private suspend fun showBookmark(context: android.content.Context, saint: String) {
        val btn = card.btnBookmark
        btn.setImageDrawable(Avatars.bookmark(context, true))
        fun set(full: Boolean) {
            btn.alpha = if (full) 1f else BOOKMARK_OFF_ALPHA
            btn.contentDescription = context.getString(if (full) R.string.fav_remove else R.string.fav_add)
        }
        set(saint in Preferiti.all(context))
        btn.visibility = View.VISIBLE
        btn.setOnClickListener {
            scope.launch {
                val full = saint in Preferiti.all(context)
                if (full) Preferiti.remove(context, listOf(saint)) else Preferiti.add(context, listOf(saint))
                set(!full)
            }
        }
    }

    /**
     * Put the "tap" hint between the card and the "Mannaggia!" button, centred in that space;
     * if the space is too short (16:9 and smaller screens), over the bottom of the card instead.
     */
    private fun placeHintUnderCard() {
        val rootY = IntArray(2).also { fx.root.getLocationOnScreen(it) }[1]
        val cardBottom = IntArray(2).also { card.root.getLocationOnScreen(it) }[1] - rootY + card.root.height
        val buttonTop = IntArray(2).also { button.getLocationOnScreen(it) }[1] - rootY
        val gap = HINT_GAP_DP * card.root.resources.displayMetrics.density
        val hint = fx.txtHint
        if (hint.height == 0) hint.measure(View.MeasureSpec.UNSPECIFIED, View.MeasureSpec.UNSPECIFIED)
        val h = if (hint.height > 0) hint.height else hint.measuredHeight
        val space = buttonTop - cardBottom
        val fits = space >= h + 2 * gap
        hint.translationY = if (fits) cardBottom + (space - h) / 2f else cardBottom - h - gap
        // Over the card it must hide the name under it, not show through.
        hint.setBackgroundColor(if (fits) HINT_BG else HINT_BG_OPAQUE)
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
        val fly = fx.imgFly
        fly.setImageBitmap(view.drawToBitmap())
        fly.layoutParams = (fly.layoutParams as FrameLayout.LayoutParams).apply {
            width = view.width
            height = view.height
        }
        val rootPos = IntArray(2).also { fx.root.getLocationOnScreen(it) }
        val cardPos = IntArray(2).also { view.getLocationOnScreen(it) }
        val targetPos = IntArray(2).also { target.getLocationOnScreen(it) }
        val startX = (cardPos[0] - rootPos[0]).toFloat()
        val startY = (cardPos[1] - rootPos[1]).toFloat()
        val w = view.width.toFloat()
        val h = view.height.toFloat()
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

    /**
     * The card is centred on the screen, with the phrase above it and the button below.
     * When the phrase (and the "Nuova!" stamp) would reach the top buttons, the card moves
     * down, as far as the button allows; only if that is not enough it gets narrower, and its
     * square portrait shorter.
     */
    private fun fitToSpace() {
        val view = card.root
        val fitH = fit.height
        if (fitH == 0 || root.height == 0) return
        val density = view.resources.displayMetrics.density
        val gap = GAP_DP * density
        val phraseGap = marginOf(phrase) { it.bottomMargin }
        // The stamp may stick out above the card into the gap left for the phrase, not beyond.
        val stampOut = maxOf(0, -stamp.top - phraseGap)
        val minTop = topLimit.bottom + gap + phrase.height + phraseGap + stampOut   // top of the card wrapper
        val maxBottom = button.top - gap
        val contentTop = root.paddingTop
        val contentH = root.height - root.paddingTop - root.paddingBottom

        // 1. Width: narrower when even the whole space between phrase and button is short.
        val width = view.width
        val target = (width + (maxBottom - minTop - fitH)).toInt()
            .coerceIn((MIN_CARD_DP * density).toInt(), (MAX_CARD_DP * density).toInt())
        if (kotlin.math.abs(target - width) >= 1) {
            view.layoutParams = view.layoutParams.apply { this.width = target }
            return                                          // refit after the new layout
        }

        // 2. Position: centred if possible, otherwise as close to the centre as the limits allow.
        val centredTop = contentTop + (contentH - fitH) / 2f
        val top = centredTop.coerceAtMost(maxBottom - fitH).coerceAtLeast(minTop)
        val bias = if (contentH > fitH) ((top - contentTop) / (contentH - fitH)).coerceIn(0f, 1f) else 0.5f
        val params = fit.layoutParams as ConstraintLayout.LayoutParams
        if (kotlin.math.abs(params.verticalBias - bias) > 0.002f) {
            params.verticalBias = bias
            fit.layoutParams = params
        }
    }

    private fun marginOf(v: View, side: (ViewGroup.MarginLayoutParams) -> Int) =
        (v.layoutParams as? ViewGroup.MarginLayoutParams)?.let(side) ?: 0

    companion object {

        /** The card bookmark while the saint is not a favourite. */

        private const val BOOKMARK_OFF_ALPHA = 0.45f
        private const val POP_IN_MS = 220L
        private const val STAMP_MS = 260L
        private const val FADE_MS = 150L
        private const val HOLD_MS = 700L
        /** The "tap to put it in the album" hint appears after this. */
        private const val HINT_DELAY_MS = 1000L
        private const val HINT_GAP_DP = 2f
        private const val HINT_BG = 0xB3000000.toInt()
        private const val HINT_BG_OPAQUE = 0xFF2A2228.toInt()
        private const val FLY_MS = 480L
        private const val BUMP_MS = 260L
        private const val GLOW_PULSE_MS = 700L
        /** Card width: 180dp as designed, down to 90dp on cramped screens. */
        private const val MAX_CARD_DP = 180f
        private const val MIN_CARD_DP = 90f
        /** Breathing space below the top buttons and above the button. */
        private const val GAP_DP = 12f
    }
}
