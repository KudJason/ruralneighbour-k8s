import os

import pytest
from fastapi.testclient import TestClient

os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_investments.db"

from app.main import app  # noqa: E402
from app.db.base import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_list_empty():
    r = client.get("/api/v1/investments/")
    assert r.status_code == 200
    assert r.json() == []


def test_create_and_get():
    payload = {
        "title": "Community Garden Microfund",
        "summary": "Support local growers",
        "impact": "Fresh produce",
        "expectedReturn": "3-5%",
        "minAmount": 25,
        "partner": "RN Coop",
        "coverKey": "react",
    }
    r = client.post("/api/v1/investments/", json=payload)
    assert r.status_code == 201
    created = r.json()
    assert created["title"] == payload["title"]
    assert created["minAmount"] == payload["minAmount"]

    rid = created["id"]
    r2 = client.get(f"/api/v1/investments/{rid}")
    assert r2.status_code == 200
    assert r2.json()["id"] == rid


def test_patch_and_delete():
    payload = {
        "title": "A",
        "summary": "B",
        "impact": "C",
        "expectedReturn": "1%",
        "minAmount": 10,
    }
    created = client.post("/api/v1/investments/", json=payload).json()
    rid = created["id"]

    upd = client.patch(f"/api/v1/investments/{rid}", json={"minAmount": 99})
    assert upd.status_code == 200
    assert upd.json()["minAmount"] == 99

    dele = client.delete(f"/api/v1/investments/{rid}")
    assert dele.status_code == 204

    not_found = client.get(f"/api/v1/investments/{rid}")
    assert not_found.status_code == 404








