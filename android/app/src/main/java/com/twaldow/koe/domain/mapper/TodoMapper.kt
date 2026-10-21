package com.twaldow.koe.domain.mapper

import com.twaldow.koe.data.remote.dto.TodoDto
import com.twaldow.koe.domain.model.Todo
import java.time.LocalDate

fun TodoDto.toDomain(): Todo = Todo(
    id = id,
    text = text,
    folderId = folderId,
    important = important,
    recurrence = recurrence,
    dueType = dueType,
    dueDate = dueDate?.let { LocalDate.parse(it) },
    isDone = isDone,
    daysUntilDue = daysUntilDue,
)
