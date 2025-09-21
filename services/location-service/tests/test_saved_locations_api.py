import os
import uuid

os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_location_service.db"

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def auth(user_id: str):
    return {"Authorization": f"Bearer user-{user_id}"}


def test_saved_locations_crud():
    user_id = str(uuid.uuid4())

    # Initially empty
    resp = client.get("/api/v1/locations/saved", headers=auth(user_id))
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # Create
    payload = {
        "address": "5th Ave, NYC",
        "latitude": 40.775,
        "longitude": -73.965,
    }
    resp = client.post("/api/v1/locations/saved", json=payload, headers=auth(user_id))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == payload["address"]
    loc_id = data["location_id"]

    # List now has 1
    resp = client.get("/api/v1/locations/saved", headers=auth(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["locations"]) == 1

    # Delete
    resp = client.delete(f"/api/v1/locations/saved/{loc_id}", headers=auth(user_id))
    assert resp.status_code == 200

    # List empty again
    resp = client.get("/api/v1/locations/saved", headers=auth(user_id))
    assert resp.status_code == 200
    assert resp.json()["total"] == 0








