# app/recurrence.py
from datetime import date, datetime, timedelta

from app.enums import Recurrence


def period_start(recurrence: Recurrence, anchor: date, today: date) -> date:
    """Letzter Periodenbeginn <= heute, als Spec Abschnitt 2."""
    if recurrence == Recurrence.DAILY:
        return today

    if recurrence == Recurrence.WEEKLY:
        days_since_anchor = (today - anchor).days
        return today - timedelta(days=days_since_anchor % 7)

    if recurrence == Recurrence.MONTHLY:
        day = min(anchor.day, _days_in_month(today.year, today.month))
        candidate = today.replace(day=day)
        if candidate > today:
            prev_year, prev_month = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
            day = min(anchor.day, _days_in_month(prev_year, prev_month))
            candidate = date(prev_year, prev_month, day)
        return candidate

    raise ValueError(f"period_start not defined for {recurrence}")


def _days_in_month(year: int, month: int) -> int:
    next_month = date(year + (month == 12), month % 12 + 1, 1)
    return (next_month - timedelta(days=1)).day


def is_done(todo, today: date, day_start: datetime) -> bool:
    if todo.recurrence == Recurrence.NONE:
        return todo.completed_at is not None
    if todo.completed_at is None:
        return False
    start = period_start(todo.recurrence, todo.recurrence_anchor, today)
    start_dt = datetime.combine(start, day_start.timetz())
    return todo.completed_at >= start_dt