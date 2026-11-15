package com.mannaggia.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.ColorFilter
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.Rect
import android.graphics.drawable.Animatable
import android.graphics.drawable.Drawable
import android.os.SystemClock
import kotlin.math.max
import kotlin.random.Random

/**
 * The eyes of the 96 px portraits. The portraits in assets/avatar/ have no eyes: they are drawn here,
 * on top, so they can move. This is a port of `occhi()` and `occhiali()` in tools/ritratti96/occhi.px.js,
 * and the six emotions are read from assets/avatar/emozioni.txt (made from the same file), so the
 * drawing stays in one place. Per-saint colours are in assets/avatar/occhi96.tsv.
 *
 * Coordinates are those of the 94 px figure plus 1 (the portrait has a 1 px outline round it).
 */
object Occhi {

    /** One step of an emotion (12 steps per second): gaze, lid, brows, worried inner brows, small pupil. */
    class Step(val dx: Int, val dy: Int, val lid: Char, val browL: Int, val browR: Int, val worry: Boolean, val small: Boolean)

    /**
     * What changes from saint to saint: the iris' middle tone (its dark and light tones are mixed from it),
     * the brows and their outer tail, the skin tone of the lid's crease and of the lower lid, a "mono" eye
     * (no crease), glasses, bushy brows (three rows, old men).
     */
    class Params(val iris: Int, val brows: Int, val skin: Int, val mono: Boolean, val glasses: Boolean, val tail: Int, val bushy: Boolean)

    const val STEP_MS = 83L
    private const val DIR = "avatar"
    private const val OFF = 1                      // the portrait's outline
    private const val CX = 47 + OFF
    private const val EYE_Y = 41 + OFF
    private const val BROW_Y = 36 + OFF
    private const val TOP = 33 + OFF                // the eye zone's top row: the brows never go above it
    private val WHITE = Color.parseColor("#fff6ea")
    private val DARK = Color.parseColor("#2a2228")       // the pupil
    private val LID = Color.parseColor("#2a1a18")
    private val SHADOW = Color.parseColor("#d9cfd2")     // the lid's shadow on the white's top row
    private val FRAME = Color.parseColor("#7c6c78")      // glasses: lighter than the lid, so they do not merge
    private val GLINT = Color.WHITE
    private val OPEN = Step(0, 0, 'n', 0, 0, false, false)

    @Volatile private var params: Map<String, Params>? = null
    @Volatile private var emotions: Map<String, List<Step>>? = null

    private val fallback = Params(Color.parseColor("#5a4636"), Color.BLACK, Color.parseColor("#d78146"), false, false, Color.BLACK, false)

    /** The brows' rows for i = 0 (inner end) .. 6 (outer end), relative to BROW_Y; three rows when bushy. */
    private val BROWS = arrayOf(intArrayOf(0, 1), intArrayOf(0, 1), intArrayOf(-1, 0), intArrayOf(-1, 0), intArrayOf(-1, 0), intArrayOf(0), intArrayOf(1))
    private val BUSHY = arrayOf(intArrayOf(-1, 0, 1), intArrayOf(-1, 0, 1), intArrayOf(-2, -1, 0), intArrayOf(-2, -1, 0),
        intArrayOf(-2, -1, 0), intArrayOf(-1, 0), intArrayOf(0, 1))

    /** [a] moved towards [b] by [t], rounded as JavaScript's Math.round (occhi.px.js mixes the same way). */
    private fun mix(a: Int, b: Int, t: Double): Int {
        fun ch(x: Int, y: Int) = kotlin.math.floor(x + (y - x) * t + 0.5).toInt()
        return Color.rgb(ch(Color.red(a), Color.red(b)), ch(Color.green(a), Color.green(b)), ch(Color.blue(a), Color.blue(b)))
    }

    /** The eye parameters of the portrait [fileId] (see [Avatars.fileId]). */
    fun params(context: Context, fileId: String): Params {
        val map = params ?: runCatching {
            context.applicationContext.assets.open("$DIR/occhi96.tsv").bufferedReader(Charsets.UTF_8).useLines { lines ->
                lines.filter { it.isNotBlank() && !it.startsWith("#") }.mapNotNull { line ->
                    val c = line.split('\t')
                    // 8 columns; a file of the old eyes has 6 (no tail, no bushy flag): the tail is then the brows' colour
                    if (c.size < 6) null else c[0] to Params(
                        Color.parseColor(c[1]), Color.parseColor(c[2]), Color.parseColor(c[3]), c[4] == "mono", c[5] == "1",
                        if (c.size >= 8) Color.parseColor(c[6]) else Color.parseColor(c[2]), c.size >= 8 && c[7] == "1")
                }.toMap()
            }
        }.getOrDefault(emptyMap()).also { params = it }
        return map[fileId] ?: fallback
    }

    /** The emotions by name, from emozioni.txt. */
    fun emotions(context: Context): Map<String, List<Step>> =
        emotions ?: runCatching {
            context.applicationContext.assets.open("$DIR/emozioni.txt").bufferedReader(Charsets.UTF_8).useLines { lines ->
                lines.filter { it.isNotBlank() && !it.startsWith("#") }.associate { line ->
                    val (name, steps) = line.split('\t')
                    name to steps.split(';').map { s ->
                        val f = s.split(',')
                        Step(f[0].toInt(), f[1].toInt(), f[2][0], f[3].toInt(), f[4].toInt(), f[5] == "1", f[6] == "1")
                    }
                }
            }
        }.getOrDefault(emptyMap()).also { emotions = it }

    /** A random emotion for a saint that has just been shown; [only] fixes it for saints that always look the same way. */
    fun randomEmotion(context: Context, only: String? = null): List<Step> {
        val all = emotions(context)
        return (only?.let { all[it] }) ?: all.values.toList().let { if (it.isEmpty()) listOf(OPEN) else it[Random.nextInt(it.size)] }
    }

    /** A copy of [base] (the portrait without eyes) with the eyes open and still. */
    fun still(base: Bitmap, p: Params): Bitmap =
        base.copy(Bitmap.Config.ARGB_8888, true).also { draw(it, p, OPEN) }

    /** Draws one step on [b], which already holds the portrait without eyes: a line-by-line port of occhi(). */
    fun draw(b: Bitmap, p: Params, f: Step) {
        fun px(x: Int, y: Int, c: Int) { if (x in 0 until b.width && y in 0 until b.height) b.setPixel(x, y, c) }
        fun hline(x: Int, y: Int, n: Int, c: Int) { for (i in 0 until n) px(x + i, y, c) }
        fun vline(x: Int, y: Int, n: Int, c: Int) { for (i in 0 until n) px(x, y + i, c) }
        val y = EYE_Y
        val iris = intArrayOf(mix(p.iris, Color.BLACK, 0.45), p.iris, mix(p.iris, Color.WHITE, 0.3))
        val rowsOf = if (p.bushy) BUSHY else BROWS
        for ((lato, ex) in listOf(CX - 11, CX + 10).withIndex()) {
            val out = if (lato == 1) 1 else -1
            val lidRow = when (f.lid) { 'w' -> y - 2; 'd' -> y; 'h', 'x' -> y + 1; else -> y - 1 }
            if (!p.mono) hline(ex - 3, y - 3, 7, p.skin)                    // the crease
            for (yy in y - 1 until lidRow) hline(ex - 3, yy, 7, p.skin)    // the lowered lid's skin
            val brow = if (lato == 0) f.browL else f.browR                  // the brows, never above the eye zone
            val off = max(brow, TOP - (BROW_Y + (if (p.bushy) -2 else -1) - (if (f.worry) 1 else 0)))
            rowsOf.forEachIndexed { i, rows ->
                rows.forEachIndexed { k, r ->
                    val yy = BROW_Y + off + r - (if (f.worry && i <= 2) 1 else 0)
                    px(ex + out * (i - 1), yy, if (i >= 5 || (p.bushy && k == rows.size - 1)) p.tail else p.brows)
                }
            }
            if (f.lid == 'x') {                                             // closed: an arc of lashes
                hline(ex - 2, y + 2, 5, LID); px(ex - 3, y + 1, LID); px(ex + 3, y + 1, LID)
                px(ex + out * 4, y, LID)
                hline(ex - 2, y + 4, 5, p.skin)
                continue
            }
            val top = lidRow + 1
            for (yy in top..y + 3) for (x in ex - 3..ex + 3) {
                if (yy == y + 3 && kotlin.math.abs(x - ex) == 3) continue    // rounded lower corners
                val ix = x - (ex + f.dx)
                val iy = yy - (y + f.dy)
                var col = if (yy == top) SHADOW else WHITE
                if (kotlin.math.abs(ix) <= 1 && iy in 0..3) {
                    col = if (iy <= 1) iris[0] else if (iy == 2) iris[1] else iris[2]
                    if (ix == 0 && (if (f.small) iy == 1 else iy == 1 || iy == 2)) col = DARK     // pupil
                    if (ix == -1 && yy == max(top, y + f.dy)) col = GLINT                     // glint, top-left
                }
                px(x, yy, col)
            }
            hline(ex - 4, lidRow, 9, LID); px(ex + out * 4, lidRow + 1, LID)  // the lid, its outer corner
            if (!p.glasses) px(ex + out * 5, lidRow - 1, LID)              // the lash (it would land on the frame)
            hline(ex - 2, y + 4, 5, p.skin)                                 // the lower lid
        }
        if (p.glasses) {
            for (ex in listOf(CX - 11, CX + 10)) {
                hline(ex - 5, y - 2, 11, FRAME); hline(ex - 5, y + 5, 11, FRAME)
                vline(ex - 5, y - 1, 6, FRAME); vline(ex + 5, y - 1, 6, FRAME)
                px(ex - 4, y - 1, GLINT)
            }
            hline(CX - 5, y, 9, FRAME)                              // bridge
            hline(CX - 19, y - 1, 3, FRAME); hline(CX + 16, y - 1, 3, FRAME)   // temples
        }
    }

    /**
     * The portrait with its eyes moving: [base] without eyes, one of the emotions, redrawn 12 times a second.
     * It runs while it is visible on screen and stops by itself when it is not (or has no view).
     */
    class Animated(private val base: Bitmap, private val p: Params, private val steps: List<Step>) : Drawable(), Animatable {
        private val work = base.copy(Bitmap.Config.ARGB_8888, true)
        private val paint = Paint().apply { isFilterBitmap = false }
        private val src = Rect(0, 0, base.width, base.height)
        private var started = 0L
        private var running = false
        private var shown = -1
        private val tick = Runnable { if (running) { invalidateSelf(); schedule() } }

        private fun index() = (((SystemClock.uptimeMillis() - started) / STEP_MS) % steps.size).toInt()

        private fun schedule() { scheduleSelf(tick, SystemClock.uptimeMillis() + STEP_MS) }

        override fun draw(canvas: Canvas) {
            val i = if (running) index() else 0
            if (i != shown) {
                Canvas(work).drawBitmap(base, 0f, 0f, null)
                Occhi.draw(work, p, steps[i])
                shown = i
            }
            canvas.drawBitmap(work, src, bounds, paint)
        }

        override fun start() {
            if (running) return
            running = true; started = SystemClock.uptimeMillis(); schedule()
        }

        override fun stop() { running = false; unscheduleSelf(tick) }
        override fun isRunning() = running

        override fun setVisible(visible: Boolean, restart: Boolean): Boolean {
            val changed = super.setVisible(visible, restart)
            if (visible) start() else stop()
            return changed
        }

        override fun getIntrinsicWidth() = base.width
        override fun getIntrinsicHeight() = base.height
        override fun setAlpha(alpha: Int) { paint.alpha = alpha }
        override fun setColorFilter(filter: ColorFilter?) { paint.colorFilter = filter }
        @Deprecated("Deprecated in Java")
        override fun getOpacity() = PixelFormat.TRANSLUCENT
    }
}
