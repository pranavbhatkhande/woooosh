package app.woooosh.ui.home

import android.text.format.DateUtils
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.DeleteOutline
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import app.woooosh.data.Task
import app.woooosh.data.TaskStatus

/**
 * A single task row.
 *
 * Gestures: tap the status ring to complete (spring + haptic), swipe
 * right to advance one stage, swipe left to delete (undoable), tap the
 * row to edit.
 */
@Composable
fun TaskRow(
    task: Task,
    onToggleDone: () -> Unit,
    onAdvance: () -> Unit,
    onDelete: () -> Unit,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val haptics = LocalHapticFeedback.current
    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = { value ->
            when (value) {
                SwipeToDismissBoxValue.StartToEnd -> {
                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                    onAdvance()
                    false // snap back; the row morphs in place
                }
                SwipeToDismissBoxValue.EndToStart -> {
                    haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                    onDelete()
                    true
                }
                SwipeToDismissBoxValue.Settled -> false
            }
        },
        positionalThreshold = { totalDistance -> totalDistance * 0.4f },
    )

    SwipeToDismissBox(
        state = dismissState,
        modifier = modifier,
        enableDismissFromStartToEnd = !task.status.isDone,
        backgroundContent = { SwipeBackground(dismissState.dismissDirection, task.status) },
    ) {
        Surface(color = MaterialTheme.colorScheme.surface) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(onClick = onClick)
                    .padding(horizontal = 20.dp, vertical = 14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                StatusRing(
                    status = task.status,
                    onClick = {
                        haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                        onToggleDone()
                    },
                )
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = task.title,
                        style = MaterialTheme.typography.bodyLarge,
                        color = if (task.status.isDone) MaterialTheme.colorScheme.onSurfaceVariant
                        else MaterialTheme.colorScheme.onSurface,
                        textDecoration = if (task.status.isDone) TextDecoration.LineThrough else null,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                Text(
                    text = DateUtils.getRelativeTimeSpanString(
                        task.completedAt ?: task.createdAt,
                        System.currentTimeMillis(),
                        DateUtils.MINUTE_IN_MILLIS,
                        DateUtils.FORMAT_ABBREV_RELATIVE,
                    ).toString(),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline,
                )
            }
        }
    }
}

/** Tap-to-complete ring: outlined in the status accent, fills with a check when done. */
@Composable
private fun StatusRing(status: TaskStatus, onClick: () -> Unit) {
    val done = status.isDone
    val fill by animateColorAsState(
        targetValue = if (done) status.accent() else Color.Transparent,
        label = "ringFill",
    )
    val scale by animateFloatAsState(
        targetValue = if (done) 1f else 0f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
        label = "checkScale",
    )
    Box(
        modifier = Modifier
            .size(26.dp)
            .clickable(onClick = onClick)
            .border(width = 2.dp, color = status.accent(), shape = CircleShape)
            .background(color = fill, shape = CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = Icons.Rounded.Check,
            contentDescription = if (done) "Mark not done" else "Mark done",
            tint = MaterialTheme.colorScheme.surface,
            modifier = Modifier
                .size(16.dp)
                .scale(scale),
        )
    }
}

@Composable
private fun SwipeBackground(direction: SwipeToDismissBoxValue, status: TaskStatus) {
    val advancing = direction == SwipeToDismissBoxValue.StartToEnd
    val next = status.advanced()
    val container = when {
        advancing && next != null -> next.accentContainer()
        direction == SwipeToDismissBoxValue.EndToStart -> MaterialTheme.colorScheme.errorContainer
        else -> Color.Transparent
    }
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(container)
            .padding(horizontal = 24.dp),
        contentAlignment = if (advancing) Alignment.CenterStart else Alignment.CenterEnd,
    ) {
        when {
            advancing && next != null -> Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Icon(next.icon, contentDescription = null, tint = next.accent())
                Text(
                    text = next.label,
                    style = MaterialTheme.typography.labelLarge,
                    color = next.accent(),
                )
            }
            direction == SwipeToDismissBoxValue.EndToStart -> Icon(
                Icons.Rounded.DeleteOutline,
                contentDescription = "Delete",
                tint = MaterialTheme.colorScheme.onErrorContainer,
            )
        }
    }
}
