package app.woooosh.ui.home

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Bolt
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.Lightbulb
import androidx.compose.material.icons.rounded.RocketLaunch
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import app.woooosh.data.TaskStatus

/**
 * Visual identity of each stage. Colors are M3 roles, so they stay
 * harmonious under dynamic color (Material You) and in dark theme.
 */
val TaskStatus.label: String
    get() = when (this) {
        TaskStatus.IDEA -> "Idea"
        TaskStatus.ACTION -> "Next"
        TaskStatus.FOCUS -> "Focus"
        TaskStatus.DONE -> "Done"
    }

val TaskStatus.icon: ImageVector
    get() = when (this) {
        TaskStatus.IDEA -> Icons.Rounded.Lightbulb
        TaskStatus.ACTION -> Icons.Rounded.Bolt
        TaskStatus.FOCUS -> Icons.Rounded.RocketLaunch
        TaskStatus.DONE -> Icons.Rounded.Check
    }

@Composable
fun TaskStatus.accent(): Color = when (this) {
    TaskStatus.IDEA -> MaterialTheme.colorScheme.tertiary
    TaskStatus.ACTION -> MaterialTheme.colorScheme.secondary
    TaskStatus.FOCUS -> MaterialTheme.colorScheme.primary
    TaskStatus.DONE -> MaterialTheme.colorScheme.outline
}

@Composable
fun TaskStatus.accentContainer(): Color = when (this) {
    TaskStatus.IDEA -> MaterialTheme.colorScheme.tertiaryContainer
    TaskStatus.ACTION -> MaterialTheme.colorScheme.secondaryContainer
    TaskStatus.FOCUS -> MaterialTheme.colorScheme.primaryContainer
    TaskStatus.DONE -> MaterialTheme.colorScheme.surfaceVariant
}
