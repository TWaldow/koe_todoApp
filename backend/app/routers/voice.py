from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import require_token
from app.db import get_db

router = APIRouter(
    prefix="/voice-todos", tags=["voice"], dependencies=[Depends(require_token)]
)


@router.post("", response_model=schemas.VoiceResponse)
def create_voice_todos(data: schemas.VoiceRequest, db: Session = Depends(get_db)):
    """Transkript -> Haiku -> Todos.

    - Ist Haiku unsicher: `question` zurückgeben, nichts speichern.
    - Erkannte Termine (`fixed`) nicht verwerfen, sondern unter `skipped` melden.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)