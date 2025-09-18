#!/usr/bin/env python3
"""
Anomaly Simulation Script
This script generates suspicious activities to test the ZTA behavioral monitoring system.
"""

import os
import sys
import time
import random
import subprocess
import threading
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from core.database import BehaviorDatabase

class AnomalySimulator:
    def __init__(self):
        self.db = BehaviorDatabase()
        self.session_id = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def simulate_suspicious_apps(self):
        """Simulate launching suspicious applications"""
        suspicious_apps = [
            'nmap', 'metasploit', 'hydra', 'aircrack-ng', 'wireshark',
            'burpsuite', 'sqlmap', 'john', 'hashcat', 'netcat',
            'kismet', 'wifite', 'nikto', 'dirb', 'gobuster'
        ]
        
        print("🚨 Simulating suspicious application launches...")
        for i in range(5):
            app = random.choice(suspicious_apps)
            print(f"   Launching: {app}")
            
            # Add suspicious app launch event
            self.db.add_event(
                event_type="app_launch",
                app_name=app,
                session_id=self.session_id,
                metadata={
                    'suspicious': True,
                    'category': 'security_tool',
                    'simulated': True,
                    'launch_time': datetime.now().isoformat()
                }
            )
            time.sleep(0.5)
    
    def simulate_unusual_time_activity(self):
        """Simulate activity at unusual hours"""
        print("🕐 Simulating unusual time activity...")
        
        # Simulate activity at 3 AM (very suspicious)
        unusual_apps = ['terminal', 'browser', 'file_manager', 'text_editor']
        for app in unusual_apps:
            print(f"   3 AM activity: {app}")
            self.db.add_event(
                event_type="unusual_time",
                app_name=app,
                session_id=self.session_id,
                metadata={
                    'hour': 3,
                    'unusual_time': True,
                    'simulated': True,
                    'description': f"Activity at 3 AM: {app}"
                }
            )
            time.sleep(0.3)
    
    def simulate_rapid_app_switching(self):
        """Simulate rapid application switching"""
        print("⚡ Simulating rapid app switching...")
        
        apps = ['browser', 'terminal', 'file_manager', 'text_editor', 'calculator', 'email']
        for i in range(15):  # Rapid switching
            app = random.choice(apps)
            print(f"   Rapid switch to: {app}")
            self.db.add_event(
                event_type="rapid_switching",
                app_name=app,
                session_id=self.session_id,
                metadata={
                    'rapid_switching': True,
                    'switch_count': i + 1,
                    'simulated': True
                }
            )
            time.sleep(0.1)  # Very rapid
    
    def simulate_unknown_applications(self):
        """Simulate launching unknown/suspicious applications"""
        print("❓ Simulating unknown applications...")
        
        unknown_apps = [
            'suspicious_binary.exe', 'keylogger.py', 'backdoor.sh',
            'data_exfil.bin', 'crypto_miner', 'rootkit_installer',
            'network_scanner', 'password_stealer', 'trojan.exe'
        ]
        
        for app in unknown_apps[:6]:  # Launch 6 suspicious apps
            print(f"   Unknown app: {app}")
            self.db.add_event(
                event_type="unknown_application",
                app_name=app,
                session_id=self.session_id,
                metadata={
                    'unknown': True,
                    'suspicious_name': True,
                    'potential_malware': True,
                    'simulated': True
                }
            )
            time.sleep(0.4)
    
    def simulate_network_anomalies(self):
        """Simulate network connection anomalies"""
        print("🌐 Simulating network anomalies...")
        
        # Simulate connection flooding
        for i in range(50):  # Lots of connections
            self.db.add_event(
                event_type="network_connection",
                app_name="suspicious_network_tool",
                session_id=self.session_id,
                metadata={
                    'connection_count': i + 1,
                    'destination': f"192.168.1.{random.randint(1, 254)}",
                    'port': random.randint(1000, 9999),
                    'flooding': True,
                    'simulated': True
                }
            )
            if i % 10 == 0:
                print(f"   Network connections: {i + 1}/50")
            time.sleep(0.05)
    
    def simulate_data_access_anomaly(self):
        """Simulate unusual data access patterns"""
        print("📁 Simulating data access anomalies...")
        
        sensitive_files = [
            '/etc/passwd', '/etc/shadow', '/home/user/.ssh/id_rsa',
            '/var/log/auth.log', '/etc/sudoers', '/root/.bashrc',
            'database_backup.sql', 'confidential_documents.zip'
        ]
        
        for file_path in sensitive_files:
            print(f"   Accessing: {file_path}")
            self.db.add_event(
                event_type="file_access",
                app_name="file_manager",
                session_id=self.session_id,
                metadata={
                    'file_path': file_path,
                    'sensitive_file': True,
                    'unauthorized_access': True,
                    'simulated': True
                }
            )
            time.sleep(0.3)
    
    def add_high_severity_anomalies(self):
        """Add some high-severity anomalies directly to the database"""
        print("💀 Adding high-severity anomalies...")
        
        high_severity_events = [
            {
                'event_type': 'security_breach',
                'app_name': 'malicious_process',
                'description': 'Potential security breach detected - unauthorized privilege escalation attempt',
                'severity': 0.95
            },
            {
                'event_type': 'data_exfiltration',
                'app_name': 'network_tool',
                'description': 'Suspicious large data transfer to external IP detected',
                'severity': 0.89
            },
            {
                'event_type': 'malware_signature',
                'app_name': 'unknown_binary',
                'description': 'Process matches known malware signature patterns',
                'severity': 0.92
            },
            {
                'event_type': 'privilege_escalation',
                'app_name': 'system_tool',
                'description': 'Unauthorized attempt to gain administrative privileges',
                'severity': 0.87
            }
        ]
        
        for anomaly in high_severity_events:
            print(f"   High severity: {anomaly['description']}")
            
            # First add the event
            event_id = self.db.add_event(
                event_type=anomaly['event_type'],
                app_name=anomaly['app_name'],
                session_id=self.session_id,
                metadata={
                    'high_severity': True,
                    'simulated': True,
                    'description': anomaly['description']
                }
            )
            
            # Then add it as an anomaly
            self.db.add_anomaly(
                event_id=event_id,
                anomaly_type=anomaly['event_type'],
                severity=anomaly['severity'],
                description=anomaly['description'],
                metadata={'simulated': True, 'high_severity': True}
            )
            time.sleep(0.5)
    
    def run_simulation(self):
        """Run the complete anomaly simulation"""
        print("🎭 Starting Anomaly Simulation for ZTA Testing")
        print("=" * 50)
        
        # Run different types of simulations
        self.simulate_suspicious_apps()
        time.sleep(1)
        
        self.simulate_unusual_time_activity()
        time.sleep(1)
        
        self.simulate_rapid_app_switching()
        time.sleep(1)
        
        self.simulate_unknown_applications()
        time.sleep(1)
        
        self.simulate_network_anomalies()
        time.sleep(1)
        
        self.simulate_data_access_anomaly()
        time.sleep(1)
        
        self.add_high_severity_anomalies()
        
        print("\n✅ Simulation complete!")
        print("🔍 Check the dashboard to see the trust score drop and anomalies appear.")
        print("📊 Dashboard: http://localhost:8080")

if __name__ == "__main__":
    simulator = AnomalySimulator()
    simulator.run_simulation()
