from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums import DueType, Recurrence

HexColor = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]


# ---------- Folder ----------


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: HexColor = "#4169E1"


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: HexColor | None = None
    position: int | None = None


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    is_system: bool
    position: int
    created_at: datetime


# ---------- Todo ----------


class TodoCreate(BaseModel):
    text: str = Field(min_length=1)
    folder_id: int | None = None  # None -> Ordner "Allgemein" (setzt der Router)
    important: bool = False
    recurrence: Recurrence = Recurrence.NONE
    due_type: DueType | None = None
    due_date: date | None = None
    # recurrence_anchor kommt nicht vom Client, der Server setzt ihn auf heute.

    @model_validator(mode="after")
    def check_due_rules(self):
        if (self.due_type is None) != (self.due_date is None):
            raise ValueError("due_type und due_date müssen beide gesetzt oder beide leer sein")
        if self.recurrence != Recurrence.none and self.due_type is not None:
            raise ValueError("Wiederkehrende Todos haben in v1 keine Deadline")
        return self


class TodoUpdate(BaseModel):
    """PATCH: nur gesendete Felder ändern.

    Im Router mit `model_dump(exclude_unset=True)` auslesen, damit "nicht gesendet"
    und "explizit null" (z. B. Deadline entfernen) unterscheidbar bleiben.
    Die Deadline-Regeln müssen dort gegen den bestehenden Datensatz geprüft
    werden, weil hier nur die gesendeten Felder vorliegen.
    """

    text: str | None = Field(default=None, min_length=1)
    folder_id: int | None = None
    important: bool | None = None
    recurrence: Recurrence | None = None
    due_type: DueType | None = None
    due_date: date | None = None


class TodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    folder_id: int
    important: bool
    recurrence: Recurrence
    recurrence_anchor: date | None
    due_type: DueType | None
    due_date: date | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # Berechnete Felder: stehen nicht in der DB, werden beim Lesen ergänzt
    # (Logik kommt später nach recurrence.py).
    is_done: bool
    days_until_due: int | None


# ---------- Voice ----------


class VoiceRequest(BaseModel):
    text: str = Field(min_length=1)
    folder_id: int | None = None
    answer: str | None = None  # Antwort auf eine Rückfrage von Haiku


class SkippedItem(BaseModel):
    text: str
    reason: str  # z. B. "fixed_not_supported"


class VoiceResponse(BaseModel):
    created: list[TodoRead]
    skipped: list[SkippedItem]
    question: str | None = None  # gesetzt -> nichts wurde gespeichert


# ---------- Settings ----------


class SettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timezone: str
    reset_hour: int


class SettingsUpdate(BaseModel):
    timezone: str | None = None
    reset_hour: int | None = Field(default=None, ge=0, le=23)

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                ZoneInfo(v)
            except Exception:
                raise ValueError(f"Unbekannte Zeitzone: {v}")
        return v