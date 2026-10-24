package com.mannaggia.app

import android.graphics.Bitmap
import android.graphics.drawable.AnimationDrawable
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.text.format.DateFormat
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.google.android.material.card.MaterialCardView
import com.google.android.material.tabs.TabLayout
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
 *
 * Two tabs: "Album" (every card found) and "Preferiti" (the favourite cards, marked by a
 * banner bookmark). In the album a long press starts a multiple selection to add cards to
 * the favourites; the detail has a bookmark toggle too. In "Preferiti" a tap opens the
 * card's detail and speaks its phrase on demand (whatever the Pronuncia option, and without
 * counting as an invocation for the album or the trophies); a long press opens the detail
 * without the voice.
 */
class AlbumActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAlbumBinding

    private var cards: List<Card> = emptyList()
    private var total = 0
    private var found = 0
    private var favourites: Set<String> = emptySet()
    private var showFavourites = false
    /** Saints selected in selection mode (empty = not selecting). */
    private val selected = linkedSetOf<String>()
    private var bookmarkBitmap: Bitmap? = null

    private var tts: TextToSpeech? = null
    private var ttsReady = false

    private val exitSelection = object : OnBackPressedCallback(false) {
        override fun handleOnBackPressed() = clearSelection()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAlbumBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.toolbar.setNavigationOnClickListener {
            if (selected.isNotEmpty()) clearSelection() else finish()
        }
        binding.toolbar.setOnMenuItemClickListener { item ->
            if (item.itemId == R.id.action_favourite) toggleSelectedFavourites()
            true
        }
        onBackPressedDispatcher.addCallback(this, exitSelection)

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
        binding.tabs.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) {
                showFavourites = tab.position == 1
                clearSelection()
            }
            override fun onTabUnselected(tab: TabLayout.Tab) = Unit
            override fun onTabReselected(tab: TabLayout.Tab) = Unit
        })
        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) {
                val result = tts?.setLanguage(Locale.ITALIAN)
                ttsReady = result != TextToSpeech.LANG_MISSING_DATA && result != TextToSpeech.LANG_NOT_SUPPORTED
            }
        }
        if (savedInstanceState == null) lifecycleScope.launch { Trofei.aperturaAlbum(this@AlbumActivity) }
    }

    override fun onResume() {
        super.onResume()
        // Reload: the widget or the tile may have found new saints meanwhile.
        lifecycleScope.launch {
            bookmarkBitmap = bookmarkBitmap ?: Avatars.bookmark(this@AlbumActivity, true)?.bitmap
            val discovered = Album.entries(this@AlbumActivity)
            total = Mannaggia.saintCount(this@AlbumActivity)
            val found = discovered.mapIndexed { i, e ->
                Card(e, Avatars.number(this@AlbumActivity, e.saint) ?: Int.MAX_VALUE, i + 1)
            }.sortedBy { it.number }
            // Special cards (trophy rewards) come first, S1..S7, with a silver frame.
            val specials = Trofei.TUTTI.filter { it.ricompensa.tipo == Trofei.Tipo.FIGURINA }.mapNotNull { t ->
                val at = Trofei.unlockedAt(this@AlbumActivity, t.id) ?: return@mapNotNull null
                val name = t.ricompensa.valore
                Card(Album.Entry(at, name), Trofei.specialNumber(name) ?: 0, 0, trophy = t)
            }.sortedBy { it.number }
            cards = specials + found
            this@AlbumActivity.found = found.size
            favourites = Preferiti.all(this@AlbumActivity)
            show()
        }
    }

    override fun onDestroy() {
        tts?.shutdown()
        tts = null
        super.onDestroy()
    }

    /**
     * An album card: the album entry, its card number and its discovery order (#1 = first found).
     * Special cards have [trophy] (the one that unlocked them) and number S1..S7.
     */
    private class Card(val entry: Album.Entry, val number: Int, val discovery: Int, val trophy: Trofei.Trofeo? = null) {
        val special get() = trophy != null
    }

    /** Fill the grid for the current tab. */
    private fun show() {
        val entries = if (showFavourites) cards.filter { it.entry.saint in favourites } else cards
        if (showFavourites) {
            binding.txtCount.text = getString(R.string.fav_count, entries.size)
            binding.progressAlbum.visibility = View.GONE
            binding.txtEmpty.setText(R.string.fav_empty)
        } else {
            val percent = if (total == 0) 0.0 else found * 100.0 / total
            binding.txtCount.text = getString(
                R.string.album_count, found, total, String.format(Locale.ITALIAN, "%.1f", percent)
            )
            binding.progressAlbum.visibility = View.VISIBLE
            binding.progressAlbum.max = total.coerceAtLeast(1)
            binding.progressAlbum.progress = found
            binding.txtEmpty.setText(R.string.album_empty)
        }
        binding.txtEmpty.visibility = if (entries.isEmpty()) View.VISIBLE else View.GONE
        binding.list.visibility = if (entries.isEmpty()) View.GONE else View.VISIBLE
        binding.list.adapter = AlbumAdapter(
            entries, lifecycleScope, favourites, selected, bookmarkBitmap,
            onClick = { position, view -> onCardClick(entries[position], view) },
            onLongClick = { position -> onCardLongClick(entries, position) },
        )
        updateToolbar()
    }

    private fun onCardClick(card: Card, view: View) {
        val saint = card.entry.saint
        when {
            selected.isNotEmpty() -> toggleSelection(saint)
            showFavourites -> {                 // the card pops up, as in the album, and speaks
                showDetail(card)
                invokeOnDemand(saint, view)
            }
            else -> showDetail(card)
        }
    }

    private fun onCardLongClick(entries: List<Card>, position: Int) {
        val card = entries[position]
        if (showFavourites) showDetail(card) else toggleSelection(card.entry.saint)
    }

    // --- Favourites tab: on-demand invocation ----------------------------------------------

    /** Speak the card's phrase now: no text, no album or trophy bookkeeping. */
    private fun invokeOnDemand(saint: String, view: View) {
        view.animate().scaleX(0.92f).scaleY(0.92f).setDuration(90).withEndAction {
            view.animate().scaleX(1f).scaleY(1f).setDuration(140).start()
        }.start()
        if (!ttsReady) {
            Toast.makeText(this, R.string.tts_unavailable, Toast.LENGTH_SHORT).show()
            return
        }
        tts?.speak(Pronuncia.perVoce(Mannaggia.phraseOf(saint)), TextToSpeech.QUEUE_FLUSH, null, "preferito")
    }

    // --- Album tab: multiple selection ----------------------------------------------------

    private fun toggleSelection(saint: String) {
        if (!selected.remove(saint)) selected.add(saint)
        binding.list.adapter?.notifyDataSetChanged()
        updateToolbar()
    }

    private fun clearSelection() {
        selected.clear()
        if (::binding.isInitialized) {
            binding.list.adapter?.notifyDataSetChanged()
            show()
        }
    }

    private fun updateToolbar() {
        val selecting = selected.isNotEmpty()
        exitSelection.isEnabled = selecting
        binding.toolbar.menu.clear()
        if (selecting) {
            binding.toolbar.title = getString(R.string.album_selected, selected.size)
            binding.toolbar.inflateMenu(R.menu.album_selection)
            val allFavourites = favourites.containsAll(selected)
            binding.toolbar.menu.findItem(R.id.action_favourite).apply {
                setTitle(if (allFavourites) R.string.fav_remove else R.string.fav_add)
                bookmarkBitmap?.let { icon = menuIcon(it) }
            }
        } else {
            binding.toolbar.setTitle(R.string.album_title)
        }
    }

    /** The pixel-art bookmark scaled (crisp) to the 24dp height of a toolbar icon. */
    private fun menuIcon(bitmap: Bitmap): android.graphics.drawable.Drawable {
        val h = (MENU_ICON_DP * resources.displayMetrics.density).toInt()
        val w = h * bitmap.width / bitmap.height
        val scaled = Bitmap.createScaledBitmap(bitmap, w, h, false).apply { density = resources.displayMetrics.densityDpi }
        return Avatars.pixelated(this, scaled)
    }

    /** Add the selected cards to the favourites, or remove them if they all are already. */
    private fun toggleSelectedFavourites() {
        val names = selected.toList()
        lifecycleScope.launch {
            if (favourites.containsAll(names)) Preferiti.remove(this@AlbumActivity, names)
            else Preferiti.add(this@AlbumActivity, names)
            favourites = Preferiti.all(this@AlbumActivity)
            selected.clear()
            show()
        }
    }

    // --- Detail ---------------------------------------------------------------------------

    /** Bottom sheet with the big portrait, legend badge, feast days, discovery date and bookmark. */
    private fun showDetail(card: Card) {
        val entry = card.entry
        val dialog = BottomSheetDialog(this)
        val view = layoutInflater.inflate(R.layout.dialog_santo, null)
        dialog.setContentView(view)
        val avatar = view.findViewById<ImageView>(R.id.imgAvatar)
        val frame = view.findViewById<ImageView>(R.id.imgFrame)
        val bookmark = view.findViewById<ImageButton>(R.id.btnBookmark)
        view.findViewById<TextView>(R.id.txtSaint).text = entry.saint
        view.findViewById<TextView>(R.id.txtFound).text = if (card.trophy != null)
            getString(R.string.album_detail_special, card.number, card.trophy.nome) + "\n" + foundOn(entry)
        else
            getString(R.string.album_detail_found_number, card.number, card.discovery) + "\n" + foundOn(entry)
        suspend fun showBookmark() {
            val fav = entry.saint in favourites
            bookmark.setImageDrawable(Avatars.bookmark(this@AlbumActivity, fav))
            bookmark.contentDescription = getString(if (fav) R.string.fav_remove else R.string.fav_add)
        }
        bookmark.setOnClickListener {
            lifecycleScope.launch {
                if (entry.saint in favourites) Preferiti.remove(this@AlbumActivity, listOf(entry.saint))
                else Preferiti.add(this@AlbumActivity, listOf(entry.saint))
                favourites = Preferiti.all(this@AlbumActivity)
                showBookmark()
                show()
            }
        }
        lifecycleScope.launch {
            showBookmark()
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
                val sparkle = Avatars.frameDrawable(this@AlbumActivity, entry.saint)
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
        private val favourites: Set<String>,
        private val selected: Set<String>,
        private val bookmark: Bitmap?,
        private val onClick: (Int, View) -> Unit,
        private val onLongClick: (Int) -> Unit,
    ) : RecyclerView.Adapter<AlbumAdapter.Holder>() {

        class Holder(view: View) : RecyclerView.ViewHolder(view) {
            val avatar: ImageView = view.findViewById(R.id.imgAvatar)
            val frame: ImageView = view.findViewById(R.id.imgFrame)
            val bookmark: ImageView = view.findViewById(R.id.imgBookmark)
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
            holder.itemView.setOnClickListener { onClick(holder.bindingAdapterPosition, holder.itemView) }
            holder.itemView.setOnLongClickListener { onLongClick(holder.bindingAdapterPosition); true }
            (holder.itemView as MaterialCardView).isChecked = entry.saint in selected
            if (entry.saint in favourites && bookmark != null) {
                holder.bookmark.setImageDrawable(Avatars.pixelated(context, bookmark))
                holder.bookmark.visibility = View.VISIBLE
            } else {
                holder.bookmark.visibility = View.GONE
            }
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
                    // A recycled cell keeps its animation only if it is the same frame (gold or special).
                    val frameName = Avatars.frameName(context, entry.saint)
                    if (holder.frame.drawable !is AnimationDrawable || holder.frame.tag != frameName) {
                        holder.frame.setImageDrawable(Avatars.frameDrawable(context, entry.saint))
                        holder.frame.tag = frameName
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
        private const val MENU_ICON_DP = 24f
    }
}
