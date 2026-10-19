from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base
from app.enums import DueType, Recurrence


class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str] = mapped_column(String(7), default="#4169E1")
    is_system: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    todos: Mapped[list["Todo"]] = relationship(back_populates="folder")

    __table_args__ = (
        CheckConstraint("name <> ''", name="folder_name_not_empty"),
        CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="folder_color_hex"),
    )


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    folder_id: Mapped[int] = mapped_column(ForeignKey("folders.id"))
    important: Mapped[bool] = mapped_column(default=False)
    recurrence: Mapped[Recurrence] = mapped_column(
        SAEnum(Recurrence, name="recurrence"), default=Recurrence.none
    )
    recurrence_anchor: Mapped[date | None]
    due_type: Mapped[DueType | None] = mapped_column(SAEnum(DueType, name="due_type"))
    due_date: Mapped[date | None]
    due_time: Mapped[time | None]  # erst mit Kalender-Feature
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    folder: Mapped[Folder] = relationship(back_populates="todos")

    __table_args__ = (
        CheckConstraint("text <> ''", name="todo_text_not_empty"),
        # due_type und due_date: beide gesetzt oder beide null
        CheckConstraint("(due_type IS NULL) = (due_date IS NULL)", name="todo_due_both_or_none"),
        # wiederkehrend braucht einen Anker
        CheckConstraint(
            "recurrence = 'none' OR recurrence_anchor IS NOT NULL",
            name="todo_recurrence_needs_anchor",
        ),
        # wiederkehrende Todos haben in v1 keine Deadline
        CheckConstraint(
            "recurrence = 'none' OR due_type IS NULL",
            name="todo_recurring_no_deadline",
        ),
    )


class ServerSettings(Base):
    """Genau eine Zeile (id = 1). Die Logik braucht Zeitzone und Reset-Stunde."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Berlin")
    reset_hour: Mapped[int] = mapped_column(default=4)

    __table_args__ = (
        CheckConstraint("id = 1", name="settings_single_row"),
        CheckConstraint("reset_hour BETWEEN 0 AND 23", name="settings_reset_hour_range"),
    )