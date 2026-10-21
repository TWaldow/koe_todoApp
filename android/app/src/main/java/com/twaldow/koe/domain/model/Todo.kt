package com.twaldow.koe.domain.model

import java.time.LocalDate

data class Todo(
    val id: Int,
    val text: String,
    val folderId: Int,
    val important: Boolean,
    val recurrence: Recurrence,
    val dueType: DueType?,
    val dueDate: LocalDate?,
    val isDone: Boolean,
    val daysUntilDue: Int?,
)
