package app.woooosh.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * M3 defaults with a tightened, more confident display/headline —
 * the header wordmark and day title carry the app's personality.
 */
val WoooshTypography = Typography().run {
    copy(
        headlineLarge = headlineLarge.copy(
            fontWeight = FontWeight.SemiBold,
            letterSpacing = (-0.5).sp,
        ),
        headlineMedium = headlineMedium.copy(
            fontWeight = FontWeight.SemiBold,
            letterSpacing = (-0.25).sp,
        ),
        titleMedium = titleMedium.copy(
            fontWeight = FontWeight.SemiBold,
        ),
        labelSmall = labelSmall.copy(
            letterSpacing = 0.8.sp,
        ),
    )
}
