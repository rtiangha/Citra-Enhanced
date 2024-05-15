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

    private var aspectRatio: Rational? = null // Default is no specific aspect ratio
    /**
     * Set the aspect ratio for this view using a nullable Rational.
     *
     * @param aspectRatio The aspect ratio to set (width / height), or null to stretch to fit.
     */
    fun setAspectRatio(aspectRatio: Rational?) {
        if (aspectRatio != null && !aspectRatio.isPositive) {
            throw IllegalArgumentException("Aspect ratio must be positive")
        }
        this.aspectRatio = aspectRatio
        requestLayout()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val originalWidth = MeasureSpec.getSize(widthMeasureSpec)
        val originalHeight = MeasureSpec.getSize(heightMeasureSpec)

        var calculatedWidth = originalWidth
        var calculatedHeight = originalHeight

        aspectRatio?.let { ratio ->
            // Calculate the desired height based on the width and the aspect ratio
            val desiredHeight = (originalWidth / ratio.toFloat()).toInt()

            if (desiredHeight > originalHeight) {
                // If the desired height is greater than the available height, adjust the width
                calculatedWidth = (originalHeight * ratio.toFloat()).toInt()
            } else {
                // Otherwise, use the desired height
                calculatedHeight = desiredHeight
            }
        }

        // Call setMeasuredDimension to set the measured width and height
        setMeasuredDimension(calculatedWidth, calculatedHeight)
    }
}
