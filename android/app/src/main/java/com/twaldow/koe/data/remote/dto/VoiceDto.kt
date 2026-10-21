package com.twaldow.koe.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class VoiceRequest(
    val text: String,
    @SerialName("folder_id") val folderId: Int? = null,
    val answer: String? = null,
)

@Serializable
data class SkippedItemDto(
    val text: String,
    val reason: String,
)

@Serializable
data class VoiceResponse(
    val created: List<TodoDto>,
    val skipped: List<SkippedItemDto>,
    val question: String? = null,
)
