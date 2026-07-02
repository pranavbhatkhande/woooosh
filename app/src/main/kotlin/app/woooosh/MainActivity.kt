package app.woooosh

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import app.woooosh.ui.TodoViewModel
import app.woooosh.ui.home.HomeScreen
import app.woooosh.ui.theme.WoooshTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            WoooshTheme {
                WoooshApp()
            }
        }
    }
}

@Composable
private fun WoooshApp(viewModel: TodoViewModel = viewModel(factory = TodoViewModel.Factory)) {
    HomeScreen(viewModel)
}
