package com.mannaggia.app

import android.view.View
import android.view.animation.DecelerateInterpolator
import androidx.lifecycle.LifecycleCoroutineScope
import com.mannaggia.app.databinding.ViewTrophyPopBinding
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * "Trofeo sbloccato" banner: slides down from the top with the pixel-art cup,
 * the trophy name and its reward, plays the jingle and slides back up. Several
 * unlocks are shown one after the other. [busy] postpones the banner while
 * something else is on stage (a legendary card with its choir).
 */
class TrophyPop(
    private val pop: ViewTrophyPopBinding,
    private val scope: LifecycleCoroutineScope,
    private val busy: () -> Boolean,
) {

    private val queue = ArrayDeque<Trofei.Trofeo>()
    private var job: Job? = null

    fun show(trophies: List<Trofei.Trofeo>) {
        if (trophies.isEmpty()) return
        queue.addAll(trophies)
        if (job?.isActive == true) return
        job = scope.launch {
            val context = pop.root.context
            if (pop.imgCup.drawable == null) pop.imgCup.setImageDrawable(Avatars.cup(context))
            while (queue.isNotEmpty()) {
                while (busy()) delay(250)
                val t = queue.removeFirst()
                pop.txtTrophy.text = t.nome
                pop.txtReward.text = t.descrizione
                val root = pop.root
                root.visibility = View.INVISIBLE
                root.post {
                    root.translationY = -(root.height + root.top).toFloat()
                    root.visibility = View.VISIBLE
                    root.animate().translationY(0f).setDuration(SLIDE_MS)
                        .setInterpolator(DecelerateInterpolator()).start()
                }
                Suono(context, R.raw.trofeo).start()
                delay(SLIDE_MS + HOLD_MS)
                root.animate().translationY(-(root.height + root.top).toFloat()).setDuration(SLIDE_MS).start()
                delay(SLIDE_MS + GAP_MS)
                root.visibility = View.GONE
            }
        }
    }

    fun cancel() {
        job?.cancel()
        queue.clear()
        pop.root.animate().cancel()
        pop.root.visibility = View.GONE
    }

    companion object {
        private const val SLIDE_MS = 280L
        private const val HOLD_MS = 2_500L
        private const val GAP_MS = 150L
    }
}
