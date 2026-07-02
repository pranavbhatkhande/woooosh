package app.woooosh.data

import kotlinx.coroutines.flow.Flow

class TaskRepository(private val dao: TaskDao) {

    val tasks: Flow<List<Task>> = dao.observeAll()

    suspend fun add(title: String): Long =
        dao.insert(Task(title = title.trim()))

    suspend fun update(task: Task) = dao.update(task)

    suspend fun setStatus(task: Task, status: TaskStatus) =
        dao.update(
            task.copy(
                status = status,
                completedAt = if (status.isDone) System.currentTimeMillis() else null,
            )
        )

    suspend fun delete(task: Task) = dao.delete(task)

    /** Re-insert a deleted task, keeping its original id (undo). */
    suspend fun restore(task: Task) = dao.insert(task)

    suspend fun clearDone() = dao.clearDone()
}
