package com.mannaggia.app

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.RectF
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.RelativeSizeSpan
import android.util.AttributeSet
import android.util.TypedValue
import android.view.ViewGroup
import android.widget.TextView
import kotlin.math.roundToInt

/**
 * The card on parchment (home and album detail): the 112 x 170 px pixel-art parchment
 * (res/drawable-nodpi/pergamena.png, from tools/ritratti96/pergamena96.px.js) scaled up without smoothing,
 * as wide as the view, and its children placed in parchment pixels: `app:pxRect="x,y,w,h"`, with
 * `app:pxText` the text size in parchment pixels. Always light, also in the dark theme.
 */
class Pergamena(context: Context, attrs: AttributeSet?) : ViewGroup(context, attrs) {

    private val parchment = BitmapFactory.decodeResource(resources, R.drawable.pergamena, BitmapFactory.Options().apply { inScaled = false })
    private val paint = Paint().apply { isFilterBitmap = false }
    private val dst = Rect()

    init { setWillNotDraw(false) }

    class LayoutParams : ViewGroup.LayoutParams {
        var rect = RectF()
        var text = 0f

        constructor(context: Context, attrs: AttributeSet?) : super(context, attrs) {
            val a = context.obtainStyledAttributes(attrs, R.styleable.Pergamena_Layout)
            a.getString(R.styleable.Pergamena_Layout_pxRect)?.split(',')?.map { it.trim().toFloat() }?.let { (x, y, w, h) ->
                rect = RectF(x, y, x + w, y + h)
            }
            text = a.getFloat(R.styleable.Pergamena_Layout_pxText, 0f)
            a.recycle()
        }

        constructor(width: Int, height: Int) : super(width, height)
    }

    override fun generateLayoutParams(attrs: AttributeSet?) = LayoutParams(context, attrs)
    override fun generateDefaultLayoutParams() = LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT)
    override fun generateLayoutParams(p: ViewGroup.LayoutParams?) = LayoutParams(p?.width ?: ViewGroup.LayoutParams.WRAP_CONTENT, p?.height ?: ViewGroup.LayoutParams.WRAP_CONTENT)
    override fun checkLayoutParams(p: ViewGroup.LayoutParams?) = p is LayoutParams

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val w = MeasureSpec.getSize(widthMeasureSpec)
        val s = w / W.toFloat()
        for (i in 0 until childCount) {
            val child = getChildAt(i)
            val lp = child.layoutParams as LayoutParams
            if (lp.text > 0f && child is TextView && child.textSize != lp.text * s) child.setTextSize(TypedValue.COMPLEX_UNIT_PX, lp.text * s)
            child.measure(MeasureSpec.makeMeasureSpec((lp.rect.width() * s).roundToInt(), MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec((lp.rect.height() * s).roundToInt(), MeasureSpec.EXACTLY))
        }
        setMeasuredDimension(w, (w * H / W.toFloat()).roundToInt())
    }

    override fun onLayout(changed: Boolean, l: Int, t: Int, r: Int, b: Int) {
        val s = width / W.toFloat()
        for (i in 0 until childCount) {
            val child = getChildAt(i)
            val rc = (child.layoutParams as LayoutParams).rect
            val x = (rc.left * s).roundToInt()
            val y = (rc.top * s).roundToInt()
            child.layout(x, y, x + child.measuredWidth, y + child.measuredHeight)
        }
    }

    override fun onDraw(canvas: Canvas) {
        dst.set(0, 0, width, height)
        canvas.drawBitmap(parchment, null, dst, paint)
    }

    companion object {
        const val W = 112
        const val H = 170
        private val RED = Color.parseColor("#9a2b25")

        /** The label on top: its initial in red and a little larger, as a rubricated letter. */
        fun etichetta(text: String): CharSequence = SpannableString(text).apply {
            if (text.isNotEmpty()) {
                setSpan(ForegroundColorSpan(RED), 0, 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                setSpan(RelativeSizeSpan(1.35f), 0, 1, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
            }
        }
    }
}
