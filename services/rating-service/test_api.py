#!/usr/bin/env python3
"""
简单的API测试脚本，用于验证评分服务的功能
"""
import requests
import json
from uuid import uuid4

# 测试配置
BASE_URL = "http://localhost:8000"
RATER_USER_ID = str(uuid4())
RATED_USER_ID = str(uuid4())
SERVICE_REQUEST_ID = str(uuid4())

def test_health():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    return response.status_code == 200

def test_create_rating_frontend_fields():
    """测试使用前端字段创建评分"""
    data = {
        "rated_user_id": RATED_USER_ID,
        "service_request_id": SERVICE_REQUEST_ID,
        "rating": 5,  # 前端字段
        "comment": "Excellent service!",
        "category": "quality"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/ratings/",
        json=data,
        params={"rater_user_id": RATER_USER_ID}
    )
    
    print(f"Create rating (frontend fields): {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return result.get("id")
    else:
        print(f"Error: {response.text}")
        return None

def test_create_rating_backend_fields():
    """测试使用后端字段创建评分"""
    data = {
        "rated_user_id": RATED_USER_ID,
        "service_request_id": str(uuid4()),
        "rating_score": 4,  # 后端字段
        "comment": "Very good service!",
        "category": "timeliness"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/ratings/",
        json=data,
        params={"rater_user_id": RATER_USER_ID}
    )
    
    print(f"Create rating (backend fields): {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return result.get("id")
    else:
        print(f"Error: {response.text}")
        return None

def test_get_ratings():
    """测试获取评分列表"""
    response = requests.get(f"{BASE_URL}/api/v1/ratings/")
    print(f"Get ratings: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Found {len(result)} ratings")
        return result
    else:
        print(f"Error: {response.text}")
        return []

def test_update_rating(rating_id):
    """测试更新评分"""
    if not rating_id:
        print("No rating ID provided for update test")
        return False
        
    data = {
        "rating": 3,  # 前端字段
        "comment": "Updated comment",
        "category": "updated_category"
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/v1/ratings/{rating_id}",
        json=data,
        params={"rater_user_id": RATER_USER_ID}
    )
    
    print(f"Update rating: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Updated rating: {json.dumps(result, indent=2)}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_user_rating_summary():
    """测试用户评分摘要"""
    response = requests.get(f"{BASE_URL}/api/v1/ratings/users/{RATED_USER_ID}/summary")
    print(f"User rating summary: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Summary: {json.dumps(result, indent=2)}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_can_rate_user():
    """测试检查是否可以评分"""
    response = requests.get(
        f"{BASE_URL}/api/v1/ratings/can_rate/{RATED_USER_ID}/{SERVICE_REQUEST_ID}",
        params={"rater_user_id": RATER_USER_ID}
    )
    print(f"Can rate user: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Can rate: {json.dumps(result, indent=2)}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """运行所有测试"""
    print("=== 评分服务API测试 ===")
    print(f"Base URL: {BASE_URL}")
    print(f"Rater User ID: {RATER_USER_ID}")
    print(f"Rated User ID: {RATED_USER_ID}")
    print(f"Service Request ID: {SERVICE_REQUEST_ID}")
    print()
    
    # 测试健康检查
    if not test_health():
        print("❌ 健康检查失败，服务可能未启动")
        return
    
    print("✅ 健康检查通过")
    print()
    
    # 测试创建评分（前端字段）
    rating_id1 = test_create_rating_frontend_fields()
    if rating_id1:
        print("✅ 前端字段创建评分成功")
    else:
        print("❌ 前端字段创建评分失败")
    print()
    
    # 测试创建评分（后端字段）
    rating_id2 = test_create_rating_backend_fields()
    if rating_id2:
        print("✅ 后端字段创建评分成功")
    else:
        print("❌ 后端字段创建评分失败")
    print()
    
    # 测试获取评分列表
    ratings = test_get_ratings()
    if ratings:
        print("✅ 获取评分列表成功")
    else:
        print("❌ 获取评分列表失败")
    print()
    
    # 测试更新评分
    if rating_id1 and test_update_rating(rating_id1):
        print("✅ 更新评分成功")
    else:
        print("❌ 更新评分失败")
    print()
    
    # 测试用户评分摘要
    if test_user_rating_summary():
        print("✅ 用户评分摘要成功")
    else:
        print("❌ 用户评分摘要失败")
    print()
    
    # 测试检查是否可以评分
    if test_can_rate_user():
        print("✅ 检查评分权限成功")
    else:
        print("❌ 检查评分权限失败")
    print()
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    main()






