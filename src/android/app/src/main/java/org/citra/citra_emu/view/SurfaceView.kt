package org.citra.citra_emu.view

import android.content.Context
import android.util.AttributeSet
import android.view.SurfaceView

class SurfaceView @JvmOverloads constructor(
    context: Context, 
    attrs: AttributeSet? = null, 
    defStyleAttr: Int = 0
) : SurfaceView(context, attrs, defStyleAttr) {

    private var aspectRatio: Float = 1.0f // Default aspect ratio (1:1)

    /**
     * Set the aspect ratio for this view.
     *
     * @param aspectRatio The aspect ratio to set (width / height).
     */
    fun setAspectRatio(aspectRatio: Float) {
        require(aspectRatio > 0) { "Aspect ratio must be positive" }
        this.aspectRatio = aspectRatio
        requestLayout()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val width = MeasureSpec.getSize(widthMeasureSpec)
        var height = MeasureSpec.getSize(heightMeasureSpec)

        if (aspectRatio != 0f) {
            // Calculate the desired height based on the width and the aspect ratio
            val desiredHeight = (width / aspectRatio).toInt()

            if (desiredHeight > height) {
                // If the desired height is greater than the available height, adjust the width
                height = (height * aspectRatio).toInt()
            } else {
                // Otherwise, use the desired height
                height = desiredHeight
            }
        }

        // Call setMeasuredDimension to set the measured width and height
        setMeasuredDimension(width, height)
    }
}
