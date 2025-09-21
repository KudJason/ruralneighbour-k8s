from app.schemas.service_request import ServiceRequestCreate, ServiceRequestUpdate


def test_pydantic_alias_create_minimal_frontend_payload():
    """Test Pydantic alias mapping for ServiceRequestCreate"""
    payload = {
        "title": "Need a ride",
        "serviceType": "transportation",
        "pickupLatitude": 37.0,
        "pickupLongitude": -122.0,
        "offeredAmount": 25,
    }
    out = ServiceRequestCreate(**payload)
    assert out.title == "Need a ride"
    assert out.service_type == "transportation"
    assert out.pickup_latitude == 37.0
    assert out.pickup_longitude == -122.0
    assert out.offered_amount == 25


def test_pydantic_alias_update_frontend_payload():
    """Test Pydantic alias mapping for ServiceRequestUpdate"""
    payload = {"offeredAmount": 99, "description": "updated"}
    out = ServiceRequestUpdate(**payload)
    assert out.offered_amount == 99
    assert out.description == "updated"


def test_pydantic_alias_backward_compatibility():
    """Test that both snake_case and camelCase work for backward compatibility"""
    # Test snake_case (backend format)
    payload_snake = {
        "title": "Test request",
        "service_type": "transportation",
        "pickup_latitude": 40.0,
        "pickup_longitude": -74.0,
        "offered_amount": 50,
    }
    out_snake = ServiceRequestCreate(**payload_snake)
    assert out_snake.service_type == "transportation"
    assert out_snake.pickup_latitude == 40.0
    assert out_snake.offered_amount == 50

    # Test camelCase (frontend format)
    payload_camel = {
        "title": "Test request",
        "serviceType": "transportation",
        "pickupLatitude": 40.0,
        "pickupLongitude": -74.0,
        "offeredAmount": 50,
    }
    out_camel = ServiceRequestCreate(**payload_camel)
    assert out_camel.service_type == "transportation"
    assert out_camel.pickup_latitude == 40.0
    assert out_camel.offered_amount == 50
