package com.mannaggia.app

import android.content.Context
import android.view.View
import android.view.animation.OvershootInterpolator
import android.widget.ImageView
import android.widget.TextView
import androidx.lifecycle.LifecycleCoroutineScope
import kotlinx.coroutines.launch

/**
 * The secret back of San Giovanni Battista: "San Giovanni Decollato" (assets/avatar/decollato.png,
 * by avatar.py). No trophy and not in the catalogue: invoking on 29 August or 31 October with
 * the Battista already in the album unlocks it (Trofei.invocazione), then his card can be flipped.
 */
object Retro {

    const val FRONTE = "San Giovanni Battista"
    const val NOME = "San Giovanni Decollato"
    const val FRASE = "Occhio alla testa, San Giovanni decollato!"
    const val FESTA = "08-29"                // the Beheading: his feast on the back of the card
    val GIORNI = setOf(FESTA, "10-31")       // and Halloween

    /** Debug builds: pretend today is this MM-DD (adb shell am start ... -e data 10-31). */
    @Volatile
    var debugOggi: String? = null

    private const val TURN_MS = 160L
    private const val BOUNCE_MS = 450L

    /**
     * Show the flip [button] (outside the card) with a bounce when [saint] is the Battista and his
     * back is unlocked; hide it otherwise.
     * Halfway through the turn of [image] the portrait, the frame and [name] change side;
     * [onFlip] then gets true for the back.
     */
    fun attach(
        scope: LifecycleCoroutineScope, button: ImageView, image: View, avatar: ImageView, frame: ImageView,
        name: TextView, saint: String, onFlip: (Boolean) -> Unit = {},
    ) {
        val context = button.context
        button.visibility = View.GONE
        button.setOnClickListener(null)
        image.animate().cancel()
        image.rotationY = 0f
        if (saint != FRONTE || !Trofei.retroSbloccato(context)) return
        image.cameraDistance = 8000 * context.resources.displayMetrics.density
        var back = false
        var front: Triple<android.graphics.drawable.Drawable?, android.graphics.drawable.Drawable?, Int>? = null
        scope.launch {
            button.setImageDrawable(Avatars.flipIcon(context))
            button.visibility = View.VISIBLE
            button.scaleX = 0.3f; button.scaleY = 0.3f
            button.animate().scaleX(1f).scaleY(1f).setDuration(BOUNCE_MS).setInterpolator(OvershootInterpolator(3f)).start()
        }
        button.setOnClickListener {
            if (image.rotationY != 0f) return@setOnClickListener   // already turning
            image.animate().rotationY(90f).setDuration(TURN_MS).withEndAction {
                scope.launch {
                    if (!back) {
                        front = Triple(avatar.drawable, frame.drawable, frame.visibility)
                        avatar.setImageDrawable(Avatars.decollato(context))
                        frame.setImageDrawable(Avatars.silverFrame(context))
                        frame.visibility = View.VISIBLE
                        name.text = NOME
                    } else {
                        front?.let { (a, f, v) -> avatar.setImageDrawable(a); frame.setImageDrawable(f); frame.visibility = v }
                        name.text = FRONTE
                    }
                    back = !back
                    image.rotationY = -90f
                    image.animate().rotationY(0f).setDuration(TURN_MS).start()
                    onFlip(back)
                }
            }.start()
        }
    }

    fun isRetroDay(monthDay: String) = (debugOggi ?: monthDay) in GIORNI
}
