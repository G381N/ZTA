#!/usr/bin/env python3
"""
ZTA Dashboard Management Tool
Complete dashboard functionality validation and management
"""

import requests
import json
import sqlite3
import os
from datetime import datetime

BASE_URL = "http://localhost:8080"
DB_PATH = "/home/gebin/Desktop/ZTA/data/behavior.db"

class DashboardManager:
    def __init__(self):
        self.base_url = BASE_URL
        self.timeout = 5

    def test_api_endpoint(self, endpoint):
        """Test a single API endpoint and return result"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            return False, str(e)

    def validate_all_apis(self):
        """Validate all dashboard API endpoints"""
        print("🛡️  ZTA Dashboard Validation")
        print("=" * 50)
        
        endpoints = [
            ("/api/status", "System Status"),
            ("/api/training-status", "Training Status"), 
            ("/api/trust", "Trust Score"),
            ("/api/anomalies", "Anomaly Detection"),
            ("/api/activity", "Recent Activity"),
            ("/api/learned-patterns", "Learned Patterns")
        ]
        
        results = []
        for endpoint, name in endpoints:
            success, data = self.test_api_endpoint(endpoint)
            results.append((endpoint, name, success, data))
            
            if success:
                print(f"✅ {name}: WORKING")
                # Show key data
                if endpoint == "/api/status":
                    print(f"   Status: {data.get('data', {}).get('status', 'Unknown')}")
                elif endpoint == "/api/training-status":
                    training_data = data.get('data', {})
                    print(f"   Phase: {training_data.get('phase', 'Unknown')}")
                    print(f"   Events Processed: {training_data.get('events_processed', 0)}")
                elif endpoint == "/api/trust":
                    trust_data = data.get('data', {})
                    print(f"   Trust Score: {trust_data.get('current_score', 0)}")
                elif endpoint == "/api/anomalies":
                    anomaly_data = data.get('data', {})
                    anomalies = anomaly_data.get('anomalies', [])
                    print(f"   Total Anomalies: {len(anomalies)}")
                elif endpoint == "/api/activity":
                    activity_data = data.get('data', {})
                    print(f"   Recent Activities: {activity_data.get('total_events', 0)}")
                elif endpoint == "/api/learned-patterns":
                    pattern_data = data.get('data', {})
                    patterns = pattern_data.get('patterns', [])
                    print(f"   Learned Patterns: {len(patterns)}")
            else:
                print(f"❌ {name}: FAILED - {data}")
            print()
        
        # Summary
        working = sum(1 for _, _, success, _ in results if success)
        total = len(results)
        
        print("=" * 50)
        if working == total:
            print(f"🎉 ALL {total} ENDPOINTS WORKING - Dashboard is 100% functional!")
        else:
            print(f"⚠️  {working}/{total} endpoints working - Needs attention")
        
        return working == total

    def get_database_stats(self):
        """Get database statistics"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            stats = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats[table_name] = count
            
            conn.close()
            return stats
        except Exception as e:
            return {"error": str(e)}

    def delete_learned_history(self):
        """Delete all learned patterns and reset training"""
        print("🗑️  Deleting Learned History")
        print("=" * 30)
        
        try:
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Clear events table
            cursor.execute("DELETE FROM events")
            events_deleted = cursor.rowcount
            
            # Clear anomalies table if exists
            try:
                cursor.execute("DELETE FROM anomalies")
                anomalies_deleted = cursor.rowcount
            except:
                anomalies_deleted = 0
            
            # Clear any other learned data tables
            try:
                cursor.execute("DELETE FROM patterns")
                patterns_deleted = cursor.rowcount
            except:
                patterns_deleted = 0
            
            conn.commit()
            conn.close()
            
            # Remove model file if exists
            model_path = "/home/gebin/Desktop/ZTA/models/behavior_model.pkl"
            if os.path.exists(model_path):
                os.remove(model_path)
                print("✅ Removed trained model file")
            
            print(f"✅ Deleted {events_deleted} events")
            print(f"✅ Deleted {anomalies_deleted} anomalies")
            print(f"✅ Deleted {patterns_deleted} patterns")
            print("✅ System reset to initial state")
            print("\n⚠️  Restart the system to begin fresh training")
            
            return True
            
        except Exception as e:
            print(f"❌ Error deleting history: {e}")
            return False

    def show_system_info(self):
        """Show comprehensive system information"""
        print("\n📊 ZTA System Information")
        print("=" * 40)
        
        # Database stats
        print("Database Statistics:")
        stats = self.get_database_stats()
        for table, count in stats.items():
            print(f"  {table}: {count} records")
        
        # File info
        model_path = "/home/gebin/Desktop/ZTA/models/behavior_model.pkl"
        if os.path.exists(model_path):
            mtime = os.path.getmtime(model_path)
            print(f"\nModel File: {datetime.fromtimestamp(mtime)}")
        else:
            print("\nModel File: Not found (untrained)")

    def interactive_menu(self):
        """Interactive dashboard management menu"""
        while True:
            print("\n🛡️  ZTA Dashboard Manager")
            print("=" * 30)
            print("1. Validate All Dashboard APIs")
            print("2. Show System Information")
            print("3. Delete Learned History")
            print("4. Test Trust Score")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                self.validate_all_apis()
            elif choice == "2":
                self.show_system_info()
            elif choice == "3":
                confirm = input("⚠️  This will delete ALL learned data. Continue? (yes/no): ")
                if confirm.lower() == "yes":
                    self.delete_learned_history()
            elif choice == "4":
                success, data = self.test_api_endpoint("/api/trust")
                if success:
                    trust_data = data.get('data', {})
                    print(f"Current Trust Score: {trust_data.get('current_score', 0)}")
                    print(f"Risk Level: {trust_data.get('risk_level', 'Unknown')}")
                else:
                    print(f"Error getting trust score: {data}")
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    manager = DashboardManager()
    
    # Check if system is running first
    success, _ = manager.test_api_endpoint("/api/status")
    if not success:
        print("❌ ZTA System is not running!")
        print("Please start the system with: python3 main.py")
        exit(1)
    
    print("🚀 ZTA System detected and running!")
    manager.interactive_menu()
