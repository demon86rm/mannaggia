package com.mannaggia.app

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

/**
 * The favourite saints, chosen in the album: one name per line in the app's private
 * storage (`preferiti.txt`). In the "Preferiti" tab a tap on their card speaks the
 * phrase on demand. Saints are keyed by name, like the album and the audio files.
 */
object Preferiti {

    private const val FILE_NAME = "preferiti.txt"

    /** Loaded on first use; guarded by `this`. */
    private var saints: LinkedHashSet<String>? = null

    suspend fun all(context: Context): Set<String> = withContext(Dispatchers.IO) {
        synchronized(this@Preferiti) { load(context).toSet() }
    }

    suspend fun add(context: Context, names: Collection<String>) = update(context) { it.addAll(names) }

    suspend fun remove(context: Context, names: Collection<String>) = update(context) { it.removeAll(names.toSet()) }

    private suspend fun update(context: Context, change: (LinkedHashSet<String>) -> Unit) =
        withContext(Dispatchers.IO) {
            synchronized(this@Preferiti) {
                val set = load(context)
                change(set)
                file(context).writeText(set.joinToString("") { "$it\n" }, Charsets.UTF_8)
            }
        }

    private fun load(context: Context): LinkedHashSet<String> {
        saints?.let { return it }
        val f = file(context)
        val set = if (f.exists()) f.readLines(Charsets.UTF_8).map { Rinominati.attuale(it.trim()) }.filterTo(LinkedHashSet()) { it.isNotEmpty() }
        else LinkedHashSet()
        saints = set
        return set
    }

    private fun file(context: Context) = File(context.applicationContext.filesDir, FILE_NAME)
}
