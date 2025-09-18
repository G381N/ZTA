"""
Training Manager for ZTA System
Manages the learning phases and user behavior baseline establishment
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from .database import BehaviorDatabase

class TrainingManager:
    """
    Manages the training phases of the ZTA system.
    
    Phase 1: Initial Training (2 days) - Learn normal behavior patterns
    Phase 2: Baseline Validation (1 day) - Verify learned patterns
    Phase 3: Active Monitoring - Start anomaly detection with proper sensitivity
    """
    
    def __init__(self, db: BehaviorDatabase):
        self.db = db
        self.config_path = Path("config/training_config.json")
        self.config_path.parent.mkdir(exist_ok=True)
        
        # Training phases
        self.INITIAL_TRAINING_DAYS = 2
        self.BASELINE_VALIDATION_DAYS = 1
        self.MINIMUM_EVENTS_FOR_BASELINE = 100
        
        # Load or create training configuration
        self.config = self._load_or_create_config()
        
        logging.info(f"Training manager initialized. Current phase: {self.get_current_phase()}")
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing training config or create new one."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Validate config structure
                required_keys = ['training_start', 'phase', 'user_profile']
                if all(key in config for key in required_keys):
                    return config
            except Exception as e:
                logging.warning(f"Failed to load training config: {e}")
        
        # Create new training config
        config = {
            'training_start': datetime.now().isoformat(),
            'phase': 'initial_training',
            'user_profile': {
                'usual_work_hours': {'start': 8, 'end': 15, 'evening_start': 19, 'evening_end': 23},
                'usual_networks': [],
                'usual_applications': [],
                'baseline_established': False,
                'total_training_events': 0
            },
            'baseline_metrics': {
                'network_connections_per_hour': 0,
                'app_launches_per_hour': 0,
                'typical_session_duration': 0,
                'common_app_sequences': []
            }
        }
        
        self._save_config(config)
        return config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save training configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save training config: {e}")
    
    def get_current_phase(self) -> str:
        """Get current training phase."""
        training_start = datetime.fromisoformat(self.config['training_start'])
        days_since_start = (datetime.now() - training_start).days
        
        if days_since_start < self.INITIAL_TRAINING_DAYS:
            return 'initial_training'
        elif days_since_start < (self.INITIAL_TRAINING_DAYS + self.BASELINE_VALIDATION_DAYS):
            return 'baseline_validation'
        else:
            return 'active_monitoring'
    
    def should_detect_anomalies(self) -> bool:
        """Check if system should perform anomaly detection."""
        current_phase = self.get_current_phase()
        
        # Only detect anomalies in active monitoring phase
        if current_phase != 'active_monitoring':
            return False
            
        # Check if baseline is established
        if not self.config['user_profile']['baseline_established']:
            return False
            
        # Require minimum events for reliable detection
        total_events = self.config['user_profile']['total_training_events']
        return total_events >= self.MINIMUM_EVENTS_FOR_BASELINE
    
    def process_training_event(self, event: Dict[str, Any]) -> None:
        """Process an event during training phase."""
        current_phase = self.get_current_phase()
        
        if current_phase == 'initial_training':
            self._process_initial_training_event(event)
        elif current_phase == 'baseline_validation':
            self._process_baseline_validation_event(event)
        
        # Update total training events
        self.config['user_profile']['total_training_events'] += 1
        self._save_config(self.config)
    
    def _process_initial_training_event(self, event: Dict[str, Any]) -> None:
        """Process event during initial training phase."""
        event_type = event.get('event_type', '')
        app_name = event.get('app_name', '')
        timestamp = datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat()))
        
        user_profile = self.config['user_profile']
        
        # Learn usual applications
        if event_type == 'app_launch' and app_name:
            if app_name not in user_profile['usual_applications']:
                user_profile['usual_applications'].append(app_name)
        
        # Learn usual work hours
        hour = timestamp.hour
        work_hours = user_profile['usual_work_hours']
        
        # Update work hour ranges based on activity patterns
        if 6 <= hour <= 18:  # Day time activity
            work_hours['start'] = min(work_hours['start'], hour)
            work_hours['end'] = max(work_hours['end'], hour)
        elif 19 <= hour <= 23:  # Evening activity
            work_hours['evening_start'] = min(work_hours['evening_start'], hour)
            work_hours['evening_end'] = max(work_hours['evening_end'], hour)
        
        # Learn network patterns (from metadata if available)
        metadata = event.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        network_info = metadata.get('network_name') or metadata.get('ssid')
        if network_info and network_info not in user_profile['usual_networks']:
            user_profile['usual_networks'].append(network_info)
        
        logging.debug(f"Training event processed: {event_type} - {app_name}")
    
    def _process_baseline_validation_event(self, event: Dict[str, Any]) -> None:
        """Process event during baseline validation phase."""
        # Calculate baseline metrics
        baseline = self.config['baseline_metrics']
        
        # Get recent events for metric calculation
        recent_events = self.db.get_events(hours=24)
        if len(recent_events) < 10:
            return
            
        # Calculate network connections per hour
        network_events = [e for e in recent_events if e.get('event_type') == 'network_connection']
        baseline['network_connections_per_hour'] = len(network_events) / 24
        
        # Calculate app launches per hour
        app_events = [e for e in recent_events if e.get('event_type') == 'app_launch']
        baseline['app_launches_per_hour'] = len(app_events) / 24
        
        # Mark baseline as established after validation period
        training_start = datetime.fromisoformat(self.config['training_start'])
        if (datetime.now() - training_start).days >= self.INITIAL_TRAINING_DAYS:
            self.config['user_profile']['baseline_established'] = True
            logging.info("Baseline establishment complete. System ready for anomaly detection.")
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile with learned patterns."""
        return self.config['user_profile'].copy()
    
    def is_normal_application(self, app_name: str) -> bool:
        """Check if application is part of normal user behavior."""
        if not app_name:
            return False
            
        usual_apps = self.config['user_profile']['usual_applications']
        
        # Direct match
        if app_name in usual_apps:
            return True
            
        # Partial match for similar apps
        app_lower = app_name.lower()
        for usual_app in usual_apps:
            if usual_app.lower() in app_lower or app_lower in usual_app.lower():
                return True
        
        return False
    
    def is_normal_time(self, timestamp: datetime = None) -> bool:
        """Check if time is within normal work hours."""
        if timestamp is None:
            timestamp = datetime.now()
            
        hour = timestamp.hour
        work_hours = self.config['user_profile']['usual_work_hours']
        
        # Check day time work hours
        if work_hours['start'] <= hour <= work_hours['end']:
            return True
            
        # Check evening work hours  
        if work_hours['evening_start'] <= hour <= work_hours['evening_end']:
            return True
            
        return False
    
    def is_normal_network(self, network_name: str) -> bool:
        """Check if network is part of normal user behavior."""
        if not network_name:
            return False
            
        usual_networks = self.config['user_profile']['usual_networks']
        return network_name in usual_networks
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get comprehensive training status."""
        current_phase = self.get_current_phase()
        training_start = datetime.fromisoformat(self.config['training_start'])
        days_elapsed = (datetime.now() - training_start).days
        
        phase_info = {
            'initial_training': {
                'description': 'Learning your normal behavior patterns',
                'duration_days': self.INITIAL_TRAINING_DAYS,
                'progress': min(days_elapsed / self.INITIAL_TRAINING_DAYS * 100, 100)
            },
            'baseline_validation': {
                'description': 'Validating learned patterns',
                'duration_days': self.BASELINE_VALIDATION_DAYS,
                'progress': min((days_elapsed - self.INITIAL_TRAINING_DAYS) / self.BASELINE_VALIDATION_DAYS * 100, 100)
            },
            'active_monitoring': {
                'description': 'Active anomaly monitoring',
                'duration_days': float('inf'),
                'progress': 100
            }
        }
        
        return {
            'current_phase': current_phase,
            'phase_info': phase_info.get(current_phase, {}),
            'days_elapsed': days_elapsed,
            'total_training_events': self.config['user_profile']['total_training_events'],
            'baseline_established': self.config['user_profile']['baseline_established'],
            'anomaly_detection_active': self.should_detect_anomalies(),
            'user_profile': self.get_user_profile(),
            'baseline_metrics': self.config['baseline_metrics']
        }
    
    def approve_anomaly_as_normal(self, anomaly_id: int) -> bool:
        """Approve an anomaly as normal behavior and add to training data."""
        try:
            # Get anomaly details
            anomaly = self.db.get_anomaly_by_id(anomaly_id)
            if not anomaly:
                return False
            
            # Mark anomaly as approved
            self.db.approve_anomaly(anomaly_id)
            
            # Extract learning data from anomaly
            if anomaly.get('anomaly_type') == 'unknown_application':
                app_name = anomaly.get('metadata', {}).get('app_name')
                if app_name and app_name not in self.config['user_profile']['usual_applications']:
                    self.config['user_profile']['usual_applications'].append(app_name)
                    logging.info(f"Added {app_name} to usual applications")
            
            elif anomaly.get('anomaly_type') == 'unusual_time':
                # Adjust work hours based on approved time
                # Implementation depends on specific time pattern
                pass
            
            # Save updated profile
            self._save_config(self.config)
            return True
            
        except Exception as e:
            logging.error(f"Failed to approve anomaly {anomaly_id}: {e}")
            return False
    
    def reset_training(self) -> None:
        """Reset training to start fresh."""
        self.config = {
            'training_start': datetime.now().isoformat(),
            'phase': 'initial_training',
            'user_profile': {
                'usual_work_hours': {'start': 8, 'end': 15, 'evening_start': 19, 'evening_end': 23},
                'usual_networks': [],
                'usual_applications': [],
                'baseline_established': False,
                'total_training_events': 0
            },
            'baseline_metrics': {
                'network_connections_per_hour': 0,
                'app_launches_per_hour': 0,
                'typical_session_duration': 0,
                'common_app_sequences': []
            }
        }
        
        self._save_config(self.config)
        logging.info("Training reset complete. Starting fresh training period.")
    
    def remove_learned_app(self, app_name: str) -> bool:
        """Remove an application from learned normal apps."""
        try:
            usual_apps = self.config['user_profile']['usual_applications']
            if app_name in usual_apps:
                usual_apps.remove(app_name)
                self._save_config(self.config)
                logging.info(f"Removed {app_name} from learned applications")
                return True
            return False
        except Exception as e:
            logging.error(f"Error removing app {app_name}: {e}")
            return False
    
    def add_learned_app(self, app_name: str) -> bool:
        """Add an application to learned normal apps."""
        try:
            usual_apps = self.config['user_profile']['usual_applications']
            if app_name not in usual_apps:
                usual_apps.append(app_name)
                self._save_config(self.config)
                logging.info(f"Added {app_name} to learned applications")
            return True
        except Exception as e:
            logging.error(f"Error adding app {app_name}: {e}")
            return False
