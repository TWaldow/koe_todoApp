package com.twaldow.koe.domain.mapper

import com.twaldow.koe.data.remote.dto.FolderDto
import com.twaldow.koe.domain.model.Folder

fun FolderDto.toDomain(): Folder = Folder(
    id = id,
    name = name,
    color = color,
    isSystem = isSystem,
    position = position,
)
