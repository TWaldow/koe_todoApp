from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app import models

BERLIN = ZoneInfo("Europe/Berlin")
RESET_HOUR = 4


# ---------- Helfer ----------

def heute() -> date:
    """Heutiger *logischer* Tag: vor 04:00 Ortszeit zählt noch der Vortag."""
    return (datetime.now(BERLIN) - timedelta(hours=RESET_HOUR)).date()


def ago(**kwargs) -> datetime:
    return datetime.now(timezone.utc) - timedelta(**kwargs)


def parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def make_todo(client, text="Test", **fields):
    return client.post("/todos", json={"text": text, **fields})


def make_folder(client, name="IT-Ideen", color="#FF8800"):
    return client.post("/folders", json={"name": name, "color": color})


def allgemein_id(client) -> int:
    return client.get("/folders").json()[0]["id"]


def set_db(db, todo_id, **fields):
    """Direkt in der DB setzen (Zeitreisen, Anker), ohne die API zu benutzen."""
    todo = db.get(models.Todo, todo_id)
    for key, value in fields.items():
        setattr(todo, key, value)
    db.commit()


def ids(response) -> list[int]:
    return [t["id"] for t in response.json()]


def urgent_todo(client, days, text="Dringend", **fields):
    payload = {
        "important": True,
        "due_type": "deadline",
        "due_date": (heute() + timedelta(days=days)).isoformat(),
        **fields,
    }
    return make_todo(client, text, **payload)


# ---------- Auth ----------

@pytest.mark.parametrize("method,path", [
    ("GET", "/todos?folder_id=1"),
    ("GET", "/todos?view=routine"),
    ("GET", "/todos/urgent"),
    ("POST", "/todos"),
    ("PATCH", "/todos/1"),
    ("DELETE", "/todos/1"),
    ("POST", "/todos/1/complete"),
    ("POST", "/todos/1/uncomplete"),
])
def test_requires_token(client, method, path):
    r = client.request(method, path, json={"text": "x"}, headers={"Authorization": ""})
    assert r.status_code == 401


def test_rejects_wrong_token(client):
    r = client.get("/todos/urgent", headers={"Authorization": "Bearer falsch"})
    assert r.status_code == 401


# ---------- POST /todos ----------

def test_create_minimal_returns_201_and_defaults(client):
    r = make_todo(client, "Milch kaufen")
    assert r.status_code == 201
    body = r.json()
    assert body["id"] is not None
    assert body["text"] == "Milch kaufen"
    assert body["folder_id"] == allgemein_id(client)
    assert body["important"] is False
    assert body["recurrence"] == "none"
    assert body["recurrence_anchor"] is None
    assert body["due_type"] is None
    assert body["due_date"] is None
    assert body["completed_at"] is None
    assert body["created_at"] is not None
    assert body["updated_at"] is not None
    assert body["is_done"] is False
    assert body["days_until_due"] is None


def test_create_in_given_folder(client):
    folder = make_folder(client).json()
    r = make_todo(client, folder_id=folder["id"])
    assert r.status_code == 201
    assert r.json()["folder_id"] == folder["id"]


def test_create_unknown_folder_is_rejected(client):
    assert make_todo(client, folder_id=9999).status_code in (404, 422)


def test_create_empty_text_returns_422(client):
    assert make_todo(client, text="").status_code == 422


def test_create_missing_text_returns_422(client):
    assert client.post("/todos", json={"important": True}).status_code == 422


def test_create_important(client):
    assert make_todo(client, important=True).json()["important"] is True


def test_create_invalid_recurrence_returns_422(client):
    assert make_todo(client, recurrence="yearly").status_code == 422


def test_create_invalid_due_type_returns_422(client):
    r = make_todo(client, due_type="irgendwann", due_date=heute().isoformat())
    assert r.status_code == 422


def test_create_invalid_date_returns_422(client):
    r = make_todo(client, due_type="deadline", due_date="morgen")
    assert r.status_code == 422


@pytest.mark.parametrize("recurrence", ["daily", "weekly", "monthly"])
def test_create_recurring_sets_anchor_to_today(client, recurrence):
    r = make_todo(client, recurrence=recurrence)
    assert r.status_code == 201
    assert r.json()["recurrence"] == recurrence
    assert r.json()["recurrence_anchor"] == heute().isoformat()


def test_create_once_has_no_anchor(client):
    assert make_todo(client, recurrence="none").json()["recurrence_anchor"] is None


def test_client_cannot_set_anchor(client):
    r = make_todo(client, recurrence="daily", recurrence_anchor="2020-01-01")
    assert r.status_code in (201, 422)
    if r.status_code == 201:
        assert r.json()["recurrence_anchor"] == heute().isoformat()


def test_client_cannot_set_completed_at(client):
    r = make_todo(client, completed_at=datetime.now(timezone.utc).isoformat())
    assert r.status_code in (201, 422)
    if r.status_code == 201:
        assert r.json()["completed_at"] is None
        assert r.json()["is_done"] is False


# ---------- POST /todos: Deadline-Regeln ----------

def test_create_with_deadline(client):
    due = heute() + timedelta(days=5)
    r = make_todo(client, due_type="deadline", due_date=due.isoformat())
    assert r.status_code == 201
    assert r.json()["due_type"] == "deadline"
    assert r.json()["due_date"] == due.isoformat()


def test_create_due_type_without_date_returns_422(client):
    assert make_todo(client, due_type="deadline").status_code == 422


def test_create_due_date_without_type_returns_422(client):
    assert make_todo(client, due_date=heute().isoformat()).status_code == 422


@pytest.mark.parametrize("recurrence", ["daily", "weekly", "monthly"])
def test_create_recurring_with_deadline_returns_422(client, recurrence):
    r = make_todo(client, recurrence=recurrence, due_type="deadline", due_date=heute().isoformat())
    assert r.status_code == 422


@pytest.mark.parametrize("offset,expected", [(3, 3), (1, 1), (0, 0), (-1, -1), (-10, -10)])
def test_days_until_due(client, offset, expected):
    due = heute() + timedelta(days=offset)
    r = make_todo(client, due_type="deadline", due_date=due.isoformat())
    assert r.json()["days_until_due"] == expected


# ---------- GET /todos?folder_id= ----------

def test_list_returns_only_todos_of_folder(client):
    folder = make_folder(client).json()
    in_folder = make_todo(client, "A", folder_id=folder["id"]).json()
    in_general = make_todo(client, "B").json()

    assert ids(client.get("/todos", params={"folder_id": folder["id"]})) == [in_folder["id"]]
    assert ids(client.get("/todos", params={"folder_id": allgemein_id(client)})) == [in_general["id"]]


def test_list_empty_folder_returns_empty_list(client):
    folder = make_folder(client).json()
    r = client.get("/todos", params={"folder_id": folder["id"]})
    assert r.status_code == 200
    assert r.json() == []


def test_list_contains_computed_fields(client):
    make_todo(client)
    todo = client.get("/todos", params={"folder_id": allgemein_id(client)}).json()[0]
    assert todo["is_done"] is False
    assert "days_until_due" in todo


def test_list_includes_recurring_todos_of_folder(client):
    todo = make_todo(client, recurrence="daily").json()
    r = client.get("/todos", params={"folder_id": allgemein_id(client)})
    assert todo["id"] in ids(r)


# ---------- Sichtbarkeit einmaliger Todos ----------

def test_once_open_todo_is_visible_and_not_done(client):
    todo = make_todo(client).json()
    items = client.get("/todos", params={"folder_id": allgemein_id(client)}).json()
    assert [(t["id"], t["is_done"]) for t in items] == [(todo["id"], False)]


def test_once_completed_today_stays_visible_as_done(client):
    todo = make_todo(client).json()
    client.post(f"/todos/{todo['id']}/complete")
    items = client.get("/todos", params={"folder_id": allgemein_id(client)}).json()
    assert [(t["id"], t["is_done"]) for t in items] == [(todo["id"], True)]


def test_once_completed_on_earlier_day_is_hidden_but_not_deleted(client, db):
    todo = make_todo(client).json()
    set_db(db, todo["id"], completed_at=ago(days=3))

    r = client.get("/todos", params={"folder_id": allgemein_id(client)})
    assert todo["id"] not in ids(r)
    assert db.get(models.Todo, todo["id"]) is not None  # ausgeblendet, nicht gelöscht


def test_uncompleting_hidden_todo_makes_it_visible_again(client, db):
    todo = make_todo(client).json()
    set_db(db, todo["id"], completed_at=ago(days=3))
    client.post(f"/todos/{todo['id']}/uncomplete")
    r = client.get("/todos", params={"folder_id": allgemein_id(client)})
    assert todo["id"] in ids(r)


# ---------- Erledigt-Logik wiederkehrender Todos ----------

@pytest.mark.parametrize("recurrence", ["daily", "weekly", "monthly"])
def test_recurring_completed_now_is_done(client, recurrence):
    todo = make_todo(client, recurrence=recurrence).json()
    r = client.post(f"/todos/{todo['id']}/complete")
    assert r.json()["is_done"] is True


@pytest.mark.parametrize("recurrence,days_ago", [("daily", 3), ("weekly", 10), ("monthly", 70)])
def test_recurring_completed_in_old_period_is_open_again(client, db, recurrence, days_ago):
    todo = make_todo(client, recurrence=recurrence).json()
    set_db(db, todo["id"], completed_at=ago(days=days_ago))

    items = client.get("/todos", params={"folder_id": allgemein_id(client)}).json()
    assert [(t["id"], t["is_done"]) for t in items] == [(todo["id"], False)]


@pytest.mark.parametrize("completed_days_ago,expected_done", [
    (1, True),   # nach Periodenbeginn (Anker vor 3 Tagen) -> erledigt
    (5, False),  # vor Periodenbeginn -> wieder offen
])
def test_weekly_period_starts_at_anchor_day(client, db, completed_days_ago, expected_done):
    todo = make_todo(client, recurrence="weekly").json()
    set_db(
        db,
        todo["id"],
        recurrence_anchor=heute() - timedelta(days=3),
        completed_at=ago(days=completed_days_ago),
    )

    items = client.get("/todos", params={"folder_id": allgemein_id(client)}).json()
    assert items[0]["is_done"] is expected_done


def test_recurring_done_stays_in_list(client):
    todo = make_todo(client, recurrence="daily").json()
    client.post(f"/todos/{todo['id']}/complete")
    r = client.get("/todos", params={"folder_id": allgemein_id(client)})
    assert todo["id"] in ids(r)


# ---------- GET /todos?view=routine ----------

def test_routine_view_returns_all_recurring_across_folders(client):
    folder = make_folder(client).json()
    daily = make_todo(client, "A", recurrence="daily").json()
    weekly = make_todo(client, "B", recurrence="weekly", folder_id=folder["id"]).json()
    monthly = make_todo(client, "C", recurrence="monthly", folder_id=folder["id"]).json()
    make_todo(client, "Einmalig")
    make_todo(client, "Einmalig im Ordner", folder_id=folder["id"])

    r = client.get("/todos", params={"view": "routine"})
    assert r.status_code == 200
    assert set(ids(r)) == {daily["id"], weekly["id"], monthly["id"]}


def test_routine_view_empty_without_recurring(client):
    make_todo(client)
    r = client.get("/todos", params={"view": "routine"})
    assert r.status_code == 200
    assert r.json() == []


def test_routine_view_includes_done_recurring(client):
    todo = make_todo(client, recurrence="daily").json()
    client.post(f"/todos/{todo['id']}/complete")
    r = client.get("/todos", params={"view": "routine"})
    assert [(t["id"], t["is_done"]) for t in r.json()] == [(todo["id"], True)]


def test_routine_view_invalid_value_returns_422(client):
    assert client.get("/todos", params={"view": "quatsch"}).status_code == 422


# ---------- GET /todos/urgent ----------

def test_urgent_contains_matching_todo(client):
    todo = urgent_todo(client, days=2).json()
    r = client.get("/todos/urgent")
    assert r.status_code == 200
    assert ids(r) == [todo["id"]]
    assert r.json()[0]["days_until_due"] == 2


def test_urgent_empty_by_default(client):
    make_todo(client)
    r = client.get("/todos/urgent")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.parametrize("days", [2, 1, 0, -1, -30])
def test_urgent_includes_due_within_two_days_and_overdue(client, days):
    todo = urgent_todo(client, days=days).json()
    assert todo["id"] in ids(client.get("/todos/urgent"))


def test_urgent_excludes_due_in_three_days(client):
    todo = urgent_todo(client, days=3).json()
    assert todo["id"] not in ids(client.get("/todos/urgent"))


def test_urgent_excludes_not_important(client):
    todo = urgent_todo(client, days=1, important=False).json()
    assert todo["id"] not in ids(client.get("/todos/urgent"))


def test_urgent_excludes_without_deadline(client):
    todo = make_todo(client, important=True).json()
    assert todo["id"] not in ids(client.get("/todos/urgent"))


def test_urgent_excludes_completed(client):
    todo = urgent_todo(client, days=1).json()
    client.post(f"/todos/{todo['id']}/complete")
    assert todo["id"] not in ids(client.get("/todos/urgent"))


def test_urgent_excludes_recurring(client):
    todo = make_todo(client, important=True, recurrence="daily").json()
    assert todo["id"] not in ids(client.get("/todos/urgent"))


def test_urgent_spans_all_folders(client):
    folder = make_folder(client).json()
    a = urgent_todo(client, days=1).json()
    b = urgent_todo(client, days=1, folder_id=folder["id"]).json()
    assert set(ids(client.get("/todos/urgent"))) == {a["id"], b["id"]}


def test_urgent_sorted_by_due_date_most_overdue_first(client):
    soon = urgent_todo(client, days=2, text="bald").json()
    overdue = urgent_todo(client, days=-5, text="überfällig").json()
    today = urgent_todo(client, days=0, text="heute").json()

    r = client.get("/todos/urgent")
    assert ids(r) == [overdue["id"], today["id"], soon["id"]]


def test_urgent_reappears_after_uncomplete(client):
    todo = urgent_todo(client, days=1).json()
    client.post(f"/todos/{todo['id']}/complete")
    client.post(f"/todos/{todo['id']}/uncomplete")
    assert todo["id"] in ids(client.get("/todos/urgent"))


# ---------- PATCH /todos/{id} ----------

def test_patch_changes_only_sent_fields(client):
    todo = make_todo(client, "Alt", important=True).json()
    r = client.patch(f"/todos/{todo['id']}", json={"text": "Neu"})
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "Neu"
    assert body["important"] is True  # unverändert
    assert body["folder_id"] == todo["folder_id"]
    assert body["recurrence"] == "none"


def test_patch_important_toggle(client):
    todo = make_todo(client).json()
    r = client.patch(f"/todos/{todo['id']}", json={"important": True})
    assert r.json()["important"] is True
    r = client.patch(f"/todos/{todo['id']}", json={"important": False})
    assert r.json()["important"] is False


def test_patch_unknown_id_returns_404(client):
    assert client.patch("/todos/9999", json={"text": "X"}).status_code == 404


def test_patch_empty_text_returns_422(client):
    todo = make_todo(client).json()
    assert client.patch(f"/todos/{todo['id']}", json={"text": ""}).status_code == 422


def test_patch_invalid_recurrence_returns_422(client):
    todo = make_todo(client).json()
    assert client.patch(f"/todos/{todo['id']}", json={"recurrence": "yearly"}).status_code == 422


def test_patch_updates_updated_at_not_created_at(client):
    todo = make_todo(client).json()
    r = client.patch(f"/todos/{todo['id']}", json={"text": "Neu"}).json()
    assert r["created_at"] == todo["created_at"]
    assert parse_dt(r["updated_at"]) > parse_dt(todo["updated_at"])


def test_patch_persists(client):
    todo = make_todo(client).json()
    client.patch(f"/todos/{todo['id']}", json={"text": "Neu"})
    items = client.get("/todos", params={"folder_id": todo["folder_id"]}).json()
    assert items[0]["text"] == "Neu"


def test_patch_move_to_other_folder(client):
    folder = make_folder(client).json()
    todo = make_todo(client).json()
    r = client.patch(f"/todos/{todo['id']}", json={"folder_id": folder["id"]})
    assert r.status_code == 200
    assert r.json()["folder_id"] == folder["id"]
    assert todo["id"] in ids(client.get("/todos", params={"folder_id": folder["id"]}))
    assert todo["id"] not in ids(client.get("/todos", params={"folder_id": allgemein_id(client)}))


def test_patch_unknown_folder_is_rejected(client):
    todo = make_todo(client).json()
    r = client.patch(f"/todos/{todo['id']}", json={"folder_id": 9999})
    assert r.status_code in (404, 422)


# ---------- PATCH: Deadline-Regeln ----------

def test_patch_add_deadline(client):
    todo = make_todo(client).json()
    due = heute() + timedelta(days=4)
    r = client.patch(f"/todos/{todo['id']}", json={"due_type": "deadline", "due_date": due.isoformat()})
    assert r.status_code == 200
    assert r.json()["due_type"] == "deadline"
    assert r.json()["due_date"] == due.isoformat()
    assert r.json()["days_until_due"] == 4


def test_patch_remove_deadline_with_explicit_null(client):
    todo = urgent_todo(client, days=1).json()
    r = client.patch(f"/todos/{todo['id']}", json={"due_type": None, "due_date": None})
    assert r.status_code == 200
    assert r.json()["due_type"] is None
    assert r.json()["due_date"] is None
    assert r.json()["days_until_due"] is None


def test_patch_change_only_due_date_keeps_due_type(client):
    todo = urgent_todo(client, days=1).json()
    new_due = heute() + timedelta(days=7)
    r = client.patch(f"/todos/{todo['id']}", json={"due_date": new_due.isoformat()})
    assert r.status_code == 200
    assert r.json()["due_type"] == "deadline"
    assert r.json()["due_date"] == new_due.isoformat()


def test_patch_only_due_date_without_existing_deadline_returns_422(client):
    todo = make_todo(client).json()
    r = client.patch(f"/todos/{todo['id']}", json={"due_date": heute().isoformat()})
    assert r.status_code == 422


def test_patch_only_due_type_without_existing_deadline_returns_422(client):
    todo = make_todo(client).json()
    assert client.patch(f"/todos/{todo['id']}", json={"due_type": "deadline"}).status_code == 422


def test_patch_remove_only_due_date_returns_422(client):
    todo = urgent_todo(client, days=1).json()
    assert client.patch(f"/todos/{todo['id']}", json={"due_date": None}).status_code == 422


def test_patch_remove_only_due_type_returns_422(client):
    todo = urgent_todo(client, days=1).json()
    assert client.patch(f"/todos/{todo['id']}", json={"due_type": None}).status_code == 422


def test_patch_deadline_on_recurring_returns_422(client):
    todo = make_todo(client, recurrence="daily").json()
    r = client.patch(
        f"/todos/{todo['id']}",
        json={"due_type": "deadline", "due_date": heute().isoformat()},
    )
    assert r.status_code == 422


def test_patch_recurrence_on_todo_with_deadline_returns_422(client):
    todo = urgent_todo(client, days=1).json()
    assert client.patch(f"/todos/{todo['id']}", json={"recurrence": "daily"}).status_code == 422


def test_patch_recurrence_and_deadline_together_returns_422(client):
    todo = make_todo(client).json()
    r = client.patch(
        f"/todos/{todo['id']}",
        json={"recurrence": "weekly", "due_type": "deadline", "due_date": heute().isoformat()},
    )
    assert r.status_code == 422


def test_patch_recurrence_and_remove_deadline_together_is_valid(client):
    todo = urgent_todo(client, days=1).json()
    r = client.patch(
        f"/todos/{todo['id']}",
        json={"recurrence": "daily", "due_type": None, "due_date": None},
    )
    assert r.status_code == 200
    assert r.json()["recurrence"] == "daily"
    assert r.json()["due_date"] is None


def test_patch_recurrence_none_and_add_deadline_together_is_valid(client):
    todo = make_todo(client, recurrence="daily").json()
    due = heute() + timedelta(days=2)
    r = client.patch(
        f"/todos/{todo['id']}",
        json={"recurrence": "none", "due_type": "deadline", "due_date": due.isoformat()},
    )
    assert r.status_code == 200
    assert r.json()["recurrence"] == "none"
    assert r.json()["due_date"] == due.isoformat()


# ---------- PATCH: Anker ----------

def test_patch_recurrence_from_none_sets_anchor_today(client):
    todo = make_todo(client).json()
    r = client.patch(f"/todos/{todo['id']}", json={"recurrence": "daily"})
    assert r.status_code == 200
    assert r.json()["recurrence"] == "daily"
    assert r.json()["recurrence_anchor"] == heute().isoformat()


def test_patch_recurrence_change_resets_anchor_to_today(client, db):
    todo = make_todo(client, recurrence="daily").json()
    set_db(db, todo["id"], recurrence_anchor=heute() - timedelta(days=10))

    r = client.patch(f"/todos/{todo['id']}", json={"recurrence": "weekly"})
    assert r.json()["recurrence"] == "weekly"
    assert r.json()["recurrence_anchor"] == heute().isoformat()


def test_patch_other_field_keeps_anchor(client, db):
    todo = make_todo(client, recurrence="weekly").json()
    old_anchor = heute() - timedelta(days=10)
    set_db(db, todo["id"], recurrence_anchor=old_anchor)

    r = client.patch(f"/todos/{todo['id']}", json={"text": "Neu"})
    assert r.json()["recurrence_anchor"] == old_anchor.isoformat()


def test_patch_same_recurrence_keeps_anchor(client, db):
    todo = make_todo(client, recurrence="weekly").json()
    old_anchor = heute() - timedelta(days=10)
    set_db(db, todo["id"], recurrence_anchor=old_anchor)

    r = client.patch(f"/todos/{todo['id']}", json={"recurrence": "weekly"})
    assert r.json()["recurrence_anchor"] == old_anchor.isoformat()


# ---------- DELETE /todos/{id} ----------

def test_delete_returns_204_and_removes_todo(client, db):
    todo = make_todo(client).json()
    assert client.delete(f"/todos/{todo['id']}").status_code == 204
    r = client.get("/todos", params={"folder_id": todo["folder_id"]})
    assert todo["id"] not in ids(r)
    assert db.get(models.Todo, todo["id"]) is None


def test_delete_unknown_id_returns_404(client):
    assert client.delete("/todos/9999").status_code == 404


def test_delete_twice_returns_404(client):
    todo = make_todo(client).json()
    client.delete(f"/todos/{todo['id']}")
    assert client.delete(f"/todos/{todo['id']}").status_code == 404


def test_delete_leaves_other_todos(client):
    a = make_todo(client, "A").json()
    b = make_todo(client, "B").json()
    client.delete(f"/todos/{a['id']}")
    assert ids(client.get("/todos", params={"folder_id": allgemein_id(client)})) == [b["id"]]


def test_delete_completed_todo(client):
    todo = make_todo(client).json()
    client.post(f"/todos/{todo['id']}/complete")
    assert client.delete(f"/todos/{todo['id']}").status_code == 204


# ---------- POST /todos/{id}/complete ----------

def test_complete_sets_completed_at_and_is_done(client):
    todo = make_todo(client).json()
    r = client.post(f"/todos/{todo['id']}/complete")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == todo["id"]
    assert body["is_done"] is True
    assert abs(datetime.now(timezone.utc) - parse_dt(body["completed_at"])) < timedelta(seconds=10)


def test_complete_unknown_id_returns_404(client):
    assert client.post("/todos/9999/complete").status_code == 404


def test_complete_twice_is_still_done(client):
    todo = make_todo(client).json()
    client.post(f"/todos/{todo['id']}/complete")
    r = client.post(f"/todos/{todo['id']}/complete")
    assert r.status_code == 200
    assert r.json()["is_done"] is True


def test_complete_persists(client):
    todo = make_todo(client).json()
    client.post(f"/todos/{todo['id']}/complete")
    items = client.get("/todos", params={"folder_id": todo["folder_id"]}).json()
    assert items[0]["is_done"] is True
    assert items[0]["completed_at"] is not None


def test_complete_does_not_change_other_fields(client):
    todo = urgent_todo(client, days=1, text="Behalten").json()
    body = client.post(f"/todos/{todo['id']}/complete").json()
    for field in ("text", "folder_id", "important", "recurrence", "due_type", "due_date"):
        assert body[field] == todo[field]


# ---------- POST /todos/{id}/uncomplete ----------

def test_uncomplete_clears_completed_at(client):
    todo = make_todo(client).json()
    client.post(f"/todos/{todo['id']}/complete")
    r = client.post(f"/todos/{todo['id']}/uncomplete")
    assert r.status_code == 200
    assert r.json()["completed_at"] is None
    assert r.json()["is_done"] is False


def test_uncomplete_recurring(client):
    todo = make_todo(client, recurrence="daily").json()
    client.post(f"/todos/{todo['id']}/complete")
    r = client.post(f"/todos/{todo['id']}/uncomplete")
    assert r.json()["is_done"] is False
    assert r.json()["completed_at"] is None


def test_uncomplete_not_completed_is_idempotent(client):
    todo = make_todo(client).json()
    r = client.post(f"/todos/{todo['id']}/uncomplete")
    assert r.status_code == 200
    assert r.json()["is_done"] is False


def test_uncomplete_unknown_id_returns_404(client):
    assert client.post("/todos/9999/uncomplete").status_code == 404


def test_uncomplete_persists(client):
    todo = make_todo(client).json()
    client.post(f"/todos/{todo['id']}/complete")
    client.post(f"/todos/{todo['id']}/uncomplete")
    items = client.get("/todos", params={"folder_id": todo["folder_id"]}).json()
    assert items[0]["is_done"] is False