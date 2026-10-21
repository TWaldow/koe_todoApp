package com.twaldow.koe.util

import com.twaldow.koe.domain.model.Recurrence
import com.twaldow.koe.domain.model.Todo
import org.junit.Assert.assertEquals
import org.junit.Test

class TodoGroupingTest {

    private fun todo(id: Int, recurrence: Recurrence) = Todo(
        id = id,
        text = "todo-$id",
        folderId = 1,
        important = false,
        recurrence = recurrence,
        dueType = null,
        dueDate = null,
        isDone = false,
        daysUntilDue = null,
    )

    @Test
    fun `splits todos into sections by recurrence`() {
        val todos = listOf(
            todo(1, Recurrence.NONE),
            todo(2, Recurrence.DAILY),
            todo(3, Recurrence.WEEKLY),
            todo(4, Recurrence.MONTHLY),
            todo(5, Recurrence.NONE),
        )

        val sections = todos.toSections()

        assertEquals(listOf(2), sections.daily.map { it.id })
        assertEquals(listOf(3), sections.weekly.map { it.id })
        assertEquals(listOf(4), sections.monthly.map { it.id })
        assertEquals(listOf(1, 5), sections.oneTime.map { it.id })
    }

    @Test
    fun `empty list produces empty sections`() {
        val sections = emptyList<Todo>().toSections()

        assertEquals(emptyList<Todo>(), sections.daily)
        assertEquals(emptyList<Todo>(), sections.weekly)
        assertEquals(emptyList<Todo>(), sections.monthly)
        assertEquals(emptyList<Todo>(), sections.oneTime)
    }
}
