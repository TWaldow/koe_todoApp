package com.twaldow.koe.ui.edit

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.twaldow.koe.data.repository.TodoRepository
import com.twaldow.koe.domain.model.Recurrence
import com.twaldow.koe.domain.model.Todo
import com.twaldow.koe.viewmodel.MainViewModel
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset

private val RECURRENCE_LABELS = mapOf(
    Recurrence.NONE to "Keine",
    Recurrence.DAILY to "Täglich",
    Recurrence.WEEKLY to "Wöchentlich",
    Recurrence.MONTHLY to "Monatlich",
)

/**
 * Dient Anlegen (initial == null) und Bearbeiten (initial != null). Es gibt keinen
 * GET /todos/{id}-Endpunkt im Backend, deshalb kommt `initial` als Snapshot aus
 * [MainViewModel.pendingEditTodo] statt per Re-Fetch über die ID.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditTodoScreen(
    navController: NavHostController,
    mainViewModel: MainViewModel,
    todoRepository: TodoRepository = TodoRepository(),
) {
    val initial = remember { mainViewModel.pendingEditTodo }
    val uiState by mainViewModel.uiState.collectAsState()
    val folders = uiState.folders
    val scope = rememberCoroutineScope()

    var text by remember { mutableStateOf(initial?.text ?: "") }
    var folderId by remember {
        mutableStateOf(initial?.folderId ?: uiState.currentFolder?.id ?: folders.firstOrNull()?.id ?: 0)
    }
    var important by remember { mutableStateOf(initial?.important ?: false) }
    var recurrence by remember { mutableStateOf(initial?.recurrence ?: Recurrence.NONE) }
    var hasDeadline by remember { mutableStateOf(initial?.dueDate != null) }
    var dueDate by remember { mutableStateOf(initial?.dueDate) }

    var isSaving by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showDeleteConfirm by remember { mutableStateOf(false) }
    var showDatePicker by remember { mutableStateOf(false) }

    fun save() {
        if (text.isBlank()) {
            error = "Text darf nicht leer sein"
            return
        }
        isSaving = true
        error = null
        scope.launch {
            try {
                val effectiveDueDate = if (recurrence == Recurrence.NONE && hasDeadline) dueDate else null
                val effectiveDueType = if (effectiveDueDate != null) com.twaldow.koe.domain.model.DueType.DEADLINE else null
                if (initial == null) {
                    todoRepository.createTodo(
                        text = text,
                        folderId = folderId,
                        important = important,
                        recurrence = recurrence,
                        dueType = effectiveDueType,
                        dueDate = effectiveDueDate,
                    )
                } else {
                    todoRepository.updateTodo(
                        id = initial.id,
                        text = text,
                        folderId = folderId,
                        important = important,
                        recurrence = recurrence,
                        dueType = effectiveDueType,
                        dueDate = effectiveDueDate,
                    )
                }
                mainViewModel.pendingEditTodo = null
                mainViewModel.refresh()
                navController.popBackStack()
            } catch (e: Exception) {
                error = e.message ?: e.toString()
            } finally {
                isSaving = false
            }
        }
    }

    fun delete() {
        val id = initial?.id ?: return
        isSaving = true
        scope.launch {
            try {
                todoRepository.deleteTodo(id)
                mainViewModel.pendingEditTodo = null
                mainViewModel.refresh()
                navController.popBackStack()
            } catch (e: Exception) {
                error = e.message ?: e.toString()
                isSaving = false
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (initial == null) "Todo anlegen" else "Todo bearbeiten") },
                navigationIcon = {
                    TextButton(onClick = { navController.popBackStack() }) { Text("Abbrechen") }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                label = { Text("Text") },
                modifier = Modifier.fillMaxWidth(),
            )

            var folderMenuExpanded by remember { mutableStateOf(false) }
            val selectedFolderName = folders.firstOrNull { it.id == folderId }?.name ?: ""
            Box(modifier = Modifier.fillMaxWidth()) {
                OutlinedTextField(
                    value = selectedFolderName,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Ordner") },
                    modifier = Modifier.fillMaxWidth(),
                )
                // Durchsichtige Flaeche ueber dem (read-only) Textfeld, da es selbst keine
                // Klicks durchlaesst - einfacher als ExposedDropdownMenuBox fuer diesen Fall.
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .clickable { folderMenuExpanded = true }
                )
                DropdownMenu(
                    expanded = folderMenuExpanded,
                    onDismissRequest = { folderMenuExpanded = false },
                ) {
                    folders.forEach { folder ->
                        DropdownMenuItem(
                            text = { Text(folder.name) },
                            onClick = {
                                folderId = folder.id
                                folderMenuExpanded = false
                            },
                        )
                    }
                }
            }

            Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Text("Wichtig", modifier = Modifier.weight(1f))
                Switch(checked = important, onCheckedChange = { important = it })
            }

            Text("Wiederholung", style = MaterialTheme.typography.labelLarge)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                RECURRENCE_LABELS.forEach { (value, label) ->
                    FilterChip(
                        selected = recurrence == value,
                        onClick = {
                            recurrence = value
                            if (value != Recurrence.NONE) hasDeadline = false
                        },
                        label = { Text(label) },
                    )
                }
            }

            if (recurrence == Recurrence.NONE) {
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Text("Deadline", modifier = Modifier.weight(1f))
                    Switch(checked = hasDeadline, onCheckedChange = { hasDeadline = it })
                }
                if (hasDeadline) {
                    OutlinedButton(onClick = { showDatePicker = true }) {
                        Text(dueDate?.toString() ?: "Datum wählen")
                    }
                }
            }

            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }

            Button(onClick = { save() }, enabled = !isSaving, modifier = Modifier.fillMaxWidth()) {
                Text("Speichern")
            }

            if (initial != null) {
                TextButton(
                    onClick = { showDeleteConfirm = true },
                    enabled = !isSaving,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Löschen", color = MaterialTheme.colorScheme.error)
                }
            }
        }
    }

    if (showDatePicker) {
        val initialMillis = (dueDate ?: LocalDate.now()).atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli()
        val datePickerState = rememberDatePickerState(initialSelectedDateMillis = initialMillis)
        DatePickerDialog(
            onDismissRequest = { showDatePicker = false },
            confirmButton = {
                TextButton(onClick = {
                    datePickerState.selectedDateMillis?.let { millis ->
                        dueDate = Instant.ofEpochMilli(millis).atZone(ZoneOffset.UTC).toLocalDate()
                    }
                    showDatePicker = false
                }) { Text("OK") }
            },
            dismissButton = {
                TextButton(onClick = { showDatePicker = false }) { Text("Abbrechen") }
            },
        ) {
            DatePicker(state = datePickerState)
        }
    }

    if (showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text("Todo löschen?") },
            text = { Text("\"$text\" wird gelöscht. Das lässt sich nicht rückgängig machen.") },
            confirmButton = {
                TextButton(onClick = {
                    showDeleteConfirm = false
                    delete()
                }) { Text("Löschen", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) { Text("Abbrechen") }
            },
        )
    }
}
