package com.mannaggia.app

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/**
 * The saints the user has already invoked, in order of discovery.
 *
 * Stored as an append-only file (`<epoch millis><TAB><santo>` per line) in the
 * app's private storage, so it survives updates and is covered by Android backup.
 * Saints are keyed by name, like the audio files: santi.txt should not be
 * regenerated without reason (see CLAUDE.md).
 */
object Album {

    private const val FILE_NAME = "album.tsv"

    data class Entry(val discoveredAt: Long, val saint: String)

    /** Loaded on first use; guarded by `this` (MainActivity, widget and tile may write). */
    private var entries: MutableList<Entry>? = null
    private var known: MutableSet<String>? = null

    /** Add [saint] if it is new. Returns true when it was not in the album yet. */
    suspend fun record(context: Context, saint: String): Boolean = withContext(Dispatchers.IO) {
        synchronized(this@Album) {
            val list = load(context)
            if (!known!!.add(saint)) return@synchronized false
            val entry = Entry(System.currentTimeMillis(), saint)
            list.add(entry)
            file(context).appendText("${entry.discoveredAt}\t${entry.saint}\n", Charsets.UTF_8)
            true
        }
    }

    /** All discovered saints, first discovery first. */
    suspend fun entries(context: Context): List<Entry> = withContext(Dispatchers.IO) {
        synchronized(this@Album) { load(context).toList() }
    }

    private fun load(context: Context): MutableList<Entry> {
        entries?.let { return it }
        val f = file(context)
        val list = if (!f.exists()) mutableListOf() else f.readLines(Charsets.UTF_8).mapNotNull { line ->
            val tab = line.indexOf('\t')
            val time = if (tab > 0) line.substring(0, tab).toLongOrNull() else null
            if (time == null) null else Entry(time, line.substring(tab + 1))
        }.distinctBy { it.saint }.toMutableList()
        entries = list
        known = list.mapTo(HashSet()) { it.saint }
        return list
    }

    private fun file(context: Context) = File(context.applicationContext.filesDir, FILE_NAME)
}
