package com.mannaggia.app

import android.content.Context
import android.util.AttributeSet
import android.widget.FrameLayout

/** A FrameLayout as tall as it is wide: the album portraits are square. */
class SquareFrameLayout(context: Context, attrs: AttributeSet?) : FrameLayout(context, attrs) {
    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        super.onMeasure(widthMeasureSpec, widthMeasureSpec)
    }
}
