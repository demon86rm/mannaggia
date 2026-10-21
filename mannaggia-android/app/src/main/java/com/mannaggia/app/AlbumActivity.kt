package com.mannaggia.app

import android.graphics.drawable.AnimationDrawable
import android.os.Bundle
import android.text.format.DateFormat
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.mannaggia.app.databinding.ActivityAlbumBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.text.DateFormatSymbols
import java.util.Date
import java.util.Locale

/**
 * Album: the saints invoked so far as pixel-art cards, sorted by card number
 * (N. 1 = most famous; legendary saints first, with a sparkling gold frame),
 * with the X/total counter. Tapping a card opens its detail.
 */
class AlbumActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAlbumBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAlbumBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.toolbar.setNavigationOnClickListener { finish() }

        // Edge-to-edge: toolbar below the status bar, grid above the navigation bar.
        ViewCompat.setOnApplyWindowInsetsListener(binding.root) { view, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
            )
            view.setPadding(bars.left, bars.top, bars.right, 0)
            binding.list.setPadding(6, 0, 6, bars.bottom)
            insets
        }

        binding.list.layoutManager = GridLayoutManager(this, COLUMNS)
        if (savedInstanceState == null) lifecycleScope.launch { Trofei.aperturaAlbum(this@AlbumActivity) }
    }

    override fun onResume() {
        super.onResume()
        // Reload: the widget or the tile may have found new saints meanwhile.
        lifecycleScope.launch {
            val discovered = Album.entries(this@AlbumActivity)
            val total = Mannaggia.saintCount(this@AlbumActivity)
            val cards = discovered.mapIndexed { i, e ->
                Card(e, Avatars.number(this@AlbumActivity, e.saint) ?: Int.MAX_VALUE, i + 1)
            }.sortedBy { it.number }
            // Special cards (trophy rewards) come first, S1..S6, with a silver frame.
            val specials = Trofei.TUTTI.filter { it.ricompensa.tipo == Trofei.Tipo.FIGURINA }.mapNotNull { t ->
                val at = Trofei.unlockedAt(this@AlbumActivity, t.id) ?: return@mapNotNull null
                val name = t.ricompensa.valore
                Card(Album.Entry(at, name), Trofei.specialNumber(name) ?: 0, 0, trophy = t)
            }.sortedBy { it.number }
            show(specials + cards, total, cards.size)
        }
    }

    /**
     * An album card: the album entry, its card number and its discovery order (#1 = first found).
     * Special cards have [trophy] (the one that unlocked them) and number S1..S6.
     */
    private class Card(val entry: Album.Entry, val number: Int, val discovery: Int, val trophy: Trofei.Trofeo? = null) {
        val special get() = trophy != null
    }

    private fun show(entries: List<Card>, total: Int, found: Int = entries.size) {
        val percent = if (total == 0) 0.0 else found * 100.0 / total
        binding.txtCount.text = getString(
            R.string.album_count, found, total, String.format(Locale.ITALIAN, "%.1f", percent)
        )
        binding.progressAlbum.max = total.coerceAtLeast(1)
        binding.progressAlbum.progress = found
        binding.txtEmpty.visibility = if (entries.isEmpty()) View.VISIBLE else View.GONE
        binding.list.visibility = if (entries.isEmpty()) View.GONE else View.VISIBLE
        binding.list.adapter = AlbumAdapter(entries, lifecycleScope) { position -> showDetail(entries, position) }
    }

    /** Bottom sheet with the big portrait, legend badge, feast days and discovery date. */
    private fun showDetail(entries: List<Card>, position: Int) {
        val card = entries[position]
        val entry = card.entry
        val dialog = BottomSheetDialog(this)
        val view = layoutInflater.inflate(R.layout.dialog_santo, null)
        dialog.setContentView(view)
        val avatar = view.findViewById<ImageView>(R.id.imgAvatar)
        val frame = view.findViewById<ImageView>(R.id.imgFrame)
        view.findViewById<TextView>(R.id.txtSaint).text = entry.saint
        view.findViewById<TextView>(R.id.txtFound).text = if (card.trophy != null)
            getString(R.string.album_detail_special, card.number, card.trophy.nome) + "\n" + foundOn(entry)
        else
            getString(R.string.album_detail_found_number, card.number, card.discovery) + "\n" + foundOn(entry)
        lifecycleScope.launch {
            Avatars.load(this@AlbumActivity, entry.saint)?.let {
                avatar.setImageDrawable(Avatars.pixelated(this@AlbumActivity, it))
            }
            val feasts = Mannaggia.feastsOf(this@AlbumActivity, entry.saint)
            view.findViewById<TextView>(R.id.txtFeast).text =
                if (card.special) getString(R.string.album_feast_special)
                else if (feasts.isEmpty()) getString(R.string.album_feast_unknown)
                else getString(R.string.album_feast, feasts.joinToString(", ") { formatDay(it) })
            if (card.special) {
                frame.setImageDrawable(Avatars.silverFrame(this@AlbumActivity))
                frame.visibility = View.VISIBLE
            } else if (Avatars.isLegendary(this@AlbumActivity, entry.saint)) {
                view.findViewById<TextView>(R.id.txtLegend).visibility = View.VISIBLE
                val sparkle = Avatars.frameDrawable(this@AlbumActivity)
                frame.setImageDrawable(sparkle)
                frame.visibility = View.VISIBLE
                sparkle.start()
            }
        }
        dialog.show()
    }

    private fun foundOn(entry: Album.Entry): String {
        val date = Date(entry.discoveredAt)
        return getString(
            R.string.album_found_on,
            DateFormat.getMediumDateFormat(this).format(date),
            DateFormat.getTimeFormat(this).format(date)
        )
    }

    /** "10-04" → "4 ottobre". */
    private fun formatDay(mmdd: String): String {
        val (month, day) = mmdd.split('-').map { it.toInt() }
        return "$day ${DateFormatSymbols(Locale.ITALIAN).months[month - 1]}"
    }

    private class AlbumAdapter(
        private val entries: List<Card>,
        private val scope: CoroutineScope,
        private val onClick: (Int) -> Unit,
    ) : RecyclerView.Adapter<AlbumAdapter.Holder>() {

        class Holder(view: View) : RecyclerView.ViewHolder(view) {
            val avatar: ImageView = view.findViewById(R.id.imgAvatar)
            val frame: ImageView = view.findViewById(R.id.imgFrame)
            val number: TextView = view.findViewById(R.id.txtNumber)
            val saint: TextView = view.findViewById(R.id.txtSaint)
            var job: Job? = null
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) = Holder(
            LayoutInflater.from(parent.context).inflate(R.layout.item_figurina, parent, false)
        )

        override fun getItemCount() = entries.size

        override fun onBindViewHolder(holder: Holder, position: Int) {
            val card = entries[position]
            val entry = card.entry
            val context = holder.itemView.context
            holder.number.text = context.getString(
                if (card.special) R.string.card_number_special else R.string.card_number, card.number
            )
            holder.saint.text = entry.saint
            holder.itemView.setOnClickListener { onClick(holder.bindingAdapterPosition) }
            holder.avatar.setImageDrawable(null)
            holder.frame.visibility = View.GONE
            // Recycled views: cancel the load of the saint previously shown here.
            holder.job?.cancel()
            holder.job = scope.launch {
                Avatars.load(context, entry.saint)?.let {
                    holder.avatar.setImageDrawable(Avatars.pixelated(context, it))
                }
                if (card.special) {
                    holder.frame.setImageDrawable(Avatars.silverFrame(context))
                    holder.frame.visibility = View.VISIBLE
                } else if (Avatars.isLegendary(context, entry.saint)) {
                    if (holder.frame.drawable !is AnimationDrawable) {
                        holder.frame.setImageDrawable(Avatars.frameDrawable(context))
                    }
                    holder.frame.visibility = View.VISIBLE
                    (holder.frame.drawable as AnimationDrawable).start()
                }
            }
        }

        // Only cards on screen sparkle.
        override fun onViewAttachedToWindow(holder: Holder) {
            if (holder.frame.visibility == View.VISIBLE) (holder.frame.drawable as? AnimationDrawable)?.start()
        }

        override fun onViewDetachedFromWindow(holder: Holder) {
            (holder.frame.drawable as? AnimationDrawable)?.stop()
        }
    }

    companion object {
        private const val COLUMNS = 3
    }
}
