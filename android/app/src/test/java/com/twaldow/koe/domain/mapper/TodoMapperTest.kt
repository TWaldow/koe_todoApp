package com.twaldow.koe.domain.mapper

import com.twaldow.koe.data.remote.dto.TodoDto
import com.twaldow.koe.domain.model.DueType
import com.twaldow.koe.domain.model.Recurrence
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.LocalDate

class TodoMapperTest {

    private fun dto(dueDate: String? = null) = TodoDto(
        id = 1,
        text = "Zahnarzt",
        folderId = 2,
        important = true,
        recurrence = Recurrence.NONE,
        recurrenceAnchor = null,
        dueType = if (dueDate != null) DueType.DEADLINE else null,
        dueDate = dueDate,
        completedAt = null,
        createdAt = "2026-01-01T10:00:00+00:00",
        updatedAt = "2026-01-01T10:00:00+00:00",
        isDone = false,
        daysUntilDue = 2,
    )

    @Test
    fun `maps all displayed fields`() {
        val todo = dto(dueDate = "2026-03-05").toDomain()

        assertEquals(1, todo.id)
        assertEquals("Zahnarzt", todo.text)
        assertEquals(2, todo.folderId)
        assertEquals(true, todo.important)
        assertEquals(Recurrence.NONE, todo.recurrence)
        assertEquals(DueType.DEADLINE, todo.dueType)
        assertEquals(LocalDate.of(2026, 3, 5), todo.dueDate)
        assertEquals(false, todo.isDone)
        assertEquals(2, todo.daysUntilDue)
    }

    @Test
    fun `missing due date maps to null, not an exception`() {
        val todo = dto(dueDate = null).toDomain()

        assertNull(todo.dueDate)
        assertNull(todo.dueType)
    }
}
