import json

from anthropic import Anthropic

from app.config import env

_client: Anthropic | None = None

SYSTEM_PROMPT = """\
Du zerlegst ein gesprochenes Transkript in ein oder mehrere Todos.
Antworte NUR mit einem JSON-Array, kein Fließtext, keine Markdown-Fences.

Format pro Todo:
{"text": "", "folder": "", "important": false, "recurrence": "none",
 "due_type": null, "due_date": null}

- recurrence: "none" | "daily" | "weekly" | "monthly"
- due_type: null | "deadline" | "fixed" (fixed = fester Termin mit Uhrzeit)
- due_date: "YYYY-MM-DD" oder null
- folder: einer der gegebenen Ordnernamen, sonst der aktuelle Ordner
"""


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=env.anthropic_api_key)
    return _client


def parse_transcript(text: str, today_iso: str, weekday: str, folder_names: list[str], current_folder: str) -> list[dict]:
    user_message = (
        f"Heutiges Datum: {today_iso} ({weekday}), Zeitzone Europe/Berlin\n"
        f"Ordner: {', '.join(folder_names)}\n"
        f"Aktueller Ordner: {current_folder}\n\n"
        f"Transkript: {text}"
    )

    response = _get_client().messages.create(
        model="claude-haiku-5-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text_blocks = [b.text for b in response.content if b.type == "text"]
    if not text_blocks:
        raise ValueError("No text block in Claude response")

    raw = text_blocks[0].strip()
    if raw.startswith("```"):  # falls Haiku doch Markdown-Fences schickt
        raw = raw.strip("`").removeprefix("json").strip()
    return json.loads(raw)