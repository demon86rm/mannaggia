package com.mannaggia.app

import android.content.Context
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

/**
 * Gifts: a saint of your album sent to a friend as a link, opened by their Mannaggia
 * (App Link verified by .well-known/assetlinks.json on demon86rm.github.io). Without
 * the app the link shows a web page with the download links. The sender keeps the card.
 *
 * Link: https://demon86rm.github.io/mannaggia/dono/#s=<saint>&k=<sha1(saint)[:4]>. The saint
 * is in the fragment, so a browser never sends it to the server; the page's "Apri in
 * Mannaggia" button puts it in the query instead, so both are accepted.
 *
 * The link is untrusted input (anyone can write one): only a saint of santi.txt is accepted,
 * so a link can't make the app show or speak arbitrary text. [k] only catches typos: the code
 * is public, and someone gifting themselves cheats only themselves.
 *
 * Gifts are logged in `doni.tsv` (`<epoch millis><TAB><inviato|ricevuto|nuovo><TAB><santo>`),
 * append-only like the album: "nuovo" is a received saint that entered the album with it.
 */
object Dono {

    private const val BASE = "https://demon86rm.github.io/mannaggia/dono/"
    private const val HOST = "demon86rm.github.io"
    private const val PATH = "/mannaggia/dono"
    private const val MAX_LINK = 300
    private const val FILE_NAME = "doni.tsv"

    private const val SENT = "inviato"
    private const val RECEIVED = "ricevuto"
    private const val RECEIVED_NEW = "nuovo"

    fun link(saint: String): String = "$BASE#s=${Uri.encode(saint)}&k=${check(saint)}"

    /** The saint gifted by [uri], or null if it isn't a valid gift link. */
    suspend fun parse(context: Context, uri: Uri?): String? {
        val raw = uri?.toString() ?: return null
        if (raw.length > MAX_LINK || uri.scheme != "https" || uri.host != HOST || uri.path?.startsWith(PATH) != true) return null
        val params = Uri.parse("?" + (uri.encodedFragment ?: uri.encodedQuery ?: return null))
        val saint = params.getQueryParameter("s") ?: return null
        if (params.getQueryParameter("k")?.lowercase() != check(saint)) return null
        val current = Rinominati.attuale(saint)        // a link from an older version
        return current.takeIf { Mannaggia.isSaint(context, it) }
    }

    /** The "Regala" button was tapped: counts as a gift (whether the message is sent can't be known). */
    suspend fun inviato(context: Context, saint: String) = append(context, SENT, saint)

    /** A gift of [saint] arrived; [isNew] if it entered the album with it. Counted once per saint. */
    suspend fun ricevuto(context: Context, saint: String, isNew: Boolean) {
        if (saint in received(context)) return
        append(context, if (isNew) RECEIVED_NEW else RECEIVED, saint)
    }

    /** Gifts made plus saints received (the gift trophies). */
    suspend fun count(context: Context): Int {
        val lines = lines(context)
        return lines.count { it.first == SENT } + lines.filter { it.first != SENT }.map { it.second }.toSet().size
    }

    /** Saints that entered the album as a gift ("Dono" in the album detail). */
    suspend fun arrivedAsGift(context: Context): Set<String> =
        lines(context).filter { it.first == RECEIVED_NEW }.mapTo(HashSet()) { it.second }

    private suspend fun received(context: Context): Set<String> =
        lines(context).filter { it.first != SENT }.mapTo(HashSet()) { it.second }

    private fun check(saint: String): String =
        MessageDigest.getInstance("SHA-1").digest(saint.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }.take(4)

    private suspend fun append(context: Context, kind: String, saint: String) = withContext(Dispatchers.IO) {
        synchronized(this@Dono) {
            file(context).appendText("${System.currentTimeMillis()}\t$kind\t$saint\n", Charsets.UTF_8)
        }
    }

    /** (kind, saint) pairs, saints mapped to their current name. */
    private suspend fun lines(context: Context): List<Pair<String, String>> = withContext(Dispatchers.IO) {
        synchronized(this@Dono) {
            val f = file(context)
            if (!f.exists()) emptyList() else f.readLines(Charsets.UTF_8).mapNotNull { line ->
                val parts = line.split('\t')
                if (parts.size == 3) parts[1] to Rinominati.attuale(parts[2]) else null
            }
        }
    }

    private fun file(context: Context) = File(context.applicationContext.filesDir, FILE_NAME)
}
