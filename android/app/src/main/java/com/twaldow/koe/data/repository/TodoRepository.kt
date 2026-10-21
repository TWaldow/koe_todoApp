package com.twaldow.koe.data.repository

import com.twaldow.koe.data.remote.KoeApi
import com.twaldow.koe.data.remote.NetworkModule
import com.twaldow.koe.data.remote.dto.TodoCreateRequest
import com.twaldow.koe.data.remote.dto.TodoUpdateRequest
import com.twaldow.koe.domain.mapper.toDomain
import com.twaldow.koe.domain.model.DueType
import com.twaldow.koe.domain.model.Recurrence
import com.twaldow.koe.domain.model.Todo
import java.time.LocalDate

class TodoRepository(private val api: KoeApi = NetworkModule.api) {

    suspend fun getTodosForFolder(folderId: Int): List<Todo> =
        api.getTodosForFolder(folderId).map { it.toDomain() }

    suspend fun getUrgentTodos(): List<Todo> = api.getUrgentTodos().map { it.toDomain() }

    suspend fun createTodo(
        text: String,
        folderId: Int?,
        important: Boolean,
        recurrence: Recurrence,
        dueType: DueType?,
        dueDate: LocalDate?,
    ): Todo = api.createTodo(
        TodoCreateRequest(
            text = text,
            folderId = folderId,
            important = important,
            recurrence = recurrence,
            dueType = dueType,
            dueDate = dueDate?.toString(),
        )
    ).toDomain()

    suspend fun updateTodo(
        id: Int,
        text: String,
        folderId: Int,
        important: Boolean,
        recurrence: Recurrence,
        dueType: DueType?,
        dueDate: LocalDate?,
    ): Todo = api.updateTodo(
        id,
        TodoUpdateRequest(
            text = text,
            folderId = folderId,
            important = important,
            recurrence = recurrence,
            dueType = dueType,
            dueDate = dueDate?.toString(),
        )
    ).toDomain()

    suspend fun deleteTodo(id: Int) = api.deleteTodo(id)

    suspend fun completeTodo(id: Int): Todo = api.completeTodo(id).toDomain()

    suspend fun uncompleteTodo(id: Int): Todo = api.uncompleteTodo(id).toDomain()
}
