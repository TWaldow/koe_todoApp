package com.twaldow.koe.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class FolderDto(
    val id: Int,
    val name: String,
    val color: String,
    @SerialName("is_system") val isSystem: Boolean,
    val position: Int,
)

@Serializable
data class FolderCreateRequest(
    val name: String,
    val color: String,
)

@Serializable
data class FolderUpdateRequest(
    val name: String? = null,
    val color: String? = null,
    val position: Int? = null,
)
