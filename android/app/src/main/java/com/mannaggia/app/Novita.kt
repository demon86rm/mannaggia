package com.mannaggia.app

import android.content.Context
import android.graphics.Typeface
import android.text.SpannableStringBuilder
import android.text.style.RelativeSizeSpan
import android.text.style.StyleSpan
import androidx.core.text.inSpans

/** The changelog in assets/novita.txt: "## <version>" blocks, newest first (# lines are comments). */
object Novita {

    /** Version -> its lines, in file order. */
    fun blocchi(context: Context): List<Pair<String, List<String>>> {
        val out = mutableListOf<Pair<String, MutableList<String>>>()
        context.assets.open("novita.txt").bufferedReader(Charsets.UTF_8).useLines { lines ->
            for (line in lines) when {
                line.startsWith("## ") -> out += line.removePrefix("## ").trim() to mutableListOf()
                line.startsWith("#") || line.isBlank() -> Unit
                else -> out.lastOrNull()?.second?.add(line.trim())
            }
        }
        return out
    }

    /** The lines of [version] ("2.1.1"; a "-debug" suffix is ignored), or null if not listed. */
    fun blocco(context: Context, version: String): List<String>? =
        blocchi(context).firstOrNull { it.first == version.substringBefore('-') }?.second

    /** The whole changelog, with bold version headers. */
    fun testo(context: Context): CharSequence = SpannableStringBuilder().apply {
        for ((version, lines) in blocchi(context)) {
            if (isNotEmpty()) append("\n\n")
            inSpans(StyleSpan(Typeface.BOLD), RelativeSizeSpan(1.15f)) { append(version) }
            append("\n").append(lines.joinToString("\n"))
        }
    }
}
