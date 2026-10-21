package com.twaldow.koe.data.repository

import com.twaldow.koe.data.remote.KoeApi
import com.twaldow.koe.data.remote.NetworkModule
import com.twaldow.koe.data.remote.dto.VoiceRequest
import com.twaldow.koe.domain.mapper.toDomain
import com.twaldow.koe.domain.model.SkippedItem
import com.twaldow.koe.domain.model.VoiceResult

class VoiceRepository(private val api: KoeApi = NetworkModule.api) {

    suspend fun send(text: String, folderId: Int?, answer: String? = null): VoiceResult {
        val response = api.createVoiceTodos(VoiceRequest(text = text, folderId = folderId, answer = answer))
        return VoiceResult(
            created = response.created.map { it.toDomain() },
            skipped = response.skipped.map { SkippedItem(it.text, it.reason) },
            question = response.question,
        )
    }
}
