package com.twaldow.koe

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.twaldow.koe.ui.edit.EditTodoScreen
import com.twaldow.koe.ui.folders.FolderManagementScreen
import com.twaldow.koe.ui.main.MainScreen
import com.twaldow.koe.ui.theme.KoeTheme
import com.twaldow.koe.viewmodel.MainViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            KoeTheme {
                // Eine MainViewModel-Instanz fuer die ganze Activity, damit Edit-/Ordner-Screen
                // denselben Zustand sehen und per refresh() aktualisieren koennen.
                val mainViewModel: MainViewModel = viewModel()
                val navController = rememberNavController()

                NavHost(navController = navController, startDestination = "main", modifier = Modifier.fillMaxSize()) {
                    composable("main") {
                        MainScreen(navController = navController, viewModel = mainViewModel)
                    }
                    composable("edit_todo") {
                        EditTodoScreen(navController = navController, mainViewModel = mainViewModel)
                    }
                    composable("folders") {
                        FolderManagementScreen(navController = navController, mainViewModel = mainViewModel)
                    }
                }
            }
        }
    }
}