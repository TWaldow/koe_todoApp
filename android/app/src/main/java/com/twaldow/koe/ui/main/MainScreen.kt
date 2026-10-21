package com.twaldow.koe.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Snackbar
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import com.twaldow.koe.domain.model.Folder
import com.twaldow.koe.domain.model.Todo
import com.twaldow.koe.ui.voice.VoiceAddButton
import com.twaldow.koe.util.needsDarkText
import com.twaldow.koe.viewmodel.MainUiState
import com.twaldow.koe.viewmodel.MainViewModel
import kotlinx.coroutines.launch

private fun parseColor(hex: String): Color = Color(android.graphics.Color.parseColor(hex))

@Composable
fun MainScreen(
    navController: NavHostController,
    viewModel: MainViewModel,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsState()
    val folders = uiState.folders
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    fun onToggle(todo: Todo) {
        if (todo.isDone) {
            viewModel.uncompleteTodo(todo.id)
        } else {
            viewModel.completeTodo(todo.id)
            scope.launch {
                val result = snackbarHostState.showSnackbar("Erledigt", actionLabel = "Rückgängig")
                if (result == SnackbarResult.ActionPerformed) {
                    viewModel.uncompleteTodo(todo.id)
                }
            }
        }
    }

    fun onEdit(todo: Todo) {
        viewModel.pendingEditTodo = todo
        navController.navigate("edit_todo")
    }

    fun onAdd() {
        viewModel.pendingEditTodo = null
        navController.navigate("edit_todo")
    }

    Scaffold(
        modifier = modifier,
        snackbarHost = { SnackbarHost(snackbarHostState) },
        floatingActionButton = {
            VoiceAddButton(
                folderId = uiState.currentFolder?.id,
                folderColorHex = uiState.currentFolder?.color ?: "#4169E1",
                onManualAdd = { onAdd() },
                onCreated = { viewModel.refresh() },
            )
        },
    ) { padding ->
        if (folders.isEmpty()) {
            Box(Modifier.fillMaxSize().padding(padding), contentAlignment = Alignment.Center) {
                if (uiState.error != null) {
                    Text("Fehler: ${uiState.error}")
                } else {
                    CircularProgressIndicator()
                }
            }
            return@Scaffold
        }

        val pagerState = rememberPagerState(initialPage = 0) { folders.size }
        LaunchedEffect(pagerState.currentPage) {
            viewModel.selectFolder(pagerState.currentPage)
        }

        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            FolderHeader(
                folder = folders[pagerState.currentPage],
                folderCount = folders.size,
                currentIndex = pagerState.currentPage,
                onHeaderClick = { navController.navigate("folders") },
            )

            HorizontalPager(state = pagerState, modifier = Modifier.fillMaxSize()) { page ->
                if (page == uiState.currentFolderIndex && !uiState.isLoading) {
                    FolderTodoList(folder = folders[page], uiState = uiState, onToggle = ::onToggle, onEdit = ::onEdit)
                } else {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
            }
        }
    }
}

@Composable
private fun FolderHeader(folder: Folder, folderCount: Int, currentIndex: Int, onHeaderClick: () -> Unit) {
    val color = parseColor(folder.color)
    Column(
        modifier = Modifier.fillMaxWidth().padding(top = 24.dp, bottom = 12.dp).clickable { onHeaderClick() },
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = folder.name, style = MaterialTheme.typography.headlineMedium, color = color)
        if (folderCount > 1) {
            Row(modifier = Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                repeat(folderCount) { index ->
                    val dotColor = if (index == currentIndex) color else MaterialTheme.colorScheme.outlineVariant
                    Box(
                        modifier = Modifier
                            .size(6.dp)
                            .background(dotColor, CircleShape)
                    )
                }
            }
        }
    }
}

@Composable
private fun FolderTodoList(
    folder: Folder,
    uiState: MainUiState,
    onToggle: (Todo) -> Unit,
    onEdit: (Todo) -> Unit,
) {
    val sections = uiState.sections
    val isEmpty = uiState.urgentTodos.isEmpty() &&
        sections.daily.isEmpty() && sections.weekly.isEmpty() && sections.monthly.isEmpty() && sections.oneTime.isEmpty()

    if (isEmpty) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text(
                "Keine Todos in \"${folder.name}\"",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        return
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        if (uiState.urgentTodos.isNotEmpty()) {
            item { SectionLabel("Dringend") }
            items(uiState.urgentTodos, key = { "urgent-${it.id}" }) { todo ->
                TodoRow(todo = todo, folderColorHex = folder.color, onToggle = onToggle, onEdit = onEdit)
            }
        }

        val hasRecurring = sections.daily.isNotEmpty() || sections.weekly.isNotEmpty() || sections.monthly.isNotEmpty()
        if (hasRecurring) {
            item { SectionLabel("Wiederkehrend") }
            if (sections.daily.isNotEmpty()) {
                item { SubSectionLabel("Täglich") }
                items(sections.daily, key = { "daily-${it.id}" }) { todo ->
                    TodoRow(todo = todo, folderColorHex = folder.color, onToggle = onToggle, onEdit = onEdit)
                }
            }
            if (sections.weekly.isNotEmpty()) {
                item { SubSectionLabel("Wöchentlich") }
                items(sections.weekly, key = { "weekly-${it.id}" }) { todo ->
                    TodoRow(todo = todo, folderColorHex = folder.color, onToggle = onToggle, onEdit = onEdit)
                }
            }
            if (sections.monthly.isNotEmpty()) {
                item { SubSectionLabel("Monatlich") }
                items(sections.monthly, key = { "monthly-${it.id}" }) { todo ->
                    TodoRow(todo = todo, folderColorHex = folder.color, onToggle = onToggle, onEdit = onEdit)
                }
            }
        }

        item { SectionLabel("Einmalig") }
        items(sections.oneTime, key = { "once-${it.id}" }) { todo ->
            TodoRow(todo = todo, folderColorHex = folder.color, onToggle = onToggle, onEdit = onEdit)
        }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleLarge,
        fontWeight = androidx.compose.ui.text.font.FontWeight.Bold,
        modifier = Modifier.padding(top = 16.dp, bottom = 4.dp),
    )
}

@Composable
private fun SubSectionLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.padding(top = 8.dp, bottom = 2.dp, start = 8.dp),
    )
}

/**
 * Wichtige Todos bekommen einen Zeilenhintergrund in Ordnerfarbe; Text-/Iconfarbe darauf
 * wird per Helligkeitsberechnung gewählt (needsDarkText), damit es z. B. auf Gelb lesbar bleibt.
 * Tippen auf die Checkbox hakt ab/entfernt den Haken, Tippen auf den Rest der Zeile öffnet
 * das Bearbeiten-Formular.
 */
@Composable
private fun TodoRow(todo: Todo, folderColorHex: String, onToggle: (Todo) -> Unit, onEdit: (Todo) -> Unit) {
    val background = if (todo.important) parseColor(folderColorHex) else Color.Transparent
    val contentColor = if (todo.important) {
        if (needsDarkText(folderColorHex)) Color.Black else Color.White
    } else {
        MaterialTheme.colorScheme.onSurface
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(background, RoundedCornerShape(14.dp))
            .clickable { onEdit(todo) }
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (todo.isDone) {
            Icon(
                imageVector = Icons.Filled.CheckCircle,
                contentDescription = "Erledigt, antippen zum Entfernen",
                tint = contentColor,
                modifier = Modifier.clickable { onToggle(todo) },
            )
        } else {
            Box(
                modifier = Modifier
                    .size(24.dp)
                    .border(width = 2.dp, color = contentColor, shape = CircleShape)
                    .clickable { onToggle(todo) }
            )
        }
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = todo.text,
                color = contentColor,
                textDecoration = if (todo.isDone) TextDecoration.LineThrough else null,
            )
            deadlineLabel(todo)?.let { label ->
                Text(text = label, style = MaterialTheme.typography.labelSmall, color = contentColor)
            }
        }
    }
}

private fun deadlineLabel(todo: Todo): String? {
    val days = todo.daysUntilDue ?: return null
    return when {
        days < 0 -> "seit ${-days} Tagen überfällig"
        days == 0 -> "heute fällig"
        else -> "noch $days Tage"
    }
}
