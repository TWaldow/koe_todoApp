package com.twaldow.koe.domain.model

data class SkippedItem(
    val text: String,
    val reason: String,
)

data class VoiceResult(
    val created: List<Todo>,
    val skipped: List<SkippedItem>,
    val question: String?,
)
