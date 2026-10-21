from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app import schemas
from app.models import ServerSettings, Todo
from app.recurrence import is_done as _is_done


def logical_now(db: Session) -> tuple[date, datetime]:
    """Heutiger logischer Tag und dessen Beginn (reset_hour, Ortszeit)."""
    settings = db.get(ServerSettings, 1)
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    today = (now - timedelta(hours=settings.reset_hour)).date()
    day_start = datetime.combine(today, time(settings.reset_hour), tzinfo=tz)
    return today, day_start


def to_read(todo: Todo, today: date, day_start: datetime) -> schemas.TodoRead:
    data = {name: getattr(todo, name) for name in schemas.TodoRead.model_fields if hasattr(todo, name)}
    data["is_done"] = _is_done(todo, today, day_start)
    data["days_until_due"] = (todo.due_date - today).days if todo.due_date else None
    return schemas.TodoRead(**data)