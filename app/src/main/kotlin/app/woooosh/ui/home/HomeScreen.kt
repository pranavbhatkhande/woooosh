package app.woooosh.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Snackbar
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import app.woooosh.data.Task
import app.woooosh.ui.HomeUiState
import app.woooosh.ui.TaskFilter
import app.woooosh.ui.TodoViewModel
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable
fun HomeScreen(viewModel: TodoViewModel) {
    val state by viewModel.uiState.collectAsState()
    val lastDeleted by viewModel.lastDeleted.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    var editing by remember { mutableStateOf<Task?>(null) }

    LaunchedEffect(lastDeleted) {
        val deleted = lastDeleted ?: return@LaunchedEffect
        val result = snackbarHostState.showSnackbar(
            message = "“${deleted.title.take(24)}” deleted",
            actionLabel = "Undo",
            withDismissAction = true,
        )
        if (result == SnackbarResult.ActionPerformed) viewModel.undoDelete()
        else viewModel.dismissUndo()
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) { data -> Snackbar(data) } },
        bottomBar = {
            QuickAddBar(
                onAdd = viewModel::add,
                modifier = Modifier
                    .padding(horizontal = 16.dp, vertical = 12.dp)
                    .navigationBarsPadding()
                    .imePadding(),
            )
        },
    ) { padding ->
        Column(modifier = Modifier.padding(padding)) {
            Header(state)
            FilterRow(
                current = state.filter,
                counts = state.counts,
                onSelect = viewModel::setFilter,
            )
            if (state.isEmpty) {
                EmptyState(state.filter)
            } else {
                TaskList(
                    state = state,
                    onToggleDone = viewModel::toggleDone,
                    onAdvance = viewModel::advance,
                    onDelete = viewModel::delete,
                    onEdit = { editing = it },
                    onClearDone = viewModel::clearDone,
                )
            }
        }
    }

    editing?.let { task ->
        TaskEditSheet(
            task = task,
            onRename = { viewModel.rename(task, it) },
            onSetStatus = { viewModel.setStatus(task, it); editing = null },
            onDelete = { viewModel.delete(task) },
            onDismiss = { editing = null },
        )
    }
}

@Composable
private fun Header(state: HomeUiState) {
    val today = remember { LocalDate.now() }
    val dayName = remember(today) {
        today.format(DateTimeFormatter.ofPattern("EEEE", Locale.getDefault()))
    }
    val dateLine = remember(today) {
        today.format(DateTimeFormatter.ofPattern("MMMM d", Locale.getDefault()))
    }
    val total = state.openCount + state.doneToday
    val progress = if (total > 0) state.doneToday.toFloat() / total else 0f

    Column(modifier = Modifier.padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(8.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "woooosh",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
            )
            Box(contentAlignment = Alignment.Center) {
                CircularProgressIndicator(
                    progress = { progress },
                    modifier = Modifier.size(34.dp),
                    strokeWidth = 3.dp,
                    trackColor = MaterialTheme.colorScheme.surfaceVariant,
                )
                Text(
                    text = "${state.doneToday}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Spacer(Modifier.height(12.dp))
        Text(text = dayName, style = MaterialTheme.typography.headlineLarge)
        Text(
            text = "$dateLine  ·  ${state.openCount} open, ${state.doneToday} done",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(16.dp))
    }
}

@Composable
private fun FilterRow(
    current: TaskFilter,
    counts: Map<TaskFilter, Int>,
    onSelect: (TaskFilter) -> Unit,
) {
    val labels = mapOf(
        TaskFilter.ALL to "All",
        TaskFilter.IDEA to "Ideas",
        TaskFilter.ACTION to "Next",
        TaskFilter.FOCUS to "Focus",
        TaskFilter.DONE to "Done",
    )
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState())
            .padding(horizontal = 20.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        TaskFilter.entries.forEach { filter ->
            val count = counts[filter] ?: 0
            FilterChip(
                selected = current == filter,
                onClick = { onSelect(filter) },
                label = {
                    Text(if (count > 0) "${labels[filter]} $count" else labels[filter].orEmpty())
                },
            )
        }
    }
}

@Composable
private fun TaskList(
    state: HomeUiState,
    onToggleDone: (Task) -> Unit,
    onAdvance: (Task) -> Unit,
    onDelete: (Task) -> Unit,
    onEdit: (Task) -> Unit,
    onClearDone: () -> Unit,
) {
    val sections = listOf(
        "In focus" to state.focus,
        "Up next" to state.next,
        "Ideas" to state.ideas,
    ).filter { it.second.isNotEmpty() }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(top = 8.dp, bottom = 96.dp),
    ) {
        sections.forEach { (title, tasks) ->
            item(key = "header-$title") { SectionHeader(title, tasks.size) }
            items(tasks, key = { it.id }) { task ->
                TaskRow(
                    task = task,
                    onToggleDone = { onToggleDone(task) },
                    onAdvance = { onAdvance(task) },
                    onDelete = { onDelete(task) },
                    onClick = { onEdit(task) },
                    modifier = Modifier.animateItem(),
                )
            }
        }
        if (state.done.isNotEmpty()) {
            item(key = "header-done") {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 20.dp, end = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    SectionHeader("Done", state.done.size, inline = true)
                    TextButton(onClick = onClearDone) { Text("Clear") }
                }
            }
            items(state.done, key = { it.id }) { task ->
                TaskRow(
                    task = task,
                    onToggleDone = { onToggleDone(task) },
                    onAdvance = { onAdvance(task) },
                    onDelete = { onDelete(task) },
                    onClick = { onEdit(task) },
                    modifier = Modifier.animateItem(),
                )
            }
        }
    }
}

@Composable
private fun SectionHeader(title: String, count: Int, inline: Boolean = false) {
    Row(
        modifier = if (inline) Modifier else Modifier.padding(
            start = 20.dp, end = 20.dp, top = 20.dp, bottom = 6.dp,
        ),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            text = title.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Surface(
            shape = CircleShape,
            color = MaterialTheme.colorScheme.surfaceVariant,
        ) {
            Text(
                text = "$count",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 7.dp, vertical = 1.dp),
            )
        }
    }
}

@Composable
private fun EmptyState(filter: TaskFilter) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.padding(bottom = 96.dp),
        ) {
            Surface(
                shape = CircleShape,
                color = MaterialTheme.colorScheme.primaryContainer,
            ) {
                Icon(
                    Icons.Rounded.AutoAwesome,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onPrimaryContainer,
                    modifier = Modifier
                        .padding(20.dp)
                        .size(32.dp),
                )
            }
            Text(
                text = if (filter == TaskFilter.ALL) "All clear" else "Nothing here",
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = "Capture an idea below to get started.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
