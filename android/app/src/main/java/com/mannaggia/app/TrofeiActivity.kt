package com.mannaggia.app

import android.graphics.ColorMatrix
import android.graphics.ColorMatrixColorFilter
import android.os.Bundle
import android.text.format.DateFormat
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.mannaggia.app.databinding.ActivityTrofeiBinding
import kotlinx.coroutines.launch
import java.util.Date

/**
 * Trophies: unlocked ones show cup, name, reward and date, and a tap opens the detail with
 * the condition (not in the list, so a screenshot of it doesn't spoil how to win them);
 * locked ones are a grey cup and "???", with no hint.
 */
class TrofeiActivity : AppCompatActivity() {

    private lateinit var binding: ActivityTrofeiBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityTrofeiBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.toolbar.setNavigationOnClickListener { finish() }
        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
            )
            view.setPadding(bars.left, bars.top, bars.right, 0)
            binding.list.setPadding(0, 0, 0, bars.bottom)
            insets
        }
        binding.list.layoutManager = LinearLayoutManager(this)
    }

    override fun onResume() {
        super.onResume()
        binding.txtCount.text = getString(
            R.string.trophies_count, Trofei.unlockedCount(this), Trofei.TUTTI.size
        )
        lifecycleScope.launch {
            val cup = Avatars.cup(this@TrofeiActivity)?.bitmap
            // Unlocked first (most recent first), then the locked ones.
            val sorted = Trofei.TUTTI.sortedByDescending { Trofei.unlockedAt(this@TrofeiActivity, it.id) ?: 0L }
            binding.list.adapter = Adapter(sorted, cup)
        }
    }

    private inner class Adapter(
        private val items: List<Trofei.Trofeo>,
        private val cup: android.graphics.Bitmap?,
    ) : RecyclerView.Adapter<Adapter.Holder>() {

        inner class Holder(view: View) : RecyclerView.ViewHolder(view) {
            val cup: ImageView = view.findViewById(R.id.imgCup)
            val name: TextView = view.findViewById(R.id.txtName)
            val condition: TextView = view.findViewById(R.id.txtCondition)
            val reward: TextView = view.findViewById(R.id.txtReward)
            val date: TextView = view.findViewById(R.id.txtDate)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
            Holder(LayoutInflater.from(parent.context).inflate(R.layout.item_trofeo, parent, false))

        override fun getItemCount() = items.size

        override fun onBindViewHolder(holder: Holder, position: Int) {
            val t = items[position]
            val at = Trofei.unlockedAt(this@TrofeiActivity, t.id)
            cup?.let { holder.cup.setImageDrawable(Avatars.pixelated(this@TrofeiActivity, it)) }
            if (at != null) {
                holder.cup.colorFilter = null
                holder.cup.alpha = 1f
                holder.name.text = t.nome
                holder.condition.visibility = View.GONE
                holder.reward.text = t.descrizione
                holder.reward.visibility = View.VISIBLE
                val d = Date(at)
                holder.date.text = getString(
                    R.string.trophy_unlocked_on,
                    DateFormat.getMediumDateFormat(this@TrofeiActivity).format(d),
                    DateFormat.getTimeFormat(this@TrofeiActivity).format(d)
                )
                holder.date.visibility = View.VISIBLE
                holder.itemView.setOnClickListener {
                    AlertDialog.Builder(this@TrofeiActivity)
                        .setTitle(t.nome)
                        .setMessage(listOf(t.condizione, t.descrizione, holder.date.text).joinToString("\n\n"))
                        .setPositiveButton(android.R.string.ok, null)
                        .show()
                }
            } else {
                // Locked: grey cup, no name, no hint.
                holder.cup.colorFilter = ColorMatrixColorFilter(ColorMatrix().apply { setSaturation(0f) })
                holder.cup.alpha = 0.45f
                holder.name.text = getString(R.string.trophy_locked)
                holder.condition.text = getString(R.string.trophy_locked_hint)
                holder.condition.visibility = View.VISIBLE
                holder.reward.visibility = View.GONE
                holder.date.visibility = View.GONE
                holder.itemView.setOnClickListener(null)
                holder.itemView.isClickable = false
            }
        }
    }
}
