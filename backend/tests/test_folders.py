from app import models


def make_folder(client, name="IT-Ideen", color="#FF8800"):
    return client.post("/folders", json={"name": name, "color": color})


# ---------- Auth ----------

def test_requires_token(client):
    r = client.get("/folders", headers={"Authorization": ""})
    assert r.status_code == 401


def test_rejects_wrong_token(client):
    r = client.get("/folders", headers={"Authorization": "Bearer falsch"})
    assert r.status_code == 401


# ---------- GET ----------

def test_list_contains_system_folder(client):
    r = client.get("/folders")
    assert r.status_code == 200
    assert [f["name"] for f in r.json()] == ["Allgemein"]


def test_list_sorted_by_position(client):
    make_folder(client, "B")
    make_folder(client, "A")
    names = [f["name"] for f in client.get("/folders").json()]
    assert names == ["Allgemein", "B", "A"]  # Reihenfolge der Anlage, nicht alphabetisch


# ---------- POST ----------

def test_create_returns_201_and_fields(client):
    r = make_folder(client)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "IT-Ideen"
    assert body["color"] == "#FF8800"
    assert body["is_system"] is False
    assert body["id"] is not None


def test_create_appends_position(client):
    first = make_folder(client, "A").json()
    second = make_folder(client, "B").json()
    assert first["position"] == 1  # Allgemein hat 0
    assert second["position"] == 2


def test_create_duplicate_name_returns_409(client):
    make_folder(client)
    assert make_folder(client).status_code == 409


def test_create_empty_name_returns_422(client):
    assert make_folder(client, name="").status_code == 422


def test_create_invalid_color_returns_422(client):
    assert make_folder(client, color="rot").status_code == 422


def test_create_missing_name_returns_422(client):
    assert client.post("/folders", json={"color": "#FF8800"}).status_code == 422


def test_user_cannot_create_system_folder(client):
    r = client.post("/folders", json={"name": "X", "color": "#FF8800", "is_system": True})
    assert r.status_code in (201, 422)
    if r.status_code == 201:
        assert r.json()["is_system"] is False


# ---------- PATCH ----------

def test_patch_changes_only_sent_fields(client):
    folder = make_folder(client).json()
    r = client.patch(f"/folders/{folder['id']}", json={"color": "#00FF00"})
    assert r.status_code == 200
    assert r.json()["color"] == "#00FF00"
    assert r.json()["name"] == "IT-Ideen"  # unverändert


def test_patch_rename(client):
    folder = make_folder(client).json()
    r = client.patch(f"/folders/{folder['id']}", json={"name": "Arbeit"})
    assert r.json()["name"] == "Arbeit"


def test_patch_unknown_id_returns_404(client):
    assert client.patch("/folders/9999", json={"name": "X"}).status_code == 404


def test_patch_duplicate_name_returns_409(client):
    make_folder(client, "A")
    b = make_folder(client, "B").json()
    assert client.patch(f"/folders/{b['id']}", json={"name": "A"}).status_code == 409


def test_patch_empty_name_returns_422(client):
    folder = make_folder(client).json()
    assert client.patch(f"/folders/{folder['id']}", json={"name": ""}).status_code == 422


# ---------- DELETE ----------

def test_delete_returns_204_and_removes_folder(client):
    folder = make_folder(client).json()
    assert client.delete(f"/folders/{folder['id']}").status_code == 204
    assert folder["id"] not in [f["id"] for f in client.get("/folders").json()]


def test_delete_unknown_id_returns_404(client):
    assert client.delete("/folders/9999").status_code == 404


def test_delete_system_folder_returns_409(client):
    allgemein = client.get("/folders").json()[0]
    assert client.delete(f"/folders/{allgemein['id']}").status_code == 409
    assert len(client.get("/folders").json()) == 1  # noch da


def test_delete_moves_todos_to_system_folder(client, db):
    folder = make_folder(client).json()
    db.add(models.Todo(text="Test", folder_id=folder["id"]))
    db.commit()

    client.delete(f"/folders/{folder['id']}")

    todo = db.query(models.Todo).one()
    allgemein = db.query(models.Folder).filter_by(is_system=True).one()
    assert todo.folder_id == allgemein.id