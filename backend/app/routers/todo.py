from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import require_token
from app.db import get_db

router = APIRouter(prefix="/todos", tags=["todos"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[schemas.TodoRead])
def list_todos(
    folder_id: int | None = None,
    view: Literal["routine"] | None = None,
    db: Session = Depends(get_db),
):
    """Sichtbare Todos eines Ordners (`folder_id`) oder alle wiederkehrenden (`view=routine`)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/urgent", response_model=list[schemas.TodoRead])
def list_urgent(db: Session = Depends(get_db)):
    """Dringend-Bereich: einmalig, Deadline, offen, wichtig, <= 2 Tage bis fällig."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("", response_model=schemas.TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(data: schemas.TodoCreate, db: Session = Depends(get_db)):
    """Manuell anlegen. Ohne `folder_id` -> Allgemein. Bei Wiederholung: Anker = heute."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.patch("/{todo_id}", response_model=schemas.TodoRead)
def update_todo(todo_id: int, data: schemas.TodoUpdate, db: Session = Depends(get_db)):
    """Bearbeiten. Ändert sich `recurrence`, wird der Anker auf heute gesetzt."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Löschen (die App fragt vorher nach)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{todo_id}/complete", response_model=schemas.TodoRead)
def complete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Abhaken: `completed_at = now`."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{todo_id}/uncomplete", response_model=schemas.TodoRead)
def uncomplete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Haken entfernen: `completed_at = null`."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)