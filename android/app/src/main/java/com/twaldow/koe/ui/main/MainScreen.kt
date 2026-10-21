package com.twaldow.koe.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.twaldow.koe.domain.model.Folder
import com.twaldow.koe.domain.model.Todo
import com.twaldow.koe.util.needsDarkText
import com.twaldow.koe.viewmodel.MainUiState
import com.twaldow.koe.viewmodel.MainViewModel

private fun parseColor(hex: String): Color = Color(android.graphics.Color.parseColor(hex))

@Composable
fun MainScreen(modifier: Modifier = Modifier, viewModel: MainViewModel = viewModel()) {
    val uiState by viewModel.uiState.collectAsState()
    val folders = uiState.folders

    if (folders.isEmpty()) {
        Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            if (uiState.error != null) {
                Text("Fehler: ${uiState.error}")
            } else {
                CircularProgressIndicator()
            }
        }
        return
    }

    val pagerState = rememberPagerState(initialPage = 0) { folders.size }
    LaunchedEffect(pagerState.currentPage) {
        viewModel.selectFolder(pagerState.currentPage)
    }

    Column(modifier = modifier.fillMaxSize()) {
        FolderHeader(folder = folders[pagerState.currentPage], folderCount = folders.size, currentIndex = pagerState.currentPage)

        HorizontalPager(state = pagerState, modifier = Modifier.fillMaxSize()) { page ->
            if (page == uiState.currentFolderIndex && !uiState.isLoading) {
                FolderTodoList(folder = folders[page], uiState = uiState)
            } else {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
        }
    }
}

@Composable
private fun FolderHeader(folder: Folder, folderCount: Int, currentIndex: Int) {
    val color = parseColor(folder.color)
    Column(
        modifier = Modifier.fillMaxWidth().padding(top = 24.dp, bottom = 12.dp),
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
private fun FolderTodoList(folder: Folder, uiState: MainUiState) {
    val sections = uiState.sections
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        if (uiState.urgentTodos.isNotEmpty()) {
            item { SectionLabel("Dringend") }
            items(uiState.urgentTodos, key = { "urgent-${it.id}" }) { todo ->
                TodoRow(todo = todo, folderColorHex = folder.color)
            }
        }

        val hasRecurring = sections.daily.isNotEmpty() || sections.weekly.isNotEmpty() || sections.monthly.isNotEmpty()
        if (hasRecurring) {
            item { SectionLabel("Wiederkehrend") }
            if (sections.daily.isNotEmpty()) {
                item { SubSectionLabel("Täglich") }
                items(sections.daily, key = { "daily-${it.id}" }) { todo ->
                    TodoRow(todo = todo, folderColorHex = folder.color)
                }
            }
            if (sections.weekly.isNotEmpty()) {
                item { SubSectionLabel("Wöchentlich") }
                items(sections.weekly, key = { "weekly-${it.id}" }) { todo ->
                    TodoRow(todo = todo, folderColorHex = folder.color)
                }
            }
            if (sections.monthly.isNotEmpty()) {
                item { SubSectionLabel("Monatlich") }
                items(sections.monthly, key = { "monthly-${it.id}" }) { todo ->
                    TodoRow(todo = todo, folderColorHex = folder.color)
                }
            }
        }

        item { SectionLabel("Einmalig") }
        items(sections.oneTime, key = { "once-${it.id}" }) { todo ->
            TodoRow(todo = todo, folderColorHex = folder.color)
        }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleMedium,
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
 * Checkbox ist hier nur Anzeige (kein Klick-Handler) - Abhaken kommt in Schritt b.
 * Wichtige Todos bekommen einen Zeilenhintergrund in Ordnerfarbe; Text-/Iconfarbe darauf
 * wird per Helligkeitsberechnung gewählt (needsDarkText), damit es z. B. auf Gelb lesbar bleibt.
 */
@Composable
private fun TodoRow(todo: Todo, folderColorHex: String) {
    val background = if (todo.important) parseColor(folderColorHex) else Color.Transparent
    val contentColor = if (todo.important) {
        if (needsDarkText(folderColorHex)) Color.Black else Color.White
    } else {
        MaterialTheme.colorScheme.onSurface
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(background, RoundedCornerShape(8.dp))
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (todo.isDone) {
            Icon(imageVector = Icons.Filled.CheckCircle, contentDescription = null, tint = contentColor)
        } else {
            Box(
                modifier = Modifier
                    .size(24.dp)
                    .border(width = 2.dp, color = contentColor, shape = CircleShape)
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
