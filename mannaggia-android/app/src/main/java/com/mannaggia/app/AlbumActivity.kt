package com.mannaggia.app

import android.os.Bundle
import android.text.format.DateFormat
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.mannaggia.app.databinding.ActivityAlbumBinding
import kotlinx.coroutines.launch
import java.util.Date
import java.util.Locale

/** Album: the saints invoked so far, in order of discovery, with the X/total counter. */
class AlbumActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAlbumBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAlbumBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.toolbar.setNavigationOnClickListener { finish() }

        // Edge-to-edge: toolbar below the status bar, list above the navigation bar.
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
        // Reload: the widget or the tile may have found new saints meanwhile.
        lifecycleScope.launch {
            val entries = Album.entries(this@AlbumActivity)
            val total = Mannaggia.saintCount(this@AlbumActivity)
            show(entries, total)
        }
    }

    private fun show(entries: List<Album.Entry>, total: Int) {
        val percent = if (total == 0) 0.0 else entries.size * 100.0 / total
        binding.txtCount.text = getString(
            R.string.album_count, entries.size, total, String.format(Locale.ITALIAN, "%.1f", percent)
        )
        binding.progressAlbum.max = total.coerceAtLeast(1)
        binding.progressAlbum.progress = entries.size
        binding.txtEmpty.visibility = if (entries.isEmpty()) View.VISIBLE else View.GONE
        binding.list.visibility = if (entries.isEmpty()) View.GONE else View.VISIBLE
        binding.list.adapter = AlbumAdapter(entries)
    }

    private class AlbumAdapter(private val entries: List<Album.Entry>) :
        RecyclerView.Adapter<AlbumAdapter.Holder>() {

        class Holder(view: View) : RecyclerView.ViewHolder(view) {
            val number: TextView = view.findViewById(R.id.txtNumber)
            val saint: TextView = view.findViewById(R.id.txtSaint)
            val date: TextView = view.findViewById(R.id.txtDate)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) = Holder(
            LayoutInflater.from(parent.context).inflate(R.layout.item_album, parent, false)
        )

        override fun getItemCount() = entries.size

        override fun onBindViewHolder(holder: Holder, position: Int) {
            val entry = entries[position]
            val context = holder.itemView.context
            holder.number.text = context.getString(R.string.album_number, position + 1)
            holder.saint.text = entry.saint
            val date = Date(entry.discoveredAt)
            holder.date.text = context.getString(
                R.string.album_found_on,
                DateFormat.getMediumDateFormat(context).format(date),
                DateFormat.getTimeFormat(context).format(date)
            )
        }
    }
}
