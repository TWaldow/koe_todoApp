package com.twaldow.koe.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.twaldow.koe.data.repository.FolderRepository
import com.twaldow.koe.data.repository.TodoRepository
import com.twaldow.koe.domain.model.Folder
import com.twaldow.koe.domain.model.Todo
import com.twaldow.koe.util.TodoSections
import com.twaldow.koe.util.toSections
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class MainUiState(
    val folders: List<Folder> = emptyList(),
    val currentFolderIndex: Int = 0,
    val urgentTodos: List<Todo> = emptyList(),
    val sections: TodoSections = TodoSections(emptyList(), emptyList(), emptyList(), emptyList()),
    val isLoading: Boolean = true,
    val error: String? = null,
) {
    val currentFolder: Folder? get() = folders.getOrNull(currentFolderIndex)
}

/**
 * Thin Client: haelt nur den aktuell angezeigten Zustand im Speicher, holt bei jeder
 * Aktion frisch vom Backend statt lokal zu cachen (siehe CONTEXT.md). Activity-scoped
 * (eine Instanz, siehe MainActivity), damit Edit-/Ordner-/Voice-Screens denselben
 * Zustand sehen und nach Rückkehr per [refresh] aktualisieren können.
 */
class MainViewModel(
    private val folderRepository: FolderRepository = FolderRepository(),
    private val todoRepository: TodoRepository = TodoRepository(),
) : ViewModel() {

    private val _uiState = MutableStateFlow(MainUiState())
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()

    /** Zwischenspeicher für den Sprung zum Bearbeiten-Formular - kein echter State (siehe EditTodoScreen). */
    var pendingEditTodo: Todo? = null

    init {
        loadFolders()
    }

    fun loadFolders() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                val folders = folderRepository.getFolders()
                val index = _uiState.value.currentFolder?.let { current ->
                    folders.indexOfFirst { it.id == current.id }.takeIf { it >= 0 }
                } ?: 0
                _uiState.update { it.copy(folders = folders, currentFolderIndex = index) }
                loadUrgentTodos()
                loadTodosForCurrentFolder()
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, error = e.message ?: e.toString()) }
            }
        }
    }

    fun selectFolder(index: Int) {
        if (index == _uiState.value.currentFolderIndex) return
        _uiState.update { it.copy(currentFolderIndex = index) }
        loadTodosForCurrentFolder()
    }

    /** Nach Rückkehr von Edit-/Ordner-/Voice-Screens: alles neu laden (kein lokaler Cache). */
    fun refresh() {
        loadFolders()
    }

    fun completeTodo(id: Int) {
        viewModelScope.launch {
            try {
                todoRepository.completeTodo(id)
                loadTodosForCurrentFolder()
                loadUrgentTodos()
            } catch (e: Exception) {
                _uiState.update { it.copy(error = e.message ?: e.toString()) }
            }
        }
    }

    fun uncompleteTodo(id: Int) {
        viewModelScope.launch {
            try {
                todoRepository.uncompleteTodo(id)
                loadTodosForCurrentFolder()
                loadUrgentTodos()
            } catch (e: Exception) {
                _uiState.update { it.copy(error = e.message ?: e.toString()) }
            }
        }
    }

    private fun loadTodosForCurrentFolder() {
        val folder = _uiState.value.currentFolder ?: return
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                val todos = todoRepository.getTodosForFolder(folder.id)
                _uiState.update { it.copy(sections = todos.toSections(), isLoading = false) }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, error = e.message ?: e.toString()) }
            }
        }
    }

    private fun loadUrgentTodos() {
        viewModelScope.launch {
            try {
                val urgent = todoRepository.getUrgentTodos()
                _uiState.update { it.copy(urgentTodos = urgent) }
            } catch (e: Exception) {
                _uiState.update { it.copy(error = e.message ?: e.toString()) }
            }
        }
    }
}
