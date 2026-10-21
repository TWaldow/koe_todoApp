package com.twaldow.koe.domain.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class Recurrence {
    @SerialName("none") NONE,
    @SerialName("daily") DAILY,
    @SerialName("weekly") WEEKLY,
    @SerialName("monthly") MONTHLY,
}

@Serializable
enum class DueType {
    @SerialName("deadline") DEADLINE,
    @SerialName("fixed") FIXED,
}
