"""
Synthetic data generator for behavioral monitoring system.
Generates realistic usage patterns and anomalies for testing.
"""

import sys
import os
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import BehaviorDatabase

class SyntheticDataGenerator:
    """Generate synthetic behavioral data for testing the monitoring system."""
    
    def __init__(self, db: BehaviorDatabase):
        self.db = db
        
        # Common applications by category
        self.applications = {
            'browsers': ['firefox', 'chromium', 'chrome', 'safari'],
            'ide': ['code', 'pycharm', 'sublime-text', 'vim', 'atom'],
            'terminals': ['gnome-terminal', 'konsole', 'xterm', 'terminator'],
            'office': ['libreoffice-writer', 'libreoffice-calc', 'evince'],
            'media': ['vlc', 'spotify', 'rhythmbox', 'totem'],
            'social': ['discord', 'telegram', 'slack', 'teams'],
            'system': ['nautilus', 'gedit', 'calculator', 'system-monitor'],
            'unusual': ['unknown-app', 'suspicious-tool', 'rare-utility', 'test-program']
        }
        
        # Normal usage patterns (hour -> probability weight)
        self.normal_hours = {
            # Early morning
            6: 0.1, 7: 0.3, 8: 0.6,
            # Work hours
            9: 1.0, 10: 1.0, 11: 1.0, 12: 0.8,
            13: 0.9, 14: 1.0, 15: 1.0, 16: 1.0, 17: 0.8,
            # Evening
            18: 0.6, 19: 0.7, 20: 0.8, 21: 0.6, 22: 0.4,
            # Night/early morning
            23: 0.1, 0: 0.05, 1: 0.02, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.05
        }
        
        # Weekend modification (different patterns)
        self.weekend_modifier = {
            6: 0.3, 7: 0.2, 8: 0.3, 9: 0.4, 10: 0.6, 11: 0.7, 12: 0.8,
            13: 0.6, 14: 0.7, 15: 0.8, 16: 0.6, 17: 0.4,
            18: 0.5, 19: 0.6, 20: 0.7, 21: 0.5, 22: 0.3,
            23: 0.1, 0: 0.05, 1: 0.02, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.02
        }
        
    def generate_normal_session(self, start_time: datetime, duration_hours: float = 4.0) -> List[Dict]:
        """Generate a normal usage session with realistic application launches."""
        events = []
        session_id = f"synthetic_session_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Session start event
        events.append({
            'event_type': 'session_start',
            'app_name': None,
            'session_id': session_id,
            'timestamp': start_time,
            'metadata': {
                'session_type': 'normal',
                'expected_duration': duration_hours
            }
        })
        
        current_time = start_time
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Generate application launches throughout the session
        while current_time < end_time:
            # Choose application based on time and context
            app_name = self._choose_application(current_time)
            
            # Add some randomness to timing
            time_gap = random.uniform(2, 30)  # 2-30 minutes between apps
            current_time += timedelta(minutes=time_gap)
            
            if current_time >= end_time:
                break
            
            events.append({
                'event_type': 'app_launch',
                'app_name': app_name,
                'session_id': session_id,
                'timestamp': current_time,
                'metadata': {
                    'hour_of_day': current_time.hour,
                    'weekday': current_time.weekday(),
                    'is_weekend': current_time.weekday() >= 5,
                    'synthetic': True
                }
            })
        
        # Session end event
        events.append({
            'event_type': 'session_end',
            'app_name': None,
            'session_id': session_id,
            'timestamp': current_time,
            'metadata': {
                'actual_duration': (current_time - start_time).total_seconds() / 3600,
                'apps_launched': len([e for e in events if e['event_type'] == 'app_launch'])
            }
        })
        
        return events
    
    def generate_anomalous_session(self, start_time: datetime, anomaly_type: str) -> List[Dict]:
        """Generate a session with specific types of anomalies."""
        events = []
        session_id = f"synthetic_anomaly_{anomaly_type}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        if anomaly_type == 'unusual_time':
            # Generate activity at very late/early hours
            events = self._generate_unusual_time_activity(start_time, session_id)
            
        elif anomaly_type == 'unknown_applications':
            # Launch applications never seen before
            events = self._generate_unknown_app_activity(start_time, session_id)
            
        elif anomaly_type == 'rapid_switching':
            # Rapid switching between many applications
            events = self._generate_rapid_switching_activity(start_time, session_id)
            
        elif anomaly_type == 'weekend_work':
            # Work activity on weekend
            events = self._generate_weekend_work_activity(start_time, session_id)
            
        elif anomaly_type == 'suspicious_pattern':
            # Mix of several suspicious behaviors
            events = self._generate_suspicious_pattern_activity(start_time, session_id)
            
        else:
            # Default to general anomalous behavior
            events = self._generate_general_anomaly_activity(start_time, session_id)
        
        return events
    
    def _choose_application(self, timestamp: datetime) -> str:
        """Choose an application based on time and context."""
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5
        
        # Modify probabilities based on time
        if 9 <= hour <= 17 and not is_weekend:
            # Work hours - more development/office apps
            app_weights = {
                'ide': 0.3,
                'browsers': 0.25,
                'terminals': 0.2,
                'office': 0.15,
                'system': 0.1
            }
        elif 18 <= hour <= 22:
            # Evening - more casual apps
            app_weights = {
                'browsers': 0.4,
                'media': 0.25,
                'social': 0.2,
                'system': 0.15
            }
        elif is_weekend:
            # Weekend - more leisure apps
            app_weights = {
                'browsers': 0.3,
                'media': 0.3,
                'social': 0.2,
                'system': 0.2
            }
        else:
            # Default distribution
            app_weights = {
                'browsers': 0.3,
                'ide': 0.2,
                'terminals': 0.2,
                'system': 0.3
            }
        
        # Choose category
        category = random.choices(
            list(app_weights.keys()),
            weights=list(app_weights.values())
        )[0]
        
        # Choose specific app from category
        return random.choice(self.applications[category])
    
    def _generate_unusual_time_activity(self, start_time: datetime, session_id: str) -> List[Dict]:
        """Generate activity at unusual hours (late night/early morning)."""
        events = []
        
        # Start session
        events.append({
            'event_type': 'session_start',
            'app_name': None,
            'session_id': session_id,
            'timestamp': start_time,
            'metadata': {'anomaly_type': 'unusual_time'}
        })
        
        current_time = start_time
        
        # Launch 3-5 applications with short intervals
        for i in range(random.randint(3, 5)):
            current_time += timedelta(minutes=random.uniform(1, 10))
            
            # Choose applications that would be unusual at this time
            if start_time.hour >= 23 or start_time.hour <= 4:
                app = random.choice(self.applications['ide'] + self.applications['terminals'])
            else:
                app = random.choice(self.applications['browsers'] + self.applications['office'])
            
            events.append({
                'event_type': 'app_launch',
                'app_name': app,
                'session_id': session_id,
                'timestamp': current_time,
                'metadata': {
                    'anomaly_type': 'unusual_time',
                    'hour_of_day': current_time.hour,
                    'synthetic': True
                }
            })
        
        # End session
        current_time += timedelta(minutes=random.uniform(10, 30))
        events.append({
            'event_type': 'session_end',
            'app_name': None,
            'session_id': session_id,
            'timestamp': current_time,
            'metadata': {'anomaly_type': 'unusual_time'}
        })
        
        return events
    
    def _generate_unknown_app_activity(self, start_time: datetime, session_id: str) -> List[Dict]:
        """Generate activity with unknown/unusual applications."""
        events = []
        
        events.append({
            'event_type': 'session_start',
            'app_name': None,
            'session_id': session_id,
            'timestamp': start_time,
            'metadata': {'anomaly_type': 'unknown_applications'}
        })
        
        current_time = start_time
        
        # Launch several unknown applications
        unusual_apps = self.applications['unusual'] + [
            f'unknown-tool-{i}' for i in range(1, 4)
        ]
        
        for app in unusual_apps[:random.randint(2, 4)]:
            current_time += timedelta(minutes=random.uniform(2, 15))
            
            events.append({
                'event_type': 'app_launch',
                'app_name': app,
                'session_id': session_id,
                'timestamp': current_time,
                'metadata': {
                    'anomaly_type': 'unknown_application',
                    'synthetic': True
                }
            })
        
        current_time += timedelta(minutes=random.uniform(5, 20))
        events.append({
            'event_type': 'session_end',
            'app_name': None,
            'session_id': session_id,
            'timestamp': current_time,
            'metadata': {'anomaly_type': 'unknown_applications'}
        })
        
        return events
    
    def _generate_rapid_switching_activity(self, start_time: datetime, session_id: str) -> List[Dict]:
        """Generate rapid switching between many applications."""
        events = []
        
        events.append({
            'event_type': 'session_start',
            'app_name': None,
            'session_id': session_id,
            'timestamp': start_time,
            'metadata': {'anomaly_type': 'rapid_switching'}
        })
        
        current_time = start_time
        all_apps = []
        for category in ['browsers', 'ide', 'terminals', 'office', 'media']:
            all_apps.extend(self.applications[category])
        
        # Launch 8-12 applications in quick succession
        for i in range(random.randint(8, 12)):
            current_time += timedelta(seconds=random.uniform(10, 120))  # Very short intervals
            
            app = random.choice(all_apps)
            events.append({
                'event_type': 'app_launch',
                'app_name': app,
                'session_id': session_id,
                'timestamp': current_time,
                'metadata': {
                    'anomaly_type': 'rapid_switching',
                    'sequence_number': i + 1,
                    'synthetic': True
                }
            })
        
        current_time += timedelta(minutes=random.uniform(5, 15))
        events.append({
            'event_type': 'session_end',
            'app_name': None,
            'session_id': session_id,
            'timestamp': current_time,
            'metadata': {'anomaly_type': 'rapid_switching'}
        })
        
        return events
    
    def _generate_weekend_work_activity(self, start_time: datetime, session_id: str) -> List[Dict]:
        """Generate work activity on weekend (unusual pattern)."""
        events = []
        
        events.append({
            'event_type': 'session_start',
            'app_name': None,
            'session_id': session_id,
            'timestamp': start_time,
            'metadata': {'anomaly_type': 'weekend_work'}
        })
        
        current_time = start_time
        
        # Work applications on weekend
        work_apps = self.applications['ide'] + self.applications['terminals'] + self.applications['office']
        
        for i in range(random.randint(4, 7)):
            current_time += timedelta(minutes=random.uniform(5, 20))
            
            app = random.choice(work_apps)
            events.append({
                'event_type': 'app_launch',
                'app_name': app,
                'session_id': session_id,
                'timestamp': current_time,
                'metadata': {
                    'anomaly_type': 'weekend_work',
                    'is_weekend': True,
                    'synthetic': True
                }
            })
        
        current_time += timedelta(minutes=random.uniform(10, 30))
        events.append({
            'event_type': 'session_end',
            'app_name': None,
            'session_id': session_id,
            'timestamp': current_time,
            'metadata': {'anomaly_type': 'weekend_work'}
        })
        
        return events
    
    def _generate_suspicious_pattern_activity(self, start_time: datetime, session_id: str) -> List[Dict]:
        """Generate a pattern with multiple suspicious behaviors."""
        events = []
        
        events.append({
            'event_type': 'session_start',
            'app_name': None,
            'session_id': session_id,
            'timestamp': start_time,
            'metadata': {'anomaly_type': 'suspicious_pattern'}
        })
        
        current_time = start_time
        
        # Mix of unusual apps, rapid switching, and unusual timing
        unusual_apps = self.applications['unusual']
        normal_apps = self.applications['browsers'] + self.applications['system']
        
        for i in range(random.randint(6, 10)):
            # Alternate between very short and longer intervals
            if i % 2 == 0:
                current_time += timedelta(seconds=random.uniform(5, 30))  # Very rapid
            else:
                current_time += timedelta(minutes=random.uniform(2, 8))   # Normal-ish
            
            # Mix unusual and normal apps
            if random.random() < 0.4:  # 40% unusual apps
                app = random.choice(unusual_apps)
            else:
                app = random.choice(normal_apps)
            
            events.append({
                'event_type': 'app_launch',
                'app_name': app,
                'session_id': session_id,
                'timestamp': current_time,
                'metadata': {
                    'anomaly_type': 'suspicious_pattern',
                    'pattern_element': i + 1,
                    'synthetic': True
                }
            })
        
        current_time += timedelta(minutes=random.uniform(5, 20))
        events.append({
            'event_type': 'session_end',
            'app_name': None,
            'session_id': session_id,
            'timestamp': current_time,
            'metadata': {'anomaly_type': 'suspicious_pattern'}
        })
        
        return events
    
    def _generate_general_anomaly_activity(self, start_time: datetime, session_id: str) -> List[Dict]:
        """Generate general anomalous behavior."""
        # Just pick one of the other anomaly types randomly
        anomaly_types = ['unusual_time', 'unknown_applications', 'rapid_switching']
        chosen_type = random.choice(anomaly_types)
        return self.generate_anomalous_session(start_time, chosen_type)
    
    def generate_week_of_data(self, start_date: datetime) -> List[Dict]:
        """Generate a full week of synthetic data with normal and anomalous patterns."""
        all_events = []
        
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(7):
            day_date = current_date + timedelta(days=day)
            is_weekend = day_date.weekday() >= 5
            
            logging.info(f"Generating data for {day_date.strftime('%Y-%m-%d %A')}")
            
            # Generate 2-4 normal sessions per day
            num_sessions = random.randint(2, 4)
            
            for session in range(num_sessions):
                # Choose session start time based on day type
                if is_weekend:
                    # Weekend sessions - more relaxed timing
                    hour = random.choices(
                        list(range(24)),
                        weights=[self.weekend_modifier.get(h, 0.1) for h in range(24)]
                    )[0]
                else:
                    # Weekday sessions - normal work pattern
                    hour = random.choices(
                        list(range(24)),
                        weights=[self.normal_hours.get(h, 0.1) for h in range(24)]
                    )[0]
                
                minute = random.randint(0, 59)
                session_start = day_date.replace(hour=hour, minute=minute)
                
                # 95% normal sessions, 5% anomalous
                if random.random() < 0.95:
                    duration = random.uniform(1.0, 6.0)  # 1-6 hours
                    session_events = self.generate_normal_session(session_start, duration)
                else:
                    # Generate an anomaly
                    anomaly_types = ['unusual_time', 'unknown_applications', 'rapid_switching', 'weekend_work', 'suspicious_pattern']
                    anomaly_type = random.choice(anomaly_types)
                    session_events = self.generate_anomalous_session(session_start, anomaly_type)
                    logging.info(f"Generated anomaly: {anomaly_type} at {session_start}")
                
                all_events.extend(session_events)
        
        # Sort events by timestamp
        all_events.sort(key=lambda x: x['timestamp'])
        
        logging.info(f"Generated {len(all_events)} events for the week")
        return all_events
    
    def insert_synthetic_data(self, events: List[Dict]):
        """Insert synthetic events into the database."""
        logging.info(f"Inserting {len(events)} synthetic events into database")
        
        for event in events:
            self.db.add_event(
                event_type=event['event_type'],
                app_name=event['app_name'],
                session_id=event['session_id'],
                metadata=event['metadata']
            )
        
        logging.info("Synthetic data insertion completed")
    
    def generate_and_insert_demo_data(self, days_back: int = 7):
        """Generate and insert demo data for the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logging.info(f"Generating {days_back} days of demo data from {start_date} to {end_date}")
        
        # Generate data week by week
        all_events = []
        current_start = start_date
        
        while current_start < end_date:
            week_events = self.generate_week_of_data(current_start)
            # Filter events to not exceed end_date
            week_events = [e for e in week_events if e['timestamp'] <= end_date]
            all_events.extend(week_events)
            current_start += timedelta(days=7)
        
        # Insert into database
        self.insert_synthetic_data(all_events)
        
        return len(all_events)

def main():
    """Main function for standalone synthetic data generation."""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    db = BehaviorDatabase()
    
    # Initialize generator
    generator = SyntheticDataGenerator(db)
    
    # Generate 7 days of demo data
    event_count = generator.generate_and_insert_demo_data(days_back=7)
    
    print(f"Generated and inserted {event_count} synthetic events")
    print("You can now start the API server and see the demo data in action!")

if __name__ == "__main__":
    main()
