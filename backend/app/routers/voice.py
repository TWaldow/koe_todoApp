from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.auth import require_token
from app.database import get_db
from app.enums import DueType, Recurrence
from app.models import Folder, ServerSettings, Todo
from app.serializers import to_read, logical_now
from app import claude_client

router = APIRouter(prefix="/voice-todos", tags=["voice"], dependencies=[Depends(require_token)])

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


# TODO: question-Rückfrage bei Unsicherheit noch nicht implementiert (siehe spec-v1.md)
@router.post("", response_model=schemas.VoiceResponse)
def create_voice_todos(data: schemas.VoiceRequest, db: Session = Depends(get_db)):
    """Transkript -> Haiku -> Todos.

    - Ist Haiku unsicher: `question` zurückgeben, nichts speichern.
    - Erkannte Termine (`fixed`) nicht verwerfen, sondern unter `skipped` melden.
    """

    if data.folder_id is not None and db.get(Folder, data.folder_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    settings = db.get(ServerSettings, 1)
    today = datetime.now(ZoneInfo(settings.timezone)).date()

    folders = db.scalars(select(Folder)).all()
    folder_by_name = {f.name: f.id for f in folders}
    current_folder = db.get(Folder, data.folder_id) if data.folder_id else None
    current_folder_name = current_folder.name if current_folder else "Allgemein"

    try:
        items = claude_client.parse_transcript(
            text=data.text,
            today_iso=today.isoformat(),
            weekday=WEEKDAYS[today.weekday()],
            folder_names=list(folder_by_name.keys()),
            current_folder=current_folder_name,
        )
    except (ValueError, KeyError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not parse response from Claude",
        )

    created: list[Todo] = []
    skipped: list[dict] = []

    for item in items:
        due_type = item.get("due_type")

        if due_type == DueType.FIXED.value:
            skipped.append({"text": item["text"], "reason": "fixed_not_supported"})
            continue

        folder_id = folder_by_name.get(item.get("folder"), folder_by_name.get("Allgemein"))
        recurrence = Recurrence(item.get("recurrence", "none"))

        todo = Todo(
            text=item["text"],
            folder_id=folder_id,
            important=item.get("important", False),
            recurrence=recurrence,
            recurrence_anchor=today if recurrence != Recurrence.NONE else None,
            due_type=DueType(due_type) if due_type else None,
            due_date=item.get("due_date"),
        )
        db.add(todo)
        created.append(todo)

        db.commit()
    today, day_start = logical_now(db)
    for todo in created:
        db.refresh(todo)

    return schemas.VoiceResponse(
        created=[to_read(t, today, day_start) for t in created],
        skipped=skipped,
        question=None,
    )