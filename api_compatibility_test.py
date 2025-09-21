#!/usr/bin/env python3
"""
API Compatibility Test Script
Tests the compatibility between frontend API calls and backend endpoints
"""

import requests
import json
from typing import Dict, List, Any

# Base URLs for different services
BASE_URLS = {
    "auth": "http://localhost:8001",
    "user": "http://localhost:8002", 
    "location": "http://localhost:8003",
    "request": "http://localhost:8004",
    "notification": "http://localhost:8005",
    "payment": "http://localhost:8006",
    "content": "http://localhost:8007",
    "rating": "http://localhost:8008",
    "investment": "http://localhost:8009",
    "safety": "http://localhost:8010"
}

# Mock token for testing
MOCK_TOKEN = "demo-token"

def test_endpoint(method: str, url: str, expected_status: int = 200, **kwargs) -> Dict[str, Any]:
    """Test a single endpoint"""
    try:
        response = requests.request(method, url, **kwargs)
        return {
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "success": response.status_code == expected_status,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except Exception as e:
        return {
            "url": url,
            "method": method,
            "status_code": None,
            "expected_status": expected_status,
            "success": False,
            "error": str(e)
        }

def run_compatibility_tests():
    """Run all compatibility tests"""
    results = []
    
    print("🧪 Running API Compatibility Tests...")
    print("=" * 50)
    
    # Test 1: Request Service Endpoints
    print("\n📋 Testing Request Service...")
    request_tests = [
        ("GET", f"{BASE_URLS['request']}/api/v1/requests", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
        ("GET", f"{BASE_URLS['request']}/api/v1/requests/available", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
        ("POST", f"{BASE_URLS['request']}/api/v1/requests/test-id/accept", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
        ("PATCH", f"{BASE_URLS['request']}/api/v1/requests/test-id", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}, "json": {"title": "Test"}}),
    ]
    
    for method, url, expected_status, kwargs in request_tests:
        result = test_endpoint(method, url, expected_status, **kwargs)
        results.append(result)
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} {method} {url} - Status: {result['status_code']}")
    
    # Test 2: Message Service Endpoints
    print("\n💬 Testing Message Service...")
    message_tests = [
        ("GET", f"{BASE_URLS['notification']}/api/v1/messages/conversations/", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
        ("POST", f"{BASE_URLS['notification']}/api/v1/messages/conversations/test-user/mark_read", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
        ("GET", f"{BASE_URLS['notification']}/api/v1/messages/unread/count", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
    ]
    
    for method, url, expected_status, kwargs in message_tests:
        result = test_endpoint(method, url, expected_status, **kwargs)
        results.append(result)
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} {method} {url} - Status: {result['status_code']}")
    
    # Test 3: Notification Service Endpoints
    print("\n🔔 Testing Notification Service...")
    notification_tests = [
        ("POST", f"{BASE_URLS['notification']}/api/v1/notifications/mark_all_read", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
        ("GET", f"{BASE_URLS['notification']}/api/v1/notifications/unread/count", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
    ]
    
    for method, url, expected_status, kwargs in notification_tests:
        result = test_endpoint(method, url, expected_status, **kwargs)
        results.append(result)
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} {method} {url} - Status: {result['status_code']}")
    
    # Test 4: Payment Service Endpoints
    print("\n💳 Testing Payment Service...")
    payment_tests = [
        ("GET", f"{BASE_URLS['payment']}/api/v1/payments/methods", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
        ("GET", f"{BASE_URLS['payment']}/api/v1/payments/transactions", 200, {"headers": {"Authorization": f"Bearer {MOCK_TOKEN}"}}),
    ]
    
    for method, url, expected_status, kwargs in payment_tests:
        result = test_endpoint(method, url, expected_status, **kwargs)
        results.append(result)
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} {method} {url} - Status: {result['status_code']}")
    
    # Test 5: News Service Endpoints
    print("\n📰 Testing News Service...")
    news_tests = [
        ("GET", f"{BASE_URLS['content']}/api/v1/news/", 200),
        ("GET", f"{BASE_URLS['content']}/api/v1/news/test-id", 200),
    ]
    
    for method, url, expected_status, kwargs in news_tests:
        result = test_endpoint(method, url, expected_status, **kwargs)
        results.append(result)
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} {method} {url} - Status: {result['status_code']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - successful_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ Failed Tests:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['method']} {result['url']} - {result.get('error', 'Status: ' + str(result['status_code']))}")
    
    return results

if __name__ == "__main__":
    run_compatibility_tests()






