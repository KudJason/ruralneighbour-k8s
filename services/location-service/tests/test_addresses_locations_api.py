import os
import uuid

os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_location_service.db"

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_create_address_accepts_is_default_and_response_contains_id_label_extra():
    user_id = str(uuid.uuid4())
    payload = {
        "user_id": user_id,
        "street_address": "123 Main St",
        "city": "Metropolis",
        "state": "CA",
        "postal_code": "90001",
        "country": "USA",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "is_default": True,
        "address_type": "residential",
    }

    headers = {"Authorization": f"Bearer user-{user_id}"}
    resp = client.post("/api/v1/addresses", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # id alias present and equals address_id
    assert "address_id" in data and "id" in data
    assert data["id"] == data["address_id"]

    # alias mapped to is_primary
    assert data["is_primary"] is True

    # label/extra present (nullable)
    assert "label" in data and "extra" in data


def test_locations_validate_ignores_extra_fields():
    payload = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
    }
    headers = {"Authorization": "Bearer user-00000000-0000-0000-0000-000000000001"}
    resp = client.post("/api/v1/locations/validate", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "is_valid" in data and "message" in data


def test_locations_distance_supports_dual_param_names_and_prefers_from_to():
    # using standard names
    headers = {"Authorization": "Bearer user-00000000-0000-0000-0000-000000000001"}
    resp_std = client.get(
        "/api/v1/locations/distance",
        params={
            "lat1": 40.0,
            "lon1": -73.0,
            "lat2": 41.0,
            "lon2": -74.0,
            "unit": "miles",
        },
        headers=headers,
    )
    assert resp_std.status_code == 200, resp_std.text
    dist_std = resp_std.json()["distance"]

    # using alias names
    resp_alt = client.get(
        "/api/v1/locations/distance",
        params={
            "from_lat": 40.0,
            "from_lng": -73.0,
            "to_lat": 41.0,
            "to_lng": -74.0,
            "unit": "miles",
        },
        headers=headers,
    )
    assert resp_alt.status_code == 200, resp_alt.text
    dist_alt = resp_alt.json()["distance"]

    assert abs(dist_std - dist_alt) < 1e-6

    # when both present, alias should take precedence and produce a different result if different values
    resp_pref = client.get(
        "/api/v1/locations/distance",
        params={
            "lat1": 10.0,
            "lon1": 10.0,
            "lat2": 20.0,
            "lon2": 20.0,
            "from_lat": 40.0,
            "from_lng": -73.0,
            "to_lat": 41.0,
            "to_lng": -74.0,
            "unit": "miles",
        },
        headers=headers,
    )
    assert resp_pref.status_code == 200, resp_pref.text
    dist_pref = resp_pref.json()["distance"]
    # should equal alias result, not the standard-only result
    assert abs(dist_pref - dist_alt) < 1e-6


