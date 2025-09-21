import os
os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_news_crud_and_filters():
    # Create (admin)
    create_payload = {
        "title": "Hello",
        "content": "World",
        "is_featured": True,
        "is_active": True,
    }
    r = client.post("/api/v1/news/", json=create_payload, headers={"authorization": "admin-token"})
    assert r.status_code == 200, r.text
    article = r.json()
    article_id = article["article_id"]

    # Get public list (no filter)
    r = client.get("/api/v1/news/?skip=0&limit=50")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["is_active"] is True

    # Get public list (is_featured=true)
    r = client.get("/api/v1/news/?is_featured=true")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1

    # Get public list (is_featured=false)
    r = client.get("/api/v1/news/?is_featured=false")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 0

    # GET detail
    r = client.get(f"/api/v1/news/{article_id}")
    assert r.status_code == 200
    assert r.json()["title"] == "Hello"

    # PATCH (admin)
    r = client.patch(
        f"/api/v1/news/{article_id}",
        json={"title": "Hello2", "is_featured": False},
        headers={"authorization": "admin-token"},
    )
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Hello2"
    assert patched["is_featured"] is False

    # Filter again (is_featured=true) should be 0 now
    r = client.get("/api/v1/news/?is_featured=true")
    assert r.status_code == 200
    assert len(r.json()) == 0

    # DELETE (admin)
    r = client.delete(
        f"/api/v1/news/{article_id}", headers={"authorization": "admin-token"}
    )
    assert r.status_code == 200

    # GET after delete
    r = client.get(f"/api/v1/news/{article_id}")
    assert r.status_code == 404


