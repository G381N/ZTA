#!/usr/bin/env python3
"""
Quick Dashboard API Test
Tests all API endpoints to ensure dashboard is 100% functional
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080"
TIMEOUT = 5

def test_api_endpoint(endpoint):
    """Test a single API endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"Testing {endpoint}...")
        
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ {endpoint}: OK - Status {response.status_code}")
        
        # Show key data for each endpoint
        if endpoint == "/status":
            print(f"   System Status: {data.get('status', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
            
        elif endpoint == "/training-status":
            print(f"   Training Phase: {data.get('phase', 'Unknown')}")
            print(f"   Events Processed: {data.get('events_processed', 0)}")
            
        elif endpoint == "/trust":
            print(f"   Trust Score: {data.get('score', 0)}")
            
        elif endpoint == "/anomalies":
            anomalies = data.get('anomalies', [])
            print(f"   Total Anomalies: {len(anomalies)}")
            if anomalies:
                print(f"   Latest: {anomalies[0].get('type', 'Unknown')} at {anomalies[0].get('timestamp', 'Unknown')}")
                
        elif endpoint == "/activity":
            activities = data.get('activities', [])
            print(f"   Recent Activities: {len(activities)}")
            
        elif endpoint == "/learned-patterns":
            patterns = data.get('patterns', [])
            print(f"   Learned Patterns: {len(patterns)}")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint}: ERROR - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ {endpoint}: UNEXPECTED ERROR - {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("ZTA Dashboard API Test Suite")
    print(f"Testing at: {datetime.now()}")
    print("=" * 60)
    
    # Test all main API endpoints
    endpoints = [
        "/status",
        "/training-status", 
        "/trust",
        "/anomalies",
        "/activity",
        "/learned-patterns"
    ]
    
    results = []
    for endpoint in endpoints:
        success = test_api_endpoint(endpoint)
        results.append((endpoint, success))
        print()
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for endpoint, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{endpoint:20} {status}")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Dashboard is 100% functional!")
    else:
        print("⚠️  Some tests failed - Dashboard needs attention")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
