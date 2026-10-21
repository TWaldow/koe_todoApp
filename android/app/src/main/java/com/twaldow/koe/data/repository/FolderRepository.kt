package com.twaldow.koe.data.repository

import com.twaldow.koe.data.remote.KoeApi
import com.twaldow.koe.data.remote.NetworkModule
import com.twaldow.koe.data.remote.dto.FolderCreateRequest
import com.twaldow.koe.data.remote.dto.FolderUpdateRequest
import com.twaldow.koe.domain.mapper.toDomain
import com.twaldow.koe.domain.model.Folder

class FolderRepository(private val api: KoeApi = NetworkModule.api) {

    suspend fun getFolders(): List<Folder> = api.getFolders().map { it.toDomain() }

    suspend fun createFolder(name: String, color: String): Folder =
        api.createFolder(FolderCreateRequest(name = name, color = color)).toDomain()

    suspend fun updateFolder(
        id: Int,
        name: String? = null,
        color: String? = null,
        position: Int? = null,
    ): Folder = api.updateFolder(id, FolderUpdateRequest(name = name, color = color, position = position)).toDomain()

    suspend fun deleteFolder(id: Int) = api.deleteFolder(id)
}
