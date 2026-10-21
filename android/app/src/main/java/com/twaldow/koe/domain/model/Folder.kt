package com.twaldow.koe.domain.model

data class Folder(
    val id: Int,
    val name: String,
    val color: String,
    val isSystem: Boolean,
    val position: Int,
)
