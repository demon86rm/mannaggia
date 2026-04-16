package com.mannaggia.app

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import kotlin.random.Random

/**
 * Shared scraping logic — the port of mannaggia.sh lives here so it can be
 * called from MainActivity, MannaggiaTileService and MannaggiaWidgetProvider.
 */
object Mannaggia {

    /** Build the final phrase shown to the user. */
    fun phraseOf(saint: String): String = "Mannaggia $saint!"

    /** Pick a random letter → scrape santiebeati.it → return a saint name. */
    suspend fun fetchRandomSaint(): String = withContext(Dispatchers.IO) {
        val letter = ('A'..'Z').random()
        val baseUrl = "https://www.santiebeati.it/$letter/"

        // awk -F'more|\.html' '/Pagina:/{print $(NF-1); exit}'
        val indexHtml = httpGet(baseUrl)
        val pages = indexHtml.lineSequence()
            .firstOrNull { "Pagina:" in it }
            ?.split(Regex("""more|\.html"""))
            ?.let { parts -> parts.getOrNull(parts.size - 2) }
            ?.trim()
            ?.toIntOrNull()
            ?: 1

        val page = if (pages > 1) Random.nextInt(1, pages + 1) else 1
        val pageUrl = if (page == 1) baseUrl else "${baseUrl}more$page.html"

        // awk -F'<FONT SIZE="-2">|</FONT> <FONT SIZE="-1"><b>|</b>' \
        //     '/<a href="\/dettaglio\/.*<FONT/{print $2,$3}'
        val pageHtml = httpGet(pageUrl)
        val lineFilter = Regex("""<a href="/dettaglio/.*<FONT""")
        val fieldSep = Regex("""<FONT SIZE="-2">|</FONT> <FONT SIZE="-1"><b>|</b>""")

        val saints = pageHtml.lineSequence()
            .filter { lineFilter.containsMatchIn(it) }
            .mapNotNull { line ->
                val parts = line.split(fieldSep)
                if (parts.size >= 3) "${parts[1]} ${parts[2]}".trim() else null
            }
            .filter { it.isNotBlank() }
            .toList()

        if (saints.isEmpty()) "Sant'Anonimo" else saints.random()
    }

    /** HTTP GET decoded as UTF-8 (equivalent to `iconv -f UTF-8`). */
    private fun httpGet(urlStr: String): String {
        val conn = (URL(urlStr).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            setRequestProperty("User-Agent", "Mozilla/5.0 Mannaggia-Android")
            connectTimeout = 10_000
            readTimeout = 15_000
        }
        try {
            val bytes = conn.inputStream.use { it.readBytes() }
            return String(bytes, Charsets.UTF_8)
        } finally {
            conn.disconnect()
        }
    }
}
