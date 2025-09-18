#!/usr/bin/env python3
"""
ZTA Dashboard API Test Suite
Tests all dashboard endpoints and functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_endpoint(endpoint, description):
    """Test a single API endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ {description}: OK")
                return data
            except json.JSONDecodeError:
                print(f"⚠️  {description}: Response not JSON")
                return response.text
        else:
            print(f"❌ {description}: HTTP {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ {description}: Connection failed")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ {description}: Timeout")
        return None
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return None

def analyze_dashboard_data(data, endpoint_name):
    """Analyze the structure and content of endpoint data"""
    if not data:
        return
        
    print(f"\n📊 {endpoint_name} Analysis:")
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                print(f"  • {key}: {len(value)} items")
                if value and isinstance(value[0], dict):
                    print(f"    Sample keys: {list(value[0].keys())}")
            else:
                print(f"  • {key}: {value}")
    elif isinstance(data, list):
        print(f"  • Total items: {len(data)}")
        if data and isinstance(data[0], dict):
            print(f"  • Sample keys: {list(data[0].keys())}")
    print()

def test_post_endpoint(endpoint, data, description):
    """Test a POST endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.post(url, json=data, timeout=5)
        
        if response.status_code in [200, 201]:
            print(f"✅ {description}: OK")
            try:
                return response.json()
            except:
                return response.text
        else:
            print(f"❌ {description}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return None

def main():
    print("🛡️  ZTA Dashboard API Test Suite")
    print("=" * 50)
    
    # Test basic connectivity
    print("\n🔗 Testing Basic Connectivity:")
    dashboard = test_endpoint("/", "Dashboard Page")
    
    print("\n📈 Testing Core API Endpoints:")
    
    # Test all dashboard endpoints
    endpoints = [
        ("/api/status", "System Status"),
        ("/api/training-status", "Training Status"),
        ("/api/trust", "Trust Score"),
        ("/api/trust/history", "Trust History"),
        ("/api/anomalies", "Anomalies List"),
        ("/api/activity", "Activity Feed"),
        ("/api/learned-patterns", "Learned Patterns"),
    ]
    
    results = {}
    for endpoint, description in endpoints:
        data = test_endpoint(endpoint, description)
        if data:
            results[endpoint] = data
            analyze_dashboard_data(data, description)
    
    print("\n🧪 Testing Interactive Functions:")
    
    # Test anomaly approval (if there are anomalies)
    if "/api/anomalies" in results and results["/api/anomalies"]:
        anomalies = results["/api/anomalies"]
        if isinstance(anomalies, list) and anomalies:
            first_anomaly_id = anomalies[0].get('id')
            if first_anomaly_id:
                test_post_endpoint(f"/api/anomalies/{first_anomaly_id}/approve", 
                                 {"approved_by": "test_user"}, 
                                 f"Approve Anomaly {first_anomaly_id}")
    
    # Test learned patterns management
    test_patterns = ["test_app", "sample_application"]
    for app_name in test_patterns:
        test_endpoint(f"/api/learned-apps/{app_name}", f"Get Learned App: {app_name}")
    
    print("\n📊 System Health Summary:")
    
    # Analyze system health
    if "/api/status" in results:
        status = results["/api/status"]
        print(f"  • System Status: {status.get('status', 'Unknown')}")
        print(f"  • Events Count: {status.get('events_count', 0)}")
        print(f"  • Anomalies Count: {status.get('anomalies_count', 0)}")
    
    if "/api/training-status" in results:
        training = results["/api/training-status"]
        print(f"  • Training Phase: {training.get('phase', 'Unknown')}")
        print(f"  • Events Processed: {training.get('events_processed', 0)}")
        print(f"  • Days Remaining: {training.get('days_remaining', 'N/A')}")
    
    if "/api/trust" in results:
        trust = results["/api/trust"]
        print(f"  • Current Trust Score: {trust.get('score', 0)}")
        print(f"  • Trust Level: {trust.get('level', 'Unknown')}")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

if __name__ == "__main__":
    main()
