package app.woooosh

import android.app.Application
import app.woooosh.data.TaskRepository
import app.woooosh.data.WoooshDatabase

class WoooshApplication : Application() {
    val repository: TaskRepository by lazy {
        TaskRepository(WoooshDatabase.get(this).taskDao())
    }
}
