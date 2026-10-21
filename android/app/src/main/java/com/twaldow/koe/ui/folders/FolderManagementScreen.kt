package com.twaldow.koe.ui.folders

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.twaldow.koe.data.repository.FolderRepository
import com.twaldow.koe.domain.model.Folder
import com.twaldow.koe.ui.common.FOLDER_COLOR_PALETTE
import com.twaldow.koe.viewmodel.MainViewModel
import kotlinx.coroutines.launch

private fun parseColor(hex: String): Color = Color(android.graphics.Color.parseColor(hex))

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FolderManagementScreen(
    navController: NavHostController,
    mainViewModel: MainViewModel,
    folderRepository: FolderRepository = FolderRepository(),
) {
    val uiState by mainViewModel.uiState.collectAsState()
    val scope = rememberCoroutineScope()
    var editingFolder by remember { mutableStateOf<Folder?>(null) }
    var showCreateDialog by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    fun refresh() = mainViewModel.refresh()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Ordner") },
                navigationIcon = {
                    TextButton(onClick = { navController.popBackStack() }) { Text("Zurück") }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showCreateDialog = true }) {
                Icon(Icons.Filled.Add, contentDescription = "Ordner anlegen")
            }
        },
    ) { padding ->
        Column(modifier = Modifier.padding(padding)) {
            error?.let {
                Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp))
            }
            LazyColumn {
                items(uiState.folders, key = { it.id }) { folder ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { editingFolder = folder }
                            .padding(horizontal = 16.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Box(
                            modifier = Modifier
                                .size(20.dp)
                                .background(parseColor(folder.color), CircleShape)
                        )
                        Text(folder.name, modifier = Modifier.weight(1f))
                        if (!folder.isSystem) {
                            IconButton(onClick = {
                                scope.launch {
                                    try {
                                        folderRepository.deleteFolder(folder.id)
                                        refresh()
                                    } catch (e: Exception) {
                                        error = e.message ?: e.toString()
                                    }
                                }
                            }) {
                                Icon(Icons.Filled.Delete, contentDescription = "Löschen")
                            }
                        }
                    }
                }
            }
        }
    }

    editingFolder?.let { folder ->
        FolderEditDialog(
            initialName = folder.name,
            initialColor = folder.color,
            title = "Ordner bearbeiten",
            onDismiss = { editingFolder = null },
            onSave = { name, color ->
                scope.launch {
                    try {
                        folderRepository.updateFolder(folder.id, name = name, color = color)
                        editingFolder = null
                        refresh()
                    } catch (e: Exception) {
                        error = e.message ?: e.toString()
                    }
                }
            },
        )
    }

    if (showCreateDialog) {
        FolderEditDialog(
            initialName = "",
            initialColor = FOLDER_COLOR_PALETTE.first(),
            title = "Neuer Ordner",
            onDismiss = { showCreateDialog = false },
            onSave = { name, color ->
                scope.launch {
                    try {
                        folderRepository.createFolder(name, color)
                        showCreateDialog = false
                        refresh()
                    } catch (e: Exception) {
                        error = e.message ?: e.toString()
                    }
                }
            },
        )
    }
}

@Composable
private fun FolderEditDialog(
    initialName: String,
    initialColor: String,
    title: String,
    onDismiss: () -> Unit,
    onSave: (name: String, color: String) -> Unit,
) {
    var name by remember { mutableStateOf(initialName) }
    var color by remember { mutableStateOf(initialColor) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Name") })
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FOLDER_COLOR_PALETTE.forEach { hex ->
                        Box(
                            modifier = Modifier
                                .size(32.dp)
                                .background(parseColor(hex), CircleShape)
                                .clickable { color = hex }
                                .then(
                                    if (color == hex) {
                                        Modifier.background(Color.Black.copy(alpha = 0.15f), CircleShape)
                                    } else Modifier
                                )
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = { if (name.isNotBlank()) onSave(name, color) }) { Text("Speichern") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Abbrechen") }
        },
    )
}
