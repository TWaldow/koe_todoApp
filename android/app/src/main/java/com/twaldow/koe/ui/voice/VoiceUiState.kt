package com.twaldow.koe.ui.voice

import com.twaldow.koe.domain.model.VoiceResult

/** Zustandsautomat für den Hinzufügen-Button (spec-v1.md Abschnitt 4). */
sealed interface VoiceUiState {
    data object Idle : VoiceUiState
    data class Recording(val partialText: String) : VoiceUiState
    /** Hochgeschoben: Aufnahme läuft weiter, Button ist in Senden/Abbrechen geteilt. */
    data class Pinned(val text: String) : VoiceUiState
    data class Sending(val text: String) : VoiceUiState
    data class Result(val result: VoiceResult) : VoiceUiState
    /** Schlägt der Request fehl, bleibt das Transkript erhalten (spec: nie verloren gehen). */
    data class Error(val transcript: String, val message: String) : VoiceUiState
}
