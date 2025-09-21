import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

def test_create_rating_with_frontend_fields(client: TestClient, sample_user_ids):
    """测试使用前端字段创建评分"""
    rating_data = {
        "rated_user_id": str(sample_user_ids["rated_id"]),
        "service_request_id": str(sample_user_ids["service_request_id"]),
        "rating": 5,  # 前端字段
        "comment": "Excellent service!",
        "category": "quality"
    }
    
    response = client.post(
        f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
        json=rating_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5
    assert data["rating_score"] == 5
    assert data["data"]["category"] == "quality"
    assert data["rated_user_id"] == str(sample_user_ids["rated_id"])
    assert data["rater_user_id"] == str(sample_user_ids["rater_id"])

def test_create_rating_with_backend_fields(client: TestClient, sample_user_ids):
    """测试使用后端字段创建评分"""
    rating_data = {
        "rated_user_id": str(sample_user_ids["rated_id"]),
        "service_request_id": str(sample_user_ids["service_request_id"]),
        "rating_score": 4,  # 后端字段
        "comment": "Very good service!",
        "category": "timeliness"
    }
    
    response = client.post(
        f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
        json=rating_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 4
    assert data["rating_score"] == 4
    assert data["data"]["category"] == "timeliness"

def test_update_rating_with_frontend_fields(client: TestClient, sample_user_ids):
    """测试使用前端字段更新评分"""
    # 先创建一个评分
    rating_data = {
        "rated_user_id": str(sample_user_ids["rated_id"]),
        "service_request_id": str(sample_user_ids["service_request_id"]),
        "rating": 3,
        "comment": "Initial comment"
    }
    
    create_response = client.post(
        f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
        json=rating_data
    )
    assert create_response.status_code == 200
    rating_id = create_response.json()["id"]
    
    # 更新评分
    update_data = {
        "rating": 4,  # 前端字段
        "comment": "Updated comment",
        "category": "updated_category"
    }
    
    response = client.patch(
        f"/api/v1/ratings/{rating_id}?rater_user_id={sample_user_ids['rater_id']}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 4
    assert data["rating_score"] == 4
    assert data["data"]["category"] == "updated_category"

def test_get_ratings(client: TestClient, sample_user_ids):
    """测试获取评分列表"""
    # 创建几个评分
    for i in range(3):
        rating_data = {
            "rated_user_id": str(sample_user_ids["rated_id"]),
            "service_request_id": str(uuid4()),
            "rating": i + 1,
            "comment": f"Comment {i + 1}"
        }
        
        response = client.post(
            f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
            json=rating_data
        )
        assert response.status_code == 200
    
    # 获取评分列表
    response = client.get(f"/api/v1/ratings/?rated_user_id={sample_user_ids['rated_id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_get_rating_by_id(client: TestClient, sample_user_ids):
    """测试根据ID获取评分"""
    rating_data = {
        "rated_user_id": str(sample_user_ids["rated_id"]),
        "service_request_id": str(sample_user_ids["service_request_id"]),
        "rating": 5,
        "comment": "Test comment"
    }
    
    create_response = client.post(
        f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
        json=rating_data
    )
    assert create_response.status_code == 200
    rating_id = create_response.json()["id"]
    
    # 获取评分
    response = client.get(f"/api/v1/ratings/{rating_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rating_id
    assert data["rating"] == 5

def test_delete_rating(client: TestClient, sample_user_ids):
    """测试删除评分"""
    rating_data = {
        "rated_user_id": str(sample_user_ids["rated_id"]),
        "service_request_id": str(sample_user_ids["service_request_id"]),
        "rating": 3,
        "comment": "Test comment"
    }
    
    create_response = client.post(
        f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
        json=rating_data
    )
    assert create_response.status_code == 200
    rating_id = create_response.json()["id"]
    
    # 删除评分
    response = client.delete(
        f"/api/v1/ratings/{rating_id}?rater_user_id={sample_user_ids['rater_id']}"
    )
    assert response.status_code == 200
    
    # 验证评分已删除
    get_response = client.get(f"/api/v1/ratings/{rating_id}")
    assert get_response.status_code == 404

def test_cannot_rate_same_request_twice(client: TestClient, sample_user_ids):
    """测试不能对同一服务请求评分两次"""
    rating_data = {
        "rated_user_id": str(sample_user_ids["rated_id"]),
        "service_request_id": str(sample_user_ids["service_request_id"]),
        "rating": 3,
        "comment": "First rating"
    }
    
    # 第一次评分
    response1 = client.post(
        f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
        json=rating_data
    )
    assert response1.status_code == 200
    
    # 第二次评分应该失败
    response2 = client.post(
        f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
        json=rating_data
    )
    assert response2.status_code == 400

def test_can_rate_user_endpoint(client: TestClient, sample_user_ids):
    """测试检查是否可以评分的端点"""
    response = client.get(
        f"/api/v1/ratings/can_rate/{sample_user_ids['rated_id']}/{sample_user_ids['service_request_id']}?rater_user_id={sample_user_ids['rater_id']}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["can_rate"] == True

def test_user_rating_summary(client: TestClient, sample_user_ids):
    """测试用户评分摘要"""
    # 创建几个评分
    for i in range(5):
        rating_data = {
            "rated_user_id": str(sample_user_ids["rated_id"]),
            "service_request_id": str(uuid4()),
            "rating": (i % 5) + 1,  # 1-5的评分
            "comment": f"Comment {i + 1}"
        }
        
        response = client.post(
            f"/api/v1/ratings/?rater_user_id={sample_user_ids['rater_id']}",
            json=rating_data
        )
        assert response.status_code == 200
    
    # 获取评分摘要
    response = client.get(f"/api/v1/ratings/users/{sample_user_ids['rated_id']}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(sample_user_ids["rated_id"])
    assert data["total_ratings"] == 5
    assert "average_rating" in data
    assert "rating_distribution" in data






