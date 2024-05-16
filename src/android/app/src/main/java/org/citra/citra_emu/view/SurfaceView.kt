package org.citra.citra_emu.view

import android.content.Context
import android.util.AttributeSet
import android.util.Rational
import android.view.SurfaceView

class SurfaceView @JvmOverloads constructor(
    context: Context, 
    attrs: AttributeSet? = null, 
    defStyleAttr: Int = 0
) : SurfaceView(context, attrs, defStyleAttr) {

    private var aspectRatio: Float = 0f // Default is no specific aspect ratio
    /**
     * Set the aspect ratio for this view using a nullable Rational.
     *
     * @param aspectRatio The aspect ratio to set (width / height), or null to stretch to fit.
     */
    fun setAspectRatio(ratio: Rational?) {
        aspectRatio = ratio?.toFloat() ?: 0f
        requestLayout()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val displayWidth: Float = MeasureSpec.getSize(widthMeasureSpec).toFloat()
        val displayHeight: Float = MeasureSpec.getSize(heightMeasureSpec).toFloat()
        if (aspectRatio != 0f) {
            val displayAspect = displayWidth / displayHeight
                // Max out height
                val halfWidth = displayWidth / 2
                val surfaceWidth = displayHeight * aspectRatio
                val newLeft: Float = halfWidth - (surfaceWidth / 2)
                val newRight: Float = halfWidth + (surfaceWidth / 2)
                super.onMeasure(
                    MeasureSpec.makeMeasureSpec(
                        newRight.toInt() - newLeft.toInt(),
                        MeasureSpec.EXACTLY
                    ),
                    heightMeasureSpec
                )
                return
        }
        super.onMeasure(widthMeasureSpec, heightMeasureSpec)
    }
}
