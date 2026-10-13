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
        val baseUrl = "https://www.santiebeati.it/$letter/index.html"

        // grep -o 'Pagina 1 di [0-9]*' | awk '{print $4}'
        val indexHtml = httpGet(baseUrl)
        val pages = Regex("""Pagina\s+\d+\s+di\s+(\d+)""")
            .find(indexHtml)
            ?.groupValues?.get(1)
            ?.toIntOrNull()
            ?: 1

        val page = if (pages > 1) Random.nextInt(1, pages + 1) else 1
        val pageUrl = if (page == 1) baseUrl else "$baseUrl?page=$page"

        // grep -o 'dettaglio/[0-9]*"><strong>[^<]*' | sed 's/.*<strong>//'
        val pageHtml = httpGet(pageUrl)
        val saintRegex = Regex("""dettaglio/\d+"><strong>([^<]*)""")

        val saints = saintRegex.findAll(pageHtml)
            .map { unescapeHtml(it.groupValues[1]).trim() }
            .filter { it.isNotBlank() }
            .toList()

        if (saints.isEmpty()) "Sant'Anonimo" else saints.random()
    }

    /** Decode the few HTML entities the site emits in saint names. */
    private fun unescapeHtml(s: String): String = s
        .replace("&#039;", "'")
        .replace("&quot;", "\"")
        .replace("&amp;", "&")

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
