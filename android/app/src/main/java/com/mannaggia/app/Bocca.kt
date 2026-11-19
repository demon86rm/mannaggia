package com.mannaggia.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color

/**
 * The mouth of the 96 px portraits, drawn over the portrait like the eyes ([Occhi]), so it can move with the
 * emotions. The forms come from assets/avatar/bocche.txt and each saint's form at rest and colours from
 * bocca96.tsv, both written by tools/ritratti96/occhi96.py from bocca.px.js: the drawing stays in one place.
 * Only the saints of santi.txt have a row: the special cards keep the mouth drawn in their portrait.
 *
 * A form is a list of rows from y 53 of the 94 px figure (+1 in the portrait, its outline), columns dx -7..7:
 * L the mouth's line, l the lip, h its light, s skin shadow, K the inside, anything else left as it is.
 */
object Bocca {

    /** A saint's mouth: the form at rest, under a beard or not, the colours by key, and all the forms. */
    class Params(val form: String, val beard: Boolean, val colors: Map<Char, Int>, val forms: Map<String, List<String?>>)

    private const val DIR = "avatar"
    private const val OFF = 1                      // the portrait's outline
    private const val CX = 47 + OFF
    private const val Y0 = 53 + OFF

    @Volatile private var params: Map<String, Params>? = null

    private fun lines(context: Context, file: String) =
        context.applicationContext.assets.open("$DIR/$file").bufferedReader(Charsets.UTF_8).useLines { l ->
            l.filter { it.isNotBlank() && !it.startsWith("#") }.map { it.split('\t') }.toList()
        }

    /** The mouth of the portrait [fileId] (see [Avatars.fileId]), or null if its portrait has the mouth drawn in. */
    fun params(context: Context, fileId: String): Params? {
        val map = params ?: runCatching {
            val forms = lines(context, "bocche.txt").associate { (name, rows) -> name to rows.split(';').map { it.takeIf { r -> r != "-" } } }
            lines(context, "bocca96.tsv").filter { it.size >= 8 }.associate { c ->
                c[0] to Params(c[1], c[2] == "1",
                    mapOf('s' to c[3], 'L' to c[4], 'l' to c[5], 'h' to c[6], 'K' to c[7]).mapValues { Color.parseColor(it.value) }, forms)
            }
        }.getOrDefault(emptyMap()).also { params = it }
        return map[fileId]
    }

    /** The form of a step: the saint's own at rest (""), else the emotion's, its bearded version under a beard (formaBocca()). */
    private fun form(rest: String, m: String, beard: Boolean) = when {
        m.isEmpty() -> rest
        m == "s" -> if (beard) "B2" else "M1"
        beard -> "B$m"
        else -> m
    }

    /** Draws the mouth of step [m] on [b], which holds the portrait with the mouth's zone in plain skin. */
    fun draw(b: Bitmap, p: Params, m: String) {
        val rows = p.forms[form(p.form, m, p.beard)] ?: return
        rows.forEachIndexed { i, row ->
            row?.forEachIndexed { j, ch ->
                val c = p.colors[ch] ?: return@forEachIndexed
                val x = CX + j - 7
                val y = Y0 + i
                if (x in 0 until b.width && y in 0 until b.height) b.setPixel(x, y, c)
            }
        }
    }
}
