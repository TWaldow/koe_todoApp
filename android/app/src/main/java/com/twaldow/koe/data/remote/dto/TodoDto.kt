package com.twaldow.koe.data.remote.dto

import com.twaldow.koe.domain.model.DueType
import com.twaldow.koe.domain.model.Recurrence
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Spiegelt `schemas.TodoRead`. Datums-/Zeitfelder bleiben als ISO-String, das Parsen in
 * `java.time`-Typen passiert erst beim Mapping auf [com.twaldow.koe.domain.model.Todo].
 */
@Serializable
data class TodoDto(
    val id: Int,
    val text: String,
    @SerialName("folder_id") val folderId: Int,
    val important: Boolean,
    val recurrence: Recurrence,
    @SerialName("recurrence_anchor") val recurrenceAnchor: String? = null,
    @SerialName("due_type") val dueType: DueType? = null,
    @SerialName("due_date") val dueDate: String? = null,
    @SerialName("completed_at") val completedAt: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("updated_at") val updatedAt: String,
    @SerialName("is_done") val isDone: Boolean,
    @SerialName("days_until_due") val daysUntilDue: Int? = null,
)

@Serializable
data class TodoCreateRequest(
    val text: String,
    @SerialName("folder_id") val folderId: Int? = null,
    val important: Boolean = false,
    val recurrence: Recurrence = Recurrence.NONE,
    @SerialName("due_type") val dueType: DueType? = null,
    @SerialName("due_date") val dueDate: String? = null,
)

/**
 * Wird immer mit dem kompletten aktuellen Formularzustand befüllt (nie mit nur geänderten
 * Feldern). `dueType`/`dueDate` haben bewusst **keinen** Default: ein Property ohne Default
 * wird von kotlinx.serialization immer mitgeschickt, auch wenn der Wert `null` ist - sonst
 * würde eine entfernte Deadline beim Serialisieren stillschweigend wegfallen (siehe
 * FolderUpdateRequest, wo echte Teil-Updates mit weggelassenen Feldern gewünscht sind).
 */
@Serializable
data class TodoUpdateRequest(
    val text: String,
    @SerialName("folder_id") val folderId: Int,
    val important: Boolean,
    val recurrence: Recurrence,
    @SerialName("due_type") val dueType: DueType?,
    @SerialName("due_date") val dueDate: String?,
)
