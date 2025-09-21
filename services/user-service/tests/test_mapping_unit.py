from app.api.v1.endpoints.profiles import (
    map_frontend_provider_update_to_schema,
    map_frontend_profile_update_to_schema,
)


def test_map_provider_update_aliases():
    payload = {
        "services": ["transportation", "errands"],
        "availability": {"mon": "9-18"},
        "description": "SUV",
        "is_available": "true",
    }
    out = map_frontend_provider_update_to_schema(payload)
    # 模型字段为字符串存储，函数会将结构化数据序列化为 JSON 字符串
    assert out.services_offered == "[\"transportation\", \"errands\"]"
    assert out.availability_schedule == "{\"mon\": \"9-18\"}"
    assert out.vehicle_description == "SUV"
    assert out.is_available == "true"


def test_map_profile_update_aliases():
    payload = {
        "bio": "hello",
        "phone": "+111",
        "avatar_url": "https://a.b/c.png",
    }
    out = map_frontend_profile_update_to_schema(payload)
    assert out.bio == "hello"
    assert out.phone_number == "+111"
    assert out.profile_picture_url == "https://a.b/c.png"

