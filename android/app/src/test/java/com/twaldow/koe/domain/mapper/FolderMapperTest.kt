package com.twaldow.koe.domain.mapper

import com.twaldow.koe.data.remote.dto.FolderDto
import org.junit.Assert.assertEquals
import org.junit.Test

class FolderMapperTest {

    @Test
    fun `maps all fields`() {
        val dto = FolderDto(
            id = 1,
            name = "Allgemein",
            color = "#4169E1",
            isSystem = true,
            position = 0,
        )

        val folder = dto.toDomain()

        assertEquals(1, folder.id)
        assertEquals("Allgemein", folder.name)
        assertEquals("#4169E1", folder.color)
        assertEquals(true, folder.isSystem)
        assertEquals(0, folder.position)
    }
}
