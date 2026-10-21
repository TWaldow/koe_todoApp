from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.enums import DueType, Recurrence
from app.models import Folder, ServerSettings, Todo

from app.auth import require_token
from app import recurrence
from app.serializers import to_read, logical_now

router = APIRouter(prefix="/todos", tags=["todos"], dependencies=[Depends(require_token)])
# ---------- Hilfsfunktionen (wandern später nach recurrence.py) ----------


def get_todo_or_404(db: Session, todo_id: int) -> Todo:
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


def require_folder(db: Session, folder_id: int) -> None:
    if db.get(Folder, folder_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")


# ---------- Lesen ----------

@router.get("", response_model=list[schemas.TodoRead])
def list_todos(
    folder_id: int | None = None,
    view: Literal["routine"] | None = None,
    db: Session = Depends(get_db),
):
    """Sichtbare Todos eines Ordners (`folder_id`) oder alle wiederkehrenden (`view=routine`)."""
    if (view is None) == (folder_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one of folder_id or view=routine is required",
        )

    today, day_start = logical_now(db)
    stmt = select(Todo)

    if view == "routine":
        stmt = stmt.where(Todo.recurrence != Recurrence.NONE)
    else:
        require_folder(db, folder_id)
        # Einmalige sind sichtbar, solange offen oder heute erledigt. Wiederkehrende immer.
        stmt = stmt.where(
            Todo.folder_id == folder_id,
            or_(
                Todo.recurrence != Recurrence.NONE,
                Todo.completed_at.is_(None),
                Todo.completed_at >= day_start,
            ),
        )

    todos = db.scalars(stmt.order_by(Todo.created_at, Todo.id)).all()
    return [to_read(t, today, day_start) for t in todos]


@router.get("/urgent", response_model=list[schemas.TodoRead])
def list_urgent(db: Session = Depends(get_db)):
    """Dringend-Bereich: einmalig, Deadline, offen, wichtig, <= 2 Tage bis fällig."""
    today, day_start = logical_now(db)
    todos = db.scalars(
        select(Todo)
        .where(
            Todo.recurrence == Recurrence.NONE,
            Todo.due_type == DueType.DEADLINE,
            Todo.completed_at.is_(None),
            Todo.important.is_(True),
            Todo.due_date <= today + timedelta(days=2),
        )
        .order_by(Todo.due_date)  # am längsten Überfälliges oben
    ).all()
    return [to_read(t, today, day_start) for t in todos]


# ---------- Anlegen / Ändern / Löschen ----------

@router.post("", response_model=schemas.TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(data: schemas.TodoCreate, db: Session = Depends(get_db)):
    """Manuell anlegen. Ohne `folder_id` -> Allgemein. Bei Wiederholung: Anker = heute."""
    if data.due_type == DueType.FIXED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="due_type 'fixed' is not supported in v1",
        )

    if data.folder_id is None:
        folder_id = db.scalar(select(Folder.id).where(Folder.is_system))
    else:
        require_folder(db, data.folder_id)
        folder_id = data.folder_id

    today, day_start = logical_now(db)
    todo = Todo(
        text=data.text,
        folder_id=folder_id,
        important=data.important,
        recurrence=data.recurrence,
        recurrence_anchor=today if data.recurrence != Recurrence.NONE else None,
        due_type=data.due_type,
        due_date=data.due_date,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return to_read(todo, today, day_start)


@router.patch("/{todo_id}", response_model=schemas.TodoRead)
def update_todo(todo_id: int, data: schemas.TodoUpdate, db: Session = Depends(get_db)):
    """Bearbeiten. Ändert sich `recurrence`, wird der Anker auf heute gesetzt."""
    todo = get_todo_or_404(db, todo_id)
    changes = data.model_dump(exclude_unset=True)

    # Diese Felder dürfen nicht explizit null sein (Deadline entfernen ist dagegen erlaubt)
    for field in ("text", "folder_id", "important", "recurrence"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} must not be null",
            )

    if "folder_id" in changes:
        require_folder(db, changes["folder_id"])

    # Deadline-Regeln gegen den Zustand NACH der Änderung prüfen
    new_recurrence = changes.get("recurrence", todo.recurrence)
    new_due_type = changes.get("due_type", todo.due_type)
    new_due_date = changes.get("due_date", todo.due_date)
    if (new_due_type is None) != (new_due_date is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="due_type and due_date must both be set or both be empty",
        )
    if new_recurrence != Recurrence.NONE and new_due_type is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recurring todos cannot have a deadline in v1",
        )
    if new_due_type == DueType.FIXED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="due_type 'fixed' is not supported in v1",
        )

    today, day_start = logical_now(db)
    if "recurrence" in changes and changes["recurrence"] != todo.recurrence:
        todo.recurrence_anchor = today if new_recurrence != Recurrence.NONE else None

    for field, value in changes.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    return to_read(todo, today, day_start)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Löschen (die App fragt vorher nach)."""
    todo = get_todo_or_404(db, todo_id)
    db.delete(todo)
    db.commit()


# ---------- Abhaken ----------

@router.post("/{todo_id}/complete", response_model=schemas.TodoRead)
def complete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Abhaken: `completed_at = now`."""
    todo = get_todo_or_404(db, todo_id)
    todo.completed_at = datetime.now(timezone.utc)
    today, day_start = logical_now(db)
    db.commit()
    db.refresh(todo)
    return to_read(todo, today, day_start)


@router.post("/{todo_id}/uncomplete", response_model=schemas.TodoRead)
def uncomplete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Haken entfernen: `completed_at = null`."""
    todo = get_todo_or_404(db, todo_id)
    todo.completed_at = None
    today, day_start = logical_now(db)
    db.commit()
    db.refresh(todo)
    return to_read(todo, today, day_start)