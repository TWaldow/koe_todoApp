from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app import claude_client, models

BERLIN = ZoneInfo("Europe/Berlin")
RESET_HOUR = 4


# ---------- Helfer ----------

def heute() -> date:
    """Heutiger *logischer* Tag: vor 04:00 Ortszeit zählt noch der Vortag."""
    return (datetime.now(BERLIN) - timedelta(hours=RESET_HOUR)).date()


class FakeHaiku:
    """Ersetzt `claude_client.parse_transcript`. Steuert, was Haiku 'zurückgegeben hätte'."""

    def __init__(self):
        self.result = None  # None = nicht konfiguriert -> Test schlägt laut fehl
        self.calls = []

    def returns(self, *todos):
        self.result = list(todos)

    def __call__(self, text, today_iso, weekday, folder_names, current_folder):
        self.calls.append(
            {
                "text": text,
                "today_iso": today_iso,
                "weekday": weekday,
                "folder_names": folder_names,
                "current_folder": current_folder,
            }
        )
        if self.result is None:
            raise AssertionError("parse_transcript wurde aufgerufen, ist im Test aber nicht konfiguriert")
        return self.result


@pytest.fixture(autouse=True)
def haiku(monkeypatch):
    """Autouse: kein Test in dieser Datei kann versehentlich die echte Anthropic-API erreichen."""
    fake = FakeHaiku()
    monkeypatch.setattr(claude_client, "parse_transcript", fake)
    return fake


def haiku_todo(text="Test", folder="", important=False, recurrence="none", due_type=None, due_date=None):
    return {
        "text": text,
        "folder": folder,
        "important": important,
        "recurrence": recurrence,
        "due_type": due_type,
        "due_date": due_date,
    }


def post_voice(client, text="Irgendwas sagen", **extra):
    return client.post("/voice-todos", json={"text": text, **extra})


def ok(response) -> dict:
    assert response.status_code in (200, 201), response.text
    return response.json()


def make_folder(client, name="IT-Ideen", color="#FF8800"):
    return client.post("/folders", json={"name": name, "color": color})


def allgemein_id(client) -> int:
    return client.get("/folders").json()[0]["id"]


def todos_in(client, folder_id):
    return client.get("/todos", params={"folder_id": folder_id}).json()


# ---------- Auth ----------

def test_requires_token(client, haiku):
    r = client.post("/voice-todos", json={"text": "x"}, headers={"Authorization": ""})
    assert r.status_code == 401
    assert haiku.calls == []


def test_rejects_wrong_token(client, haiku):
    r = client.post("/voice-todos", json={"text": "x"}, headers={"Authorization": "Bearer falsch"})
    assert r.status_code == 401
    assert haiku.calls == []


# ---------- Request-Validierung ----------

def test_empty_text_returns_422(client, haiku):
    assert post_voice(client, text="").status_code == 422
    assert haiku.calls == []


def test_missing_text_returns_422(client, haiku):
    assert client.post("/voice-todos", json={"folder_id": None}).status_code == 422
    assert haiku.calls == []


def test_empty_body_returns_422(client, haiku):
    assert client.post("/voice-todos", json={}).status_code == 422
    assert haiku.calls == []


def test_invalid_folder_id_type_returns_422(client, haiku):
    assert post_voice(client, folder_id="abc").status_code == 422
    assert haiku.calls == []


def test_unknown_folder_id_is_rejected(client, haiku):
    assert post_voice(client, folder_id=9999).status_code in (404, 422)
    assert haiku.calls == []


def test_optional_fields_may_be_null_or_omitted(client, haiku):
    haiku.returns()
    assert post_voice(client).status_code in (200, 201)
    assert post_voice(client, folder_id=None, answer=None).status_code in (200, 201)


# ---------- Normalfall ----------

def test_single_todo_is_created(client, haiku):
    haiku.returns(haiku_todo("Milch kaufen"))

    body = ok(post_voice(client, "Ich muss Milch kaufen"))

    assert len(body["created"]) == 1
    assert body["skipped"] == []
    assert body["question"] is None
    todo = body["created"][0]
    assert todo["id"] is not None
    assert todo["text"] == "Milch kaufen"
    assert todo["folder_id"] == allgemein_id(client)
    assert todo["important"] is False
    assert todo["recurrence"] == "none"
    assert todo["recurrence_anchor"] is None
    assert todo["due_type"] is None
    assert todo["due_date"] is None
    assert todo["completed_at"] is None
    assert todo["is_done"] is False


def test_created_todo_is_persisted(client, haiku):
    haiku.returns(haiku_todo("Milch kaufen"))
    created = ok(post_voice(client))["created"][0]

    items = todos_in(client, allgemein_id(client))
    assert [(t["id"], t["text"]) for t in items] == [(created["id"], "Milch kaufen")]


def test_transcript_is_passed_to_haiku(client, haiku):
    haiku.returns()
    post_voice(client, "Ich muss Milch kaufen")
    assert len(haiku.calls) == 1
    assert haiku.calls[0]["text"] == "Ich muss Milch kaufen"


def test_haiku_gets_today_weekday_and_folders(client, haiku):
    make_folder(client, "IT-Ideen")
    haiku.returns()

    post_voice(client, "bis Freitag Steuern machen")

    call = haiku.calls[0]
    assert call["today_iso"] == heute().isoformat()
    assert call["weekday"]  # Wochentag ist nötig, damit "bis Freitag" auflösbar ist
    assert set(call["folder_names"]) >= {"Allgemein", "IT-Ideen"}


def test_haiku_gets_current_folder(client, haiku):
    folder = make_folder(client, "IT-Ideen").json()
    haiku.returns()

    post_voice(client, "irgendwas", folder_id=folder["id"])

    assert haiku.calls[0]["current_folder"] == "IT-Ideen"


def test_important_flag_is_taken_over(client, haiku):
    haiku.returns(haiku_todo("Steuererklärung", important=True))
    assert ok(post_voice(client))["created"][0]["important"] is True


def test_deadline_is_taken_over(client, haiku):
    due = heute() + timedelta(days=3)
    haiku.returns(haiku_todo("Steuern", due_type="deadline", due_date=due.isoformat()))

    todo = ok(post_voice(client))["created"][0]

    assert todo["due_type"] == "deadline"
    assert todo["due_date"] == due.isoformat()
    assert todo["days_until_due"] == 3


# ---------- Mehrere Todos ----------

def test_multiple_todos_from_one_transcript(client, haiku):
    haiku.returns(
        haiku_todo("Milch kaufen"),
        haiku_todo("Wäsche waschen", important=True),
        haiku_todo("Mama anrufen"),
    )

    body = ok(post_voice(client, "Milch kaufen, Wäsche waschen und Mama anrufen"))

    assert [t["text"] for t in body["created"]] == ["Milch kaufen", "Wäsche waschen", "Mama anrufen"]
    assert len({t["id"] for t in body["created"]}) == 3
    assert body["skipped"] == []
    assert len(todos_in(client, allgemein_id(client))) == 3


def test_multiple_todos_in_different_folders(client, haiku):
    folder = make_folder(client, "IT-Ideen").json()
    haiku.returns(
        haiku_todo("Docker lernen", folder="IT-Ideen"),
        haiku_todo("Milch kaufen", folder="Allgemein"),
    )

    body = ok(post_voice(client))

    by_text = {t["text"]: t["folder_id"] for t in body["created"]}
    assert by_text == {"Docker lernen": folder["id"], "Milch kaufen": allgemein_id(client)}


# ---------- Ordnerzuordnung ----------

def test_known_folder_name_assigns_todo_to_folder(client, haiku):
    folder = make_folder(client, "IT-Ideen").json()
    haiku.returns(haiku_todo("Docker lernen", folder="IT-Ideen"))

    todo = ok(post_voice(client))["created"][0]

    assert todo["folder_id"] == folder["id"]
    assert [t["id"] for t in todos_in(client, folder["id"])] == [todo["id"]]
    assert todos_in(client, allgemein_id(client)) == []


def test_unknown_folder_name_falls_back_to_allgemein(client, haiku):
    haiku.returns(haiku_todo("Irgendwas", folder="Gibt es nicht"))

    body = ok(post_voice(client))

    assert body["created"][0]["folder_id"] == allgemein_id(client)
    assert body["skipped"] == []


def test_empty_folder_name_falls_back_to_allgemein(client, haiku):
    haiku.returns(haiku_todo("Irgendwas", folder=""))
    assert ok(post_voice(client))["created"][0]["folder_id"] == allgemein_id(client)


def test_unknown_folder_name_does_not_create_folder(client, haiku):
    haiku.returns(haiku_todo("Irgendwas", folder="Gibt es nicht"))
    ok(post_voice(client))
    assert [f["name"] for f in client.get("/folders").json()] == ["Allgemein"]


# ---------- Termine (fixed) ----------

def test_fixed_goes_to_skipped_and_is_not_created(client, haiku, db):
    haiku.returns(
        haiku_todo(
            "Zahnarzt Dienstag 10 Uhr",
            due_type="fixed",
            due_date=(heute() + timedelta(days=2)).isoformat(),
        )
    )

    body = ok(post_voice(client, "Zahnarzt Dienstag 10 Uhr"))

    assert body["created"] == []
    assert body["skipped"] == [{"text": "Zahnarzt Dienstag 10 Uhr", "reason": "fixed_not_supported"}]
    assert body["question"] is None
    assert db.query(models.Todo).count() == 0  # nicht still gespeichert


def test_fixed_is_not_silently_dropped(client, haiku):
    haiku.returns(haiku_todo("Meeting", due_type="fixed", due_date=heute().isoformat()))
    assert len(ok(post_voice(client))["skipped"]) == 1


def test_mixed_normal_and_fixed(client, haiku, db):
    haiku.returns(
        haiku_todo("Milch kaufen"),
        haiku_todo("Zahnarzt", due_type="fixed", due_date=heute().isoformat()),
        haiku_todo("Wäsche waschen"),
    )

    body = ok(post_voice(client))

    assert [t["text"] for t in body["created"]] == ["Milch kaufen", "Wäsche waschen"]
    assert [(s["text"], s["reason"]) for s in body["skipped"]] == [("Zahnarzt", "fixed_not_supported")]
    assert [t.text for t in db.query(models.Todo).order_by(models.Todo.id)] == ["Milch kaufen", "Wäsche waschen"]


def test_multiple_fixed_are_all_skipped(client, haiku):
    haiku.returns(
        haiku_todo("Zahnarzt", due_type="fixed", due_date=heute().isoformat()),
        haiku_todo("Friseur", due_type="fixed", due_date=heute().isoformat()),
    )

    body = ok(post_voice(client))

    assert body["created"] == []
    assert [s["text"] for s in body["skipped"]] == ["Zahnarzt", "Friseur"]
    assert {s["reason"] for s in body["skipped"]} == {"fixed_not_supported"}


# ---------- Leeres Ergebnis ----------

def test_empty_haiku_result_returns_empty_lists(client, haiku, db):
    haiku.returns()  # []

    r = post_voice(client, "ähm, naja")

    body = ok(r)
    assert body["created"] == []
    assert body["skipped"] == []
    assert body["question"] is None
    assert db.query(models.Todo).count() == 0


# ---------- Wiederkehrende Todos ----------

@pytest.mark.parametrize("recurrence", ["daily", "weekly", "monthly"])
def test_recurring_todo_gets_anchor_today(client, haiku, recurrence):
    haiku.returns(haiku_todo("Pflanzen gießen", recurrence=recurrence))

    todo = ok(post_voice(client))["created"][0]

    assert todo["recurrence"] == recurrence
    assert todo["recurrence_anchor"] == heute().isoformat()
    assert todo["is_done"] is False


def test_recurring_todo_appears_in_routine_view(client, haiku):
    haiku.returns(haiku_todo("Pflanzen gießen", recurrence="weekly"), haiku_todo("Einmalig"))

    created = ok(post_voice(client))["created"]

    routine = client.get("/todos", params={"view": "routine"}).json()
    assert [t["id"] for t in routine] == [created[0]["id"]]


def test_non_recurring_todo_has_no_anchor(client, haiku):
    haiku.returns(haiku_todo("Einmalig", recurrence="none"))
    assert ok(post_voice(client))["created"][0]["recurrence_anchor"] is None