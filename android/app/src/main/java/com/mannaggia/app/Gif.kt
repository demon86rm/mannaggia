package com.mannaggia.app

import java.io.OutputStream

/**
 * A minimal animated GIF89a encoder, enough for pixel art: one global palette of the 256 most
 * used colours (the rarer ones go to the nearest), LZW, opaque frames, endless loop.
 */
object Gif {

    /** [frames]: ARGB pixels (alpha ignored) of [width] x [height], all the same size. */
    fun write(out: OutputStream, width: Int, height: Int, frames: List<() -> IntArray>, delayMs: Int) {
        val counts = HashMap<Int, Int>()
        for (frame in frames) for (c in frame()) counts.merge(c and 0xFFFFFF, 1, Int::plus)
        val palette = counts.entries.sortedByDescending { it.value }.take(256).map { it.key }
        val index = HashMap<Int, Int>().apply { palette.forEachIndexed { i, c -> put(c, i) } }

        fun nearest(c: Int): Int = index.getOrPut(c) {
            palette.indices.minBy { i ->
                val p = palette[i]
                val dr = (p shr 16 and 0xFF) - (c shr 16 and 0xFF)
                val dg = (p shr 8 and 0xFF) - (c shr 8 and 0xFF)
                val db = (p and 0xFF) - (c and 0xFF)
                dr * dr + dg * dg + db * db
            }
        }

        out.write("GIF89a".toByteArray())
        short(out, width); short(out, height)
        out.write(0xF7); out.write(0); out.write(0)          // global table of 256 colours
        for (i in 0 until 256) {
            val c = palette.getOrElse(i) { 0 }
            out.write(c shr 16 and 0xFF); out.write(c shr 8 and 0xFF); out.write(c and 0xFF)
        }
        out.write(byteArrayOf(0x21, 0xFF.toByte(), 0x0B) + "NETSCAPE2.0".toByteArray() + byteArrayOf(3, 1, 0, 0, 0))
        for (frame in frames) {
            out.write(byteArrayOf(0x21, 0xF9.toByte(), 4, 0x04))   // graphic control: do not dispose
            short(out, delayMs / 10); out.write(0); out.write(0)
            out.write(0x2C); short(out, 0); short(out, 0); short(out, width); short(out, height); out.write(0)
            val pixels = frame()
            lzw(out, ByteArray(pixels.size) { nearest(pixels[it] and 0xFFFFFF).toByte() })
        }
        out.write(0x3B)
    }

    private fun short(out: OutputStream, v: Int) {
        out.write(v and 0xFF); out.write(v shr 8 and 0xFF)
    }

    /** LZW with 8-bit pixels, codes from 9 to 12 bits, a clear code when the table is full. */
    private fun lzw(out: OutputStream, indices: ByteArray) {
        val clear = 256
        val end = 257
        out.write(8)
        val blocks = SubBlocks(out)
        var bits = 0L
        var nBits = 0
        var codeSize = 9
        fun emit(code: Int) {
            bits = bits or (code.toLong() shl nBits)
            nBits += codeSize
            while (nBits >= 8) {
                blocks.write((bits and 0xFF).toInt()); bits = bits shr 8; nBits -= 8
            }
        }
        val table = HashMap<Int, Int>()
        var next = end + 1
        emit(clear)
        var prefix = indices[0].toInt() and 0xFF
        for (i in 1 until indices.size) {
            val k = indices[i].toInt() and 0xFF
            val key = (prefix shl 8) or k
            val code = table[key]
            if (code != null) {
                prefix = code
                continue
            }
            emit(prefix)
            if (next == 4096) {
                emit(clear)
                table.clear(); next = end + 1; codeSize = 9
            } else {
                if (next >= (1 shl codeSize)) codeSize++
                table[key] = next++
            }
            prefix = k
        }
        emit(prefix)
        emit(end)
        if (nBits > 0) blocks.write((bits and 0xFF).toInt())
        blocks.close()
    }

    /** GIF data sub-blocks: at most 255 bytes each, then a zero-length terminator. */
    private class SubBlocks(private val out: OutputStream) {
        private val buf = ByteArray(255)
        private var n = 0
        fun write(b: Int) {
            buf[n++] = b.toByte()
            if (n == 255) flush()
        }
        private fun flush() {
            if (n == 0) return
            out.write(n); out.write(buf, 0, n); n = 0
        }
        fun close() {
            flush(); out.write(0)
        }
    }
}
