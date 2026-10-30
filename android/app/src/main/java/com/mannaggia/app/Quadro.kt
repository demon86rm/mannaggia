package com.mannaggia.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import android.text.TextUtils
import androidx.core.content.res.ResourcesCompat

/**
 * "I miei santi": up to 9 favourite cards in centred, symmetric rows (5 = 2-1-2, 7 = 2-3-2,
 * 8 = 3-2-3), names under the portraits, a title on top and one of the animated frames
 * stretched around the whole picture (corners kept, the plain middle of each side repeated).
 * Drawn in avatar pixels, then scaled up by an integer factor so the pixels stay crisp.
 */
class Quadro private constructor(
    private val context: Context,
    private val cards: List<Card>,
    private val frame: List<Bitmap>,
) {
    /** A portrait with its own animated (or still) frame, if any. */
    class Card(val name: String, val portrait: Bitmap, val frame: List<Bitmap>?)

    private val rows = RIGHE.getValue(cards.size)
    val width = maxOf(MIN_W, SIDE * 2 + rows.max() * CELL + (rows.max() - 1) * GAP_X)
    val height = TOP + rows.size * (CELL + LABEL) + (rows.size - 1) * GAP_Y + BOTTOM

    /** Frame [step] of the animation, [zoom] times bigger. */
    fun render(step: Int, zoom: Int): Bitmap {
        val small = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val c = Canvas(small)
        c.drawColor(PAPER)
        val slots = slots()
        for ((card, x, y) in slots) {
            c.drawBitmap(card.portrait, x.toFloat(), y.toFloat(), null)
            card.frame?.let { c.drawBitmap(it[step % it.size], x.toFloat(), y.toFloat(), null) }
        }
        stretch(c, frame[step % frame.size])
        val big = Bitmap.createScaledBitmap(small, width * zoom, height * zoom, false)
        small.recycle()
        val bc = Canvas(big)
        val font = ResourcesCompat.getFont(context, R.font.unifraktur_maguntia)
        val title = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            typeface = font; color = INK; textSize = TITLE_SIZE * zoom; textAlign = Paint.Align.CENTER
        }
        bc.drawText(context.getString(R.string.quadro_title), width * zoom / 2f, TITLE_Y * zoom, title)
        val label = TextPaint(Paint.ANTI_ALIAS_FLAG).apply { typeface = font; color = INK; textSize = NAME_SIZE * zoom }
        val labelW = (CELL + GAP_X - 2) * zoom
        for ((card, x, y) in slots) {
            val text = StaticLayout.Builder.obtain(card.name, 0, card.name.length, label, labelW)
                .setAlignment(Layout.Alignment.ALIGN_CENTER).setMaxLines(2)
                .setEllipsize(TextUtils.TruncateAt.END).setIncludePad(false).build()
            bc.save()
            bc.translate((x + CELL / 2f) * zoom - labelW / 2f, (y + CELL + 1f) * zoom)
            text.draw(bc)
            bc.restore()
        }
        return big
    }

    private fun slots(): List<Triple<Card, Int, Int>> {
        val out = mutableListOf<Triple<Card, Int, Int>>()
        var i = 0
        rows.forEachIndexed { r, n ->
            val x0 = (width - (n * CELL + (n - 1) * GAP_X)) / 2
            val y = TOP + r * (CELL + LABEL + GAP_Y)
            repeat(n) { k -> out += Triple(cards[i++], x0 + k * (CELL + GAP_X), y) }
        }
        return out
    }

    /** The frame, twice as big, around the whole picture: corners kept, sides tiled. */
    private fun stretch(c: Canvas, f1: Bitmap) {
        val f = Bitmap.createScaledBitmap(f1, f1.width * 2, f1.height * 2, false)
        val n = f.width
        val k = CORNER * 2
        val mid = n - 2 * k
        fun put(sx: Int, sy: Int, sw: Int, sh: Int, dx: Int, dy: Int) =
            c.drawBitmap(f, Rect(sx, sy, sx + sw, sy + sh), Rect(dx, dy, dx + sw, dy + sh), null)
        var x = k
        while (x < width - k) {
            val w = minOf(mid, width - k - x)
            put(k, 0, w, k, x, 0); put(k, n - k, w, k, x, height - k)
            x += mid
        }
        var y = k
        while (y < height - k) {
            val h = minOf(mid, height - k - y)
            put(0, k, k, h, 0, y); put(n - k, k, k, h, width - k, y)
            y += mid
        }
        put(0, 0, k, k, 0, 0); put(n - k, 0, k, k, width - k, 0)
        put(0, n - k, k, k, 0, height - k); put(n - k, n - k, k, k, width - k, height - k)
        f.recycle()
    }

    companion object {
        const val MAX = 9
        val RIGHE = mapOf(1 to listOf(1), 2 to listOf(2), 3 to listOf(3), 4 to listOf(2, 2), 5 to listOf(2, 1, 2),
            6 to listOf(3, 3), 7 to listOf(2, 3, 2), 8 to listOf(3, 2, 3), 9 to listOf(3, 3, 3))
        private const val CELL = 48
        private const val GAP_X = 10
        private const val GAP_Y = 6
        private const val LABEL = 13
        private const val SIDE = 28
        private const val TOP = 48
        private const val BOTTOM = 22
        private const val MIN_W = 160            // room for the title with a single saint
        private const val CORNER = 14            // corner decorations (gems, nails, candles) stay whole
        private const val TITLE_Y = 32f
        private const val TITLE_SIZE = 14f
        private const val NAME_SIZE = 4.5f
        private val PAPER = Color.rgb(246, 238, 220)
        private val INK = Color.rgb(60, 30, 30)

        /** The picture of [saints] (1 to [MAX]) in the frame [frameName]. */
        suspend fun of(context: Context, saints: List<String>, frameName: String): Quadro {
            require(saints.size in 1..MAX)
            val cards = saints.map { s ->
                val own = when {
                    Trofei.isSpecial(s) -> Avatars.silverFrame(context)?.bitmap?.let { listOf(it) }
                    else -> Avatars.frameName(context, s)?.let { Avatars.frameBitmaps(context, it) }
                }
                Card(s, Avatars.load(context, s) ?: Bitmap.createBitmap(CELL, CELL, Bitmap.Config.ARGB_8888), own)
            }
            return Quadro(context, cards, Avatars.frameBitmaps(context, frameName))
        }
    }
}
