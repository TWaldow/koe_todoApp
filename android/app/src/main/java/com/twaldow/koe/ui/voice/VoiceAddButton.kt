package com.twaldow.koe.ui.voice

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChange
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.twaldow.koe.data.repository.VoiceRepository
import com.twaldow.koe.util.needsDarkText
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

private fun parseColor(hex: String): Color = Color(android.graphics.Color.parseColor(hex))

/**
 * Hinzufügen-Button: Tippen -> manuelles Formular, gedrückt halten -> Aufnahme, Loslassen ->
 * senden, Hochschieben -> fixieren (zwei Kreise: Senden/Abbrechen). Siehe spec-v1.md Abschnitt 4.
 *
 * Entscheidung: Mikrofon-Berechtigung wird beim ersten Halten angefragt; wird sie gerade erst
 * erteilt, muss der Nutzer einmal erneut gedrückt halten (kein Auto-Start mitten im
 * Berechtigungsdialog) - für v1 bewusst einfach gehalten.
 */
@Composable
fun VoiceAddButton(
    folderId: Int?,
    folderColorHex: String,
    onManualAdd: () -> Unit,
    onCreated: () -> Unit,
    voiceRepository: VoiceRepository = VoiceRepository(),
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val folderColor = parseColor(folderColorHex)
    val onColor = if (needsDarkText(folderColorHex)) Color.Black else Color.White

    var hasAudioPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
        )
    }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        hasAudioPermission = granted
    }

    var state by remember { mutableStateOf<VoiceUiState>(VoiceUiState.Idle) }

    fun sendTranscript(text: String) {
        state = VoiceUiState.Sending(text)
        scope.launch {
            try {
                val result = voiceRepository.send(text = text, folderId = folderId)
                if (result.question != null) {
                    // question-Rückfrage ist im Backend noch nicht implementiert (TODO in voice.py);
                    // wir zeigen sie trotzdem an, statt sie zu verschlucken.
                    state = VoiceUiState.Error(text, "Rückfrage: ${result.question}")
                } else {
                    state = VoiceUiState.Result(result)
                    onCreated()
                }
            } catch (e: Exception) {
                state = VoiceUiState.Error(text, e.message ?: e.toString())
            }
        }
    }

    val controller = remember {
        SpeechRecognizerController(
            context = context,
            onPartialResult = { text ->
                state = when (val s = state) {
                    is VoiceUiState.Recording -> VoiceUiState.Recording(text)
                    is VoiceUiState.Pinned -> VoiceUiState.Pinned(text)
                    else -> s
                }
            },
            onFinalResult = { text ->
                if (state is VoiceUiState.Recording || state is VoiceUiState.Pinned) {
                    sendTranscript(text)
                }
            },
            onError = { message ->
                val partial = when (val s = state) {
                    is VoiceUiState.Recording -> s.partialText
                    is VoiceUiState.Pinned -> s.text
                    else -> null
                }
                state = if (!partial.isNullOrBlank()) VoiceUiState.Error(partial, message) else VoiceUiState.Idle
            },
        )
    }
    DisposableEffect(Unit) { onDispose { controller.destroy() } }

    Column(horizontalAlignment = Alignment.End) {
        when (val s = state) {
            is VoiceUiState.Recording -> TranscriptBubble(s.partialText.ifBlank { "Höre zu…" })
            is VoiceUiState.Pinned -> TranscriptBubble(s.text.ifBlank { "Höre zu…" })
            is VoiceUiState.Error -> ErrorCard(
                message = s.message,
                transcript = s.transcript,
                onRetry = { sendTranscript(s.transcript) },
                onDismiss = { state = VoiceUiState.Idle },
            )
            else -> {}
        }

        when (val s = state) {
            is VoiceUiState.Pinned -> {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Box(
                        modifier = Modifier
                            .size(56.dp)
                            .border(width = 2.dp, color = folderColor, shape = CircleShape)
                            .clickable {
                                controller.cancel()
                                state = VoiceUiState.Idle
                            },
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Filled.Close, contentDescription = "Abbrechen", tint = folderColor)
                    }
                    Box(
                        modifier = Modifier
                            .size(56.dp)
                            .background(folderColor, CircleShape)
                            .clickable { controller.stop() },
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Filled.Check, contentDescription = "Senden", tint = onColor)
                    }
                }
            }
            is VoiceUiState.Sending -> {
                Box(modifier = Modifier.size(56.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = folderColor)
                }
            }
            else -> {
                // Idle/Recording/Error/Result teilen sich bewusst EINEN Composable-Aufruf (fester
                // Call-Site): wechselt man z. B. bei Idle->Recording in einen eigenen `when`-Zweig,
                // baut Compose eine neue Node und die laufende Geste (der Finger ist ja noch unten)
                // würde abgebrochen - mit einem gemeinsamen Aufruf bleibt pointerInput über den
                // ganzen Press-Hold-Drag-Vorgang hinweg an derselben Node und damit am Leben.
                PressToRecordButton(
                    onTap = onManualAdd,
                    onHoldStart = {
                        if (!hasAudioPermission) {
                            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                            false
                        } else if (!controller.isAvailable) {
                            state = VoiceUiState.Error("", "Spracherkennung auf diesem Gerät nicht verfügbar")
                            false
                        } else {
                            state = VoiceUiState.Recording("")
                            controller.start()
                            true
                        }
                    },
                    onPin = { state = VoiceUiState.Pinned((state as? VoiceUiState.Recording)?.partialText ?: "") },
                    onReleaseWithoutPin = { controller.stop() },
                    recording = state is VoiceUiState.Recording,
                    color = folderColor,
                )
                if (s is VoiceUiState.Result) {
                    VoiceResultDialog(result = s.result, onDismiss = { state = VoiceUiState.Idle })
                }
            }
        }
    }
}

/**
 * Eigene Gestenerkennung statt combinedClickable: wir brauchen Tippen, Halten *und* ein
 * Hochziehen während des Haltens gleichzeitig - dafür reichen die Standard-Click-Modifier
 * nicht. awaitFirstDown/waitForUpOrCancellation sind dieselben Bausteine, aus denen
 * detectTapGestures selbst gebaut ist.
 */
@Composable
private fun PressToRecordButton(
    onTap: () -> Unit,
    onHoldStart: () -> Boolean,
    onPin: () -> Unit,
    onReleaseWithoutPin: () -> Unit,
    recording: Boolean = false,
    color: Color = MaterialTheme.colorScheme.primary,
) {
    val pinThresholdPx = with(androidx.compose.ui.platform.LocalDensity.current) { 64.dp.toPx() }

    Box(
        modifier = Modifier
            .size(56.dp)
            .background(if (recording) color else MaterialTheme.colorScheme.primaryContainer, CircleShape)
            .pointerInput(Unit) {
                awaitEachGesture {
                    val down = awaitFirstDown(requireUnconsumed = false)
                    val longPressMillis = viewConfiguration.longPressTimeoutMillis
                    val upBeforeLongPress = withTimeoutOrNull(longPressMillis) { waitForUpOrCancellation() }
                    if (upBeforeLongPress != null) {
                        onTap()
                        return@awaitEachGesture
                    }
                    val started = onHoldStart()
                    if (!started) return@awaitEachGesture

                    var pinned = false
                    var totalDragY = 0f
                    while (true) {
                        val event = awaitPointerEvent()
                        val change = event.changes.firstOrNull { it.id == down.id } ?: break
                        if (!change.pressed) {
                            if (!pinned) onReleaseWithoutPin()
                            break
                        }
                        totalDragY += change.positionChange().y
                        change.consume()
                        if (!pinned && totalDragY < -pinThresholdPx) {
                            pinned = true
                            onPin()
                        }
                    }
                }
            },
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = Icons.Filled.Add,
            contentDescription = "Todo anlegen (tippen) oder aufnehmen (halten)",
            tint = if (recording) Color.White else MaterialTheme.colorScheme.onPrimaryContainer,
        )
    }
}

@Composable
private fun TranscriptBubble(text: String) {
    Card(modifier = Modifier.padding(bottom = 8.dp).widthIn(max = 260.dp)) {
        Text(text, modifier = Modifier.padding(12.dp), style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun ErrorCard(message: String, transcript: String, onRetry: () -> Unit, onDismiss: () -> Unit) {
    Card(modifier = Modifier.padding(bottom = 8.dp).widthIn(max = 280.dp)) {
        Column(modifier = Modifier.padding(12.dp)) {
            if (transcript.isNotBlank()) {
                Text("„$transcript“", style = MaterialTheme.typography.bodyMedium)
            }
            Text(message, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            Row {
                TextButton(onClick = onDismiss) { Text("Verwerfen") }
                if (transcript.isNotBlank()) {
                    TextButton(onClick = onRetry) { Text("Erneut senden") }
                }
            }
        }
    }
}

@Composable
private fun VoiceResultDialog(result: com.twaldow.koe.domain.model.VoiceResult, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Sprach-Todos") },
        text = {
            Column {
                if (result.created.isEmpty() && result.skipped.isEmpty()) {
                    Text("Nichts erkannt.")
                }
                result.created.forEach { todo -> Text("✓ ${todo.text}") }
                result.skipped.forEach { skipped ->
                    Text("– ${skipped.text} (${skipped.reason})", color = MaterialTheme.colorScheme.error)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("OK") }
        },
    )
}
