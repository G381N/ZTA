"""
Database handler for behavioral monitoring system.
Handles SQLite operations for event storage and trust scoring.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import threading

class BehaviorDatabase:
    """Thread-safe SQLite database handler for behavioral monitoring."""
    
    def __init__(self, db_path: str = "data/behavior.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    app_name TEXT,
                    session_id TEXT,
                    metadata TEXT,  -- JSON field for additional data
                    processed BOOLEAN DEFAULT FALSE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trust_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    score INTEGER NOT NULL,  -- 0-100
                    previous_score INTEGER,
                    change_reason TEXT,
                    anomaly_data TEXT  -- JSON field
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_id INTEGER,
                    anomaly_type TEXT NOT NULL,
                    severity REAL,  -- 0.0-1.0
                    description TEXT,
                    metadata TEXT,  -- JSON field
                    approved BOOLEAN DEFAULT FALSE,
                    approved_at DATETIME,
                    approved_by TEXT,
                    FOREIGN KEY(event_id) REFERENCES events(id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_app ON events(app_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_trust_timestamp ON trust_scores(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomalies(timestamp)")
            
            conn.commit()
            conn.close()
    
    def add_event(self, event_type: str, app_name: str = None, 
                  session_id: str = None, metadata: Dict = None) -> int:
        """Add a new event to the database."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO events (event_type, app_name, session_id, metadata)
                VALUES (?, ?, ?, ?)
            """, (event_type, app_name, session_id, metadata_json))
            
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logging.info(f"Added event: {event_type}, app: {app_name}, id: {event_id}")
            return event_id
    
    def get_recent_events(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get recent events within specified hours."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT id, timestamp, event_type, app_name, session_id, metadata
                FROM events 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (cutoff_time.isoformat(), limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event = {
                    'id': row[0],
                    'timestamp': row[1],
                    'event_type': row[2],
                    'app_name': row[3],
                    'session_id': row[4],
                    'metadata': json.loads(row[5]) if row[5] else {}
                }
                events.append(event)
            
            return events
    
    def get_unprocessed_events(self) -> List[Dict]:
        """Get events that haven't been processed by the ML model."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, event_type, app_name, session_id, metadata
                FROM events 
                WHERE processed = FALSE 
                ORDER BY timestamp ASC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                event = {
                    'id': row[0],
                    'timestamp': row[1],
                    'event_type': row[2],
                    'app_name': row[3],
                    'session_id': row[4],
                    'metadata': json.loads(row[5]) if row[5] else {}
                }
                events.append(event)
            
            return events
    
    def mark_events_processed(self, event_ids: List[int]):
        """Mark events as processed."""
        if not event_ids:
            return
            
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(event_ids))
            cursor.execute(f"""
                UPDATE events 
                SET processed = TRUE 
                WHERE id IN ({placeholders})
            """, event_ids)
            
            conn.commit()
            conn.close()
    
    def add_trust_score(self, score: int, previous_score: int = None, 
                       change_reason: str = None, anomaly_data: Dict = None) -> int:
        """Add a new trust score entry."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            anomaly_json = json.dumps(anomaly_data) if anomaly_data else None
            
            cursor.execute("""
                INSERT INTO trust_scores (score, previous_score, change_reason, anomaly_data)
                VALUES (?, ?, ?, ?)
            """, (score, previous_score, change_reason, anomaly_json))
            
            trust_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logging.info(f"Added trust score: {score} (was: {previous_score}), reason: {change_reason}")
            return trust_id
    
    def get_current_trust_score(self) -> Optional[int]:
        """Get the most recent trust score."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT score FROM trust_scores 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else None  # Return None if no scores yet
    
    def add_anomaly(self, event_id: int, anomaly_type: str, severity: float,
                   description: str, metadata: Dict = None) -> int:
        """Add an anomaly detection result."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO anomalies (event_id, anomaly_type, severity, description, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (event_id, anomaly_type, severity, description, metadata_json))
            
            anomaly_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logging.warning(f"Anomaly detected: {anomaly_type} (severity: {severity:.2f}) - {description}")
            return anomaly_id
    

    
    def get_events_since(self, timestamp: float) -> List[Dict[str, Any]]:
        """Get events since a specific timestamp."""
        cutoff_datetime = datetime.fromtimestamp(timestamp)
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM events 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            ''', (cutoff_datetime.isoformat(),))
            
            events = []
            for row in cursor.fetchall():
                event = {
                    'id': row[0],
                    'timestamp': row[1],
                    'event_type': row[2],
                    'app_name': row[3],
                    'session_id': row[4],
                    'metadata': json.loads(row[5]) if row[5] else {}
                }
                events.append(event)
            
            conn.close()
            return events
    
    def get_recent_anomalies(self, hours: int = 168) -> List[Dict]:  # Default 7 days instead of 24 hours
        """Get anomalies within specified hours."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            anomalies_list = []
            
            try:
                # Get formal anomalies from anomalies table
                cursor.execute("""
                    SELECT a.id, a.timestamp, a.event_id, a.anomaly_type, a.severity, 
                           a.description, a.metadata, e.event_type, e.app_name
                    FROM anomalies a
                    LEFT JOIN events e ON a.event_id = e.id
                    WHERE a.timestamp > ? 
                    ORDER BY a.timestamp DESC
                """, (cutoff_time.isoformat(),))
                
                rows = cursor.fetchall()
                
                for row in rows:
                    anomaly = {
                        'id': row[0],
                        'timestamp': row[1],
                        'event_id': row[2],
                        'anomaly_type': row[3] or 'general_anomaly',
                        'severity': float(row[4] or 0.5),
                        'description': row[5] or 'Anomaly detected',
                        'metadata': json.loads(row[6]) if row[6] else {},
                        'event_type': row[7] or 'unknown',
                        'app_name': row[8] or 'Unknown'
                    }
                    anomalies_list.append(anomaly)
                
            except Exception as e:
                logging.warning(f"Could not fetch formal anomalies: {e}")
            
            try:
                # Also get suspicious events that might be anomalies
                cursor.execute("""
                    SELECT id, timestamp, event_type, app_name, details, trust_impact, metadata
                    FROM events 
                    WHERE timestamp > ? 
                    AND (
                        trust_impact < -5 
                        OR event_type LIKE '%anomaly%' 
                        OR event_type LIKE '%suspicious%' 
                        OR event_type LIKE '%unknown%'
                        OR event_type LIKE '%flooding%'
                        OR app_name LIKE '%unknown%'
                        OR (event_type = 'network_connection' AND trust_impact < -2)
                    )
                    ORDER BY timestamp DESC
                    LIMIT 30
                """, (cutoff_time.isoformat(),))
                
                event_rows = cursor.fetchall()
                
                for row in event_rows:
                    # Check if this event already has a formal anomaly
                    existing_anomaly = any(a.get('event_id') == row[0] for a in anomalies_list)
                    if not existing_anomaly:
                        # Convert trust impact to severity (0-1 scale)
                        trust_impact = float(row[5] or 0)
                        severity = min(abs(trust_impact) / 20.0, 1.0) if trust_impact < 0 else 0.3
                        
                        # Determine anomaly type from event
                        event_type = row[2] or 'unknown'
                        anomaly_type = event_type
                        if 'network' in event_type.lower():
                            anomaly_type = 'network_anomaly'
                        elif 'unknown' in str(row[3]).lower() or 'unknown' in event_type.lower():
                            anomaly_type = 'unknown_application'
                        elif 'flooding' in event_type.lower():
                            anomaly_type = 'connection_flooding'
                        
                        # Create description
                        app_name = row[3] or 'Unknown'
                        details = row[4] or ''
                        description = f"Suspicious {event_type}: {app_name}"
                        if details and len(details) < 100:
                            description += f" - {details}"
                        
                        anomaly = {
                            'id': f"evt_{row[0]}",  # Prefix to distinguish from formal anomalies
                            'timestamp': row[1],
                            'event_id': row[0],
                            'anomaly_type': anomaly_type,
                            'severity': severity,
                            'description': description,
                            'metadata': json.loads(row[6]) if row[6] else {},
                            'event_type': event_type,
                            'app_name': app_name,
                            'trust_impact': trust_impact
                        }
                        anomalies_list.append(anomaly)
                        
            except Exception as e:
                logging.warning(f"Could not fetch suspicious events: {e}")
            
            conn.close()
            
            # Sort all anomalies by timestamp (newest first) and remove duplicates
            unique_anomalies = {}
            for anomaly in anomalies_list:
                # Use timestamp + type as key to avoid duplicates
                key = f"{anomaly['timestamp']}_{anomaly['anomaly_type']}"
                if key not in unique_anomalies or anomaly['severity'] > unique_anomalies[key]['severity']:
                    unique_anomalies[key] = anomaly
            
            # Sort by timestamp (newest first)
            sorted_anomalies = sorted(
                unique_anomalies.values(),
                key=lambda x: x['timestamp'],
                reverse=True
            )
            
            return sorted_anomalies[:50]  # Limit to 50 most recent
    
    def get_live_activity(self, minutes: int = 30) -> Dict[str, Any]:
        """Get live system activity for dashboard display."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            activity_summary = {
                'app_launches': [],
                'network_activity': [],
                'recent_events': [],
                'activity_stats': {
                    'total_events': 0,
                    'unique_apps': 0,
                    'network_connections': 0,
                    'suspicious_events': 0
                }
            }
            
            try:
                # Get recent app launches
                cursor.execute("""
                    SELECT timestamp, app_name, event_type, metadata, processed
                    FROM events 
                    WHERE timestamp > ? 
                    AND event_type IN ('app_launch', 'app_opened', 'application_launch')
                    ORDER BY timestamp DESC
                    LIMIT 20
                """, (cutoff_time.isoformat(),))
                
                for row in cursor.fetchall():
                    meta = json.loads(row[3]) if row[3] else {}
                    activity_summary['app_launches'].append({
                        'timestamp': row[0],
                        'app_name': row[1] or 'Unknown',
                        'event_type': row[2],
                        'details': meta.get('details', ''),
                        'trust_impact': float(meta.get('trust_impact', 0))
                    })
                
                # Get network activity
                cursor.execute("""
                    SELECT timestamp, event_type, app_name, metadata, processed
                    FROM events 
                    WHERE timestamp > ? 
                    AND (event_type LIKE '%network%' OR event_type LIKE '%connection%')
                    ORDER BY timestamp DESC
                    LIMIT 15
                """, (cutoff_time.isoformat(),))
                
                for row in cursor.fetchall():
                    meta = json.loads(row[3]) if row[3] else {}
                    activity_summary['network_activity'].append({
                        'timestamp': row[0],
                        'event_type': row[1],
                        'app_name': row[2] or '',
                        'details': meta.get('details', ''),
                        'trust_impact': float(meta.get('trust_impact', 0)),
                        'connections_count': meta.get('connection_count', 0),
                        'new_connections': meta.get('new_connections', 0)
                    })
                
                # Get all recent events for stats
                cursor.execute("""
                    SELECT event_type, app_name, metadata
                    FROM events 
                    WHERE timestamp > ?
                """, (cutoff_time.isoformat(),))
                
                all_events = cursor.fetchall()
                unique_apps = set()
                network_count = 0
                suspicious_count = 0
                
                for event in all_events:
                    meta = json.loads(event[2]) if event[2] else {}
                    trust_impact = float(meta.get('trust_impact', 0))
                    if event[1]:  # app_name exists
                        unique_apps.add(event[1])
                    if 'network' in str(event[0]).lower() or 'connection' in str(event[0]).lower():
                        network_count += 1
                    if trust_impact < -3:  # High negative trust impact
                        suspicious_count += 1
                
                activity_summary['activity_stats'] = {
                    'total_events': len(all_events),
                    'unique_apps': len(unique_apps),
                    'network_connections': network_count,
                    'suspicious_events': suspicious_count
                }
                
                # Get most recent events for display
                cursor.execute("""
                    SELECT timestamp, event_type, app_name, metadata, processed
                    FROM events 
                    WHERE timestamp > ? 
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, (cutoff_time.isoformat(),))
                
                for row in cursor.fetchall():
                    meta = json.loads(row[3]) if row[3] else {}
                    activity_summary['recent_events'].append({
                        'timestamp': row[0],
                        'event_type': row[1] or 'unknown',
                        'app_name': row[2] or 'System',
                        'details': meta.get('details', '')[:100],  # Truncate long details
                        'trust_impact': float(meta.get('trust_impact', 0))
                    })
                
            except Exception as e:
                logging.error(f"Error getting live activity: {e}")
            
            conn.close()
            return activity_summary
    
    def get_learned_patterns(self) -> Dict[str, Any]:
        """Get what the system has learned as normal behavioral patterns."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            patterns = {
                'usual_login_hours': [],
                'usual_apps': [],
                'usual_networks': [],
                'usual_locations': [],
                'activity_patterns': {},
                'stats': {}
            }
            
            try:
                # Get usual login/activity hours
                cursor.execute("""
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM events 
                    WHERE event_type LIKE '%login%' OR event_type LIKE '%session%'
                    GROUP BY hour
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                hours_data = cursor.fetchall()
                patterns['usual_login_hours'] = [
                    {'hour': f"{int(row[0]):02d}:00", 'frequency': row[1]} 
                    for row in hours_data if row[0]
                ]
                
                # Get most used apps
                cursor.execute("""
                    SELECT app_name, COUNT(*) as usage_count
                    FROM events 
                    WHERE app_name IS NOT NULL AND app_name != ''
                    GROUP BY app_name
                    ORDER BY usage_count DESC
                    LIMIT 15
                """)
                
                apps_data = cursor.fetchall()
                patterns['usual_apps'] = [
                    {'app': row[0], 'usage_count': row[1]} 
                    for row in apps_data
                ]
                
                # Get activity patterns by day of week
                cursor.execute("""
                    SELECT strftime('%w', timestamp) as day_of_week, 
                           strftime('%H', timestamp) as hour,
                           COUNT(*) as activity_count
                    FROM events 
                    GROUP BY day_of_week, hour
                    ORDER BY activity_count DESC
                    LIMIT 50
                """)
                
                activity_data = cursor.fetchall()
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                
                for row in activity_data:
                    if row[0] and row[1]:
                        day_name = day_names[int(row[0])]
                        hour = f"{int(row[1]):02d}:00"
                        if day_name not in patterns['activity_patterns']:
                            patterns['activity_patterns'][day_name] = []
                        patterns['activity_patterns'][day_name].append({
                            'hour': hour,
                            'activity': row[2]
                        })
                
                # Get network patterns (from metadata)
                cursor.execute("""
                    SELECT metadata, COUNT(*) as count
                    FROM events 
                    WHERE event_type LIKE '%network%' AND metadata IS NOT NULL
                    GROUP BY metadata
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                network_data = cursor.fetchall()
                networks = []
                for row in network_data:
                    try:
                        meta = json.loads(row[0]) if row[0] else {}
                        if 'destination' in meta or 'network' in meta:
                            networks.append({
                                'network': meta.get('destination', meta.get('network', 'Unknown')),
                                'frequency': row[1]
                            })
                    except:
                        pass
                
                patterns['usual_networks'] = networks
                
                # Get general stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(DISTINCT app_name) as unique_apps,
                        COUNT(DISTINCT DATE(timestamp)) as active_days
                    FROM events
                """)
                
                stats_row = cursor.fetchone()
                if stats_row:
                    patterns['stats'] = {
                        'total_events': stats_row[0],
                        'unique_apps': stats_row[1],
                        'active_days': stats_row[2],
                        'avg_events_per_day': round(stats_row[0] / max(stats_row[2], 1), 1)
                    }
                
            except Exception as e:
                logging.error(f"Error getting learned patterns: {e}")
            
            conn.close()
            return patterns

    def get_trust_history(self, hours: int = 24) -> List[Dict]:
        """Get trust score history within specified hours."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT timestamp, score, previous_score, change_reason, anomaly_data
                FROM trust_scores 
                WHERE timestamp > ? 
                ORDER BY timestamp ASC
            """, (cutoff_time.isoformat(),))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                entry = {
                    'timestamp': row[0],
                    'score': row[1],
                    'previous_score': row[2],
                    'change_reason': row[3],
                    'anomaly_data': json.loads(row[4]) if row[4] else {}
                }
                history.append(entry)
            
            return history
    
    def approve_anomaly(self, anomaly_id: int, approved_by: str = "admin") -> bool:
        """Mark an anomaly as approved/normal."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE anomalies 
                    SET approved = TRUE, approved_at = ?, approved_by = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), approved_by, anomaly_id))
                
                conn.commit()
                conn.close()
                
                logging.info(f"Anomaly {anomaly_id} approved as normal by {approved_by}")
                return True
                
        except Exception as e:
            logging.error(f"Error approving anomaly {anomaly_id}: {e}")
            return False
    
    def get_anomaly_by_id(self, anomaly_id: int) -> Optional[Dict]:
        """Get anomaly details by ID."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, timestamp, event_id, anomaly_type, severity, 
                           description, metadata, approved, approved_at, approved_by
                    FROM anomalies 
                    WHERE id = ?
                """, (anomaly_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        'id': row[0],
                        'timestamp': row[1],
                        'event_id': row[2],
                        'anomaly_type': row[3],
                        'severity': row[4],
                        'description': row[5],
                        'metadata': json.loads(row[6]) if row[6] else {},
                        'approved': bool(row[7]),
                        'approved_at': row[8],
                        'approved_by': row[9]
                    }
                return None
                
        except Exception as e:
            logging.error(f"Error getting anomaly {anomaly_id}: {e}")
            return None
    
    def get_events(self, hours: int = 24) -> List[Dict]:
        """Get events within specified hours (alias for get_recent_events)."""
        return self.get_recent_events(hours=hours)
    
    def cleanup_old_data(self, keep_days: int = 30):
        """Remove old data to prevent database from growing too large."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            # Delete old events
            cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_time.isoformat(),))
            
            # Delete old trust scores (keep more history for analysis)
            old_cutoff = datetime.now() - timedelta(days=keep_days * 2)
            cursor.execute("DELETE FROM trust_scores WHERE timestamp < ?", (old_cutoff.isoformat(),))
            
            # Delete old anomalies
            cursor.execute("DELETE FROM anomalies WHERE timestamp < ?", (cutoff_time.isoformat(),))
            
            # Vacuum database to reclaim space
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            logging.info(f"Cleaned up data older than {keep_days} days")
