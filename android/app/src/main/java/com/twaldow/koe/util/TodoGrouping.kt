package com.twaldow.koe.util

import com.twaldow.koe.domain.model.Recurrence
import com.twaldow.koe.domain.model.Todo

/** Abschnitte des Hauptscreens fuer einen Ordner (spec-v1.md Abschnitt 4), ohne Dringend -
 * das ist ordnerübergreifend und kommt aus einem eigenen Endpoint (/todos/urgent). */
data class TodoSections(
    val daily: List<Todo>,
    val weekly: List<Todo>,
    val monthly: List<Todo>,
    val oneTime: List<Todo>,
)

fun List<Todo>.toSections(): TodoSections = TodoSections(
    daily = filter { it.recurrence == Recurrence.DAILY },
    weekly = filter { it.recurrence == Recurrence.WEEKLY },
    monthly = filter { it.recurrence == Recurrence.MONTHLY },
    oneTime = filter { it.recurrence == Recurrence.NONE },
)
