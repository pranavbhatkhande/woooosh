package app.woooosh.data

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * The woooosh flow: capture an [IDEA], commit to it as an [ACTION],
 * pull it into [FOCUS] when you start, and land it in [DONE].
 */
enum class TaskStatus {
    IDEA, ACTION, FOCUS, DONE;

    val isDone: Boolean get() = this == DONE

    /** The next stage in the flow, or null when already done. */
    fun advanced(): TaskStatus? = when (this) {
        IDEA -> ACTION
        ACTION -> FOCUS
        FOCUS -> DONE
        DONE -> null
    }
}

@Entity(tableName = "tasks")
data class Task(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val title: String,
    val status: TaskStatus = TaskStatus.IDEA,
    val createdAt: Long = System.currentTimeMillis(),
    val completedAt: Long? = null,
)
