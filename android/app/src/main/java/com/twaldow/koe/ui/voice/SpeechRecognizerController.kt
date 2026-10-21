package com.twaldow.koe.ui.voice

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * Dünner Wrapper um android.speech.SpeechRecognizer. Lange Stille-Timeouts, weil nicht die
 * Sprachpause das Ende der Aufnahme bestimmt, sondern Loslassen/Senden/Abbrechen am Button -
 * stop()/cancel() steuern das Ende aktiv.
 */
class SpeechRecognizerController(
    context: Context,
    private val onPartialResult: (String) -> Unit,
    private val onFinalResult: (String) -> Unit,
    private val onError: (String) -> Unit,
) {
    private val recognizer: SpeechRecognizer? =
        if (SpeechRecognizer.isRecognitionAvailable(context)) {
            SpeechRecognizer.createSpeechRecognizer(context)
        } else {
            null
        }

    init {
        recognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onPartialResults(bundle: Bundle) = emit(bundle, onPartialResult)
            override fun onResults(bundle: Bundle) = emit(bundle, onFinalResult)
            override fun onError(error: Int) {
                // KEIN Fehler, wenn wir selbst stop()/cancel() ausgelöst haben - das kommt als
                // ERROR_NO_MATCH/ERROR_CLIENT, aber onFinalResult wurde dann meist schon vorher
                // über onResults geliefert. Melden wir trotzdem, der Aufrufer entscheidet.
                onError(describeError(error))
            }

            override fun onReadyForSpeech(params: Bundle?) {}
            override fun onBeginningOfSpeech() {}
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
        })
    }

    val isAvailable: Boolean get() = recognizer != null

    fun start() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "de-DE")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 60_000)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 60_000)
        }
        recognizer?.startListening(intent)
    }

    /** Beendet die Aufnahme und liefert das Ergebnis über onFinalResult. */
    fun stop() = recognizer?.stopListening()

    /** Bricht ohne Ergebnis ab (Abbrechen-Kreis). */
    fun cancel() = recognizer?.cancel()

    fun destroy() = recognizer?.destroy()

    private fun emit(bundle: Bundle, callback: (String) -> Unit) {
        val text = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()
        if (text != null) callback(text)
    }

    private fun describeError(error: Int): String = when (error) {
        SpeechRecognizer.ERROR_NO_MATCH -> "Nichts verstanden"
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Keine Sprache erkannt"
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Mikrofon-Berechtigung fehlt"
        SpeechRecognizer.ERROR_NETWORK -> "Netzwerkfehler bei der Spracherkennung"
        else -> "Spracherkennung fehlgeschlagen (Code $error)"
    }
}
