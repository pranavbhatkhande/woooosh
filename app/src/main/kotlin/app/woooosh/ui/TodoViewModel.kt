package app.woooosh.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import app.woooosh.WoooshApplication
import app.woooosh.data.Task
import app.woooosh.data.TaskRepository
import app.woooosh.data.TaskStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/** Which slice of the flow the user is looking at. */
enum class TaskFilter { ALL, IDEA, ACTION, FOCUS, DONE }

data class HomeUiState(
    val filter: TaskFilter = TaskFilter.ALL,
    val focus: List<Task> = emptyList(),
    val next: List<Task> = emptyList(),
    val ideas: List<Task> = emptyList(),
    val done: List<Task> = emptyList(),
    val counts: Map<TaskFilter, Int> = emptyMap(),
) {
    val isEmpty: Boolean get() = focus.isEmpty() && next.isEmpty() && ideas.isEmpty() && done.isEmpty()
    val doneToday: Int get() = done.size
    val openCount: Int get() = focus.size + next.size + ideas.size
}

class TodoViewModel(private val repository: TaskRepository) : ViewModel() {

    private val filter = MutableStateFlow(TaskFilter.ALL)

    /** The most recently deleted task, held for snackbar undo. */
    private val _lastDeleted = MutableStateFlow<Task?>(null)
    val lastDeleted: StateFlow<Task?> = _lastDeleted.asStateFlow()

    val uiState: StateFlow<HomeUiState> =
        combine(repository.tasks, filter) { tasks, f ->
            val visible = when (f) {
                TaskFilter.ALL -> tasks
                TaskFilter.IDEA -> tasks.filter { it.status == TaskStatus.IDEA }
                TaskFilter.ACTION -> tasks.filter { it.status == TaskStatus.ACTION }
                TaskFilter.FOCUS -> tasks.filter { it.status == TaskStatus.FOCUS }
                TaskFilter.DONE -> tasks.filter { it.status == TaskStatus.DONE }
            }
            HomeUiState(
                filter = f,
                focus = visible.filter { it.status == TaskStatus.FOCUS },
                next = visible.filter { it.status == TaskStatus.ACTION },
                ideas = visible.filter { it.status == TaskStatus.IDEA },
                done = visible.filter { it.status == TaskStatus.DONE }
                    .sortedByDescending { it.completedAt ?: 0 },
                counts = mapOf(
                    TaskFilter.ALL to tasks.size,
                    TaskFilter.IDEA to tasks.count { it.status == TaskStatus.IDEA },
                    TaskFilter.ACTION to tasks.count { it.status == TaskStatus.ACTION },
                    TaskFilter.FOCUS to tasks.count { it.status == TaskStatus.FOCUS },
                    TaskFilter.DONE to tasks.count { it.status == TaskStatus.DONE },
                ),
            )
        }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), HomeUiState())

    fun setFilter(f: TaskFilter) {
        filter.value = f
    }

    fun add(title: String) {
        if (title.isBlank()) return
        viewModelScope.launch { repository.add(title) }
    }

    fun rename(task: Task, title: String) {
        if (title.isBlank()) return
        viewModelScope.launch { repository.update(task.copy(title = title.trim())) }
    }

    fun setStatus(task: Task, status: TaskStatus) {
        viewModelScope.launch { repository.setStatus(task, status) }
    }

    /** Move the task one stage forward in the flow (idea → action → focus → done). */
    fun advance(task: Task) {
        task.status.advanced()?.let { setStatus(task, it) }
    }

    /** Toggle between done and back to action. */
    fun toggleDone(task: Task) {
        setStatus(task, if (task.status.isDone) TaskStatus.ACTION else TaskStatus.DONE)
    }

    fun delete(task: Task) {
        viewModelScope.launch {
            repository.delete(task)
            _lastDeleted.value = task
        }
    }

    fun undoDelete() {
        val task = _lastDeleted.value ?: return
        _lastDeleted.value = null
        viewModelScope.launch { repository.restore(task) }
    }

    fun dismissUndo() {
        _lastDeleted.value = null
    }

    fun clearDone() {
        viewModelScope.launch { repository.clearDone() }
    }

    companion object {
        val Factory: ViewModelProvider.Factory = viewModelFactory {
            initializer {
                val app = this[ViewModelProvider.AndroidViewModelFactory.APPLICATION_KEY] as WoooshApplication
                TodoViewModel(app.repository)
            }
        }
    }
}
