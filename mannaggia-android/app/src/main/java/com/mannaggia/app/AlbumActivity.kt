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
            show(cards, total)
        }
    }

    /** An album card: the album entry, its card number and its discovery order (#1 = first found). */
    private class Card(val entry: Album.Entry, val number: Int, val discovery: Int)

    private fun show(entries: List<Card>, total: Int) {
        val percent = if (total == 0) 0.0 else entries.size * 100.0 / total
        binding.txtCount.text = getString(
            R.string.album_count, entries.size, total, String.format(Locale.ITALIAN, "%.1f", percent)
        )
        binding.progressAlbum.max = total.coerceAtLeast(1)
        binding.progressAlbum.progress = entries.size
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
        view.findViewById<TextView>(R.id.txtFound).text =
            getString(R.string.album_detail_found_number, card.number, card.discovery) + "\n" + foundOn(entry)
        lifecycleScope.launch {
            Avatars.load(this@AlbumActivity, entry.saint)?.let {
                avatar.setImageDrawable(Avatars.pixelated(this@AlbumActivity, it))
            }
            val feasts = Mannaggia.feastsOf(this@AlbumActivity, entry.saint)
            view.findViewById<TextView>(R.id.txtFeast).text =
                if (feasts.isEmpty()) getString(R.string.album_feast_unknown)
                else getString(R.string.album_feast, feasts.joinToString(", ") { formatDay(it) })
            if (Avatars.isLegendary(this@AlbumActivity, entry.saint)) {
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
            holder.number.text = context.getString(R.string.card_number, card.number)
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
                if (Avatars.isLegendary(context, entry.saint)) {
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
