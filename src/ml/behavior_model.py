"""
AI-based behavior model for anomaly detection.
Uses IsolationForest to detect unusual usage patterns.
"""

import numpy as np
import pandas as pd
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from .feature_extractor import FeatureExtractor

class BehaviorModel:
    """AI-based behavioral monitoring model using anomaly detection."""
    
    def __init__(self, model_path: str = "models/behavior_model.pkl"):
        self.model_path = Path(model_path)
        self.model_path.parent.mkdir(exist_ok=True)
        
        # Model components
        self.isolation_forest: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.feature_extractor = FeatureExtractor()
        
        # Enhanced model parameters for higher sensitivity
        self.contamination = 0.15  # Increased from 0.1 - expect more anomalies (more sensitive)
        self.n_estimators = 150    # Increased from 100 for better detection
        self.random_state = 42
        
        # Enhanced anomaly thresholds (more sensitive)
        self.anomaly_thresholds = {
            'critical': -0.25,    # Most severe anomalies
            'high': -0.15,        # Clear anomalies  
            'medium': -0.05,      # Suspicious patterns
            'low': 0.05           # Slightly unusual
        }
        
        # Load existing model if available
        self._load_model()
        
    def _load_model(self) -> bool:
        """Load existing model from disk."""
        try:
            if not self.model_path.exists():
                logging.info("No existing model found, will train new model")
                return False
            
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.isolation_forest = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.training_info = model_data.get('training_info', {})
            
            logging.info(f"Loaded model trained at {self.training_info.get('trained_at')}")
            return True
            
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            return False
    
    def _save_model(self):
        """Save model to disk."""
        try:
            model_data = {
                'model': self.isolation_forest,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'training_info': self.training_info
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logging.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logging.error(f"Error saving model: {e}")
    
    def train(self, events: List[Dict], force_retrain: bool = False) -> Dict[str, Any]:
        """
        Train the behavior model on historical events.
        
        Args:
            events: List of event dictionaries
            force_retrain: Whether to retrain even if model exists
            
        Returns:
            Training results dictionary
        """
        if not events:
            logging.warning("No events provided for training")
            return {'status': 'error', 'message': 'No training data'}
        
        # Check if we need to train
        if self.isolation_forest is not None and not force_retrain:
            logging.info("Model already exists, skipping training")
            return {'status': 'skipped', 'message': 'Model already trained'}
        
        try:
            logging.info(f"Training behavior model on {len(events)} events")
            
            # Extract features
            df = self.feature_extractor.extract_event_features(events)
            if df.empty:
                return {'status': 'error', 'message': 'No features extracted'}
            
            # Prepare features for ML
            X, feature_names = self.feature_extractor.prepare_features_for_ml(df)
            if X.size == 0:
                return {'status': 'error', 'message': 'No ML features available'}
            
            # Filter out any invalid data
            X = self._clean_training_data(X)
            if X.size == 0:
                return {'status': 'error', 'message': 'No valid training data after cleaning'}
            
            logging.info(f"Training on {X.shape[0]} samples with {X.shape[1]} features")
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train isolation forest
            self.isolation_forest = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                n_jobs=-1  # Use all cores
            )
            
            self.isolation_forest.fit(X_scaled)
            self.feature_names = feature_names
            
            # Update training info
            self.training_info = {
                'trained_at': datetime.now().isoformat(),
                'training_samples': X.shape[0],
                'feature_count': X.shape[1],
                'model_version': '1.0',
                'contamination': self.contamination
            }
            
            # Save model
            self._save_model()
            
            # Evaluate on training data to set thresholds
            scores = self.isolation_forest.decision_function(X_scaled)
            
            # Calculate percentiles for thresholds
            self.anomaly_thresholds = {
                'high': np.percentile(scores, 5),    # Bottom 5% are clear anomalies
                'medium': np.percentile(scores, 15), # Bottom 15% are suspicious
                'low': np.percentile(scores, 30)     # Bottom 30% are slightly unusual
            }
            
            result = {
                'status': 'success',
                'training_samples': X.shape[0],
                'features': feature_names,
                'anomaly_thresholds': self.anomaly_thresholds,
                'training_info': self.training_info
            }
            
            logging.info(f"Model training completed successfully: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error training model: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _clean_training_data(self, X: np.ndarray) -> np.ndarray:
        """Clean training data by removing invalid values."""
        # Remove rows with NaN or infinite values
        mask = np.isfinite(X).all(axis=1)
        X_clean = X[mask]
        
        if len(X_clean) < len(X):
            logging.warning(f"Removed {len(X) - len(X_clean)} invalid samples during training")
        
        return X_clean
    
    def detect_anomalies(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in new events.
        
        Args:
            events: List of new event dictionaries
            
        Returns:
            List of anomaly detection results
        """
        if not self.isolation_forest:
            logging.warning("Model not trained, cannot detect anomalies")
            return []
        
        if not events:
            return []
        
        try:
            # Extract features
            df = self.feature_extractor.extract_event_features(events)
            if df.empty:
                return []
            
            # Prepare features for ML
            X, _ = self.feature_extractor.prepare_features_for_ml(df)
            if X.size == 0:
                return []
            
            # Ensure feature consistency
            if X.shape[1] != len(self.feature_names):
                logging.error(f"Feature count mismatch: got {X.shape[1]}, expected {len(self.feature_names)}")
                return []
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict anomalies
            anomaly_labels = self.isolation_forest.predict(X_scaled)
            anomaly_scores = self.isolation_forest.decision_function(X_scaled)
            
            # Process results
            anomalies = []
            for i, (event, label, score) in enumerate(zip(events, anomaly_labels, anomaly_scores)):
                if label == -1:  # Anomaly detected
                    severity = self._calculate_severity(score)
                    anomaly_type, description = self._classify_anomaly(event, df.iloc[i], score)
                    
                    anomaly = {
                        'event_id': event['id'],
                        'event': event,
                        'anomaly_score': float(score),
                        'severity': severity,
                        'anomaly_type': anomaly_type,
                        'description': description,
                        'detected_at': datetime.now().isoformat(),
                        'model_info': {
                            'model_version': self.training_info.get('model_version'),
                            'trained_at': self.training_info.get('trained_at')
                        }
                    }
                    
                    anomalies.append(anomaly)
                    
                    logging.info(f"Anomaly detected: {anomaly_type} (severity: {severity:.2f}, score: {score:.3f})")
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error detecting anomalies: {e}")
            return []
    
    def _calculate_severity(self, score: float) -> float:
        """Enhanced severity calculation based on score with more granular levels."""
        if score <= self.anomaly_thresholds['critical']:
            return 0.9 + (self.anomaly_thresholds['critical'] - score) * 0.2  # 0.9-1.0
        elif score <= self.anomaly_thresholds['high']:
            return 0.7 + (self.anomaly_thresholds['high'] - score) * 0.6    # 0.7-0.9
        elif score <= self.anomaly_thresholds['medium']:
            return 0.4 + (self.anomaly_thresholds['medium'] - score) * 0.6  # 0.4-0.7
        elif score <= self.anomaly_thresholds['low']:
            return 0.2 + (self.anomaly_thresholds['low'] - score) * 0.4     # 0.2-0.4
        else:
            return max(0.1, 0.3 - score * 0.2)  # 0.1-0.3
    
    def _classify_anomaly(self, event: Dict, features: pd.Series, score: float) -> Tuple[str, str]:
        """Enhanced anomaly classification with network and security patterns."""
        app_name = event.get('app_name', 'unknown')
        event_type = event.get('event_type', 'unknown')
        timestamp = pd.to_datetime(event['timestamp'])
        metadata = event.get('metadata', {})
        
        # 1. NETWORK-BASED ANOMALIES (NEW)
        if event_type == 'network_connection':
            remote_ip = metadata.get('remote_ip', '')
            remote_port = metadata.get('remote_port', 0)
            
            if metadata.get('is_suspicious_ip', False):
                return 'suspicious_ip_connection', f"Connection to suspicious IP: {remote_ip}:{remote_port}"
            
            if remote_port in {22, 23, 135, 139, 445, 1433, 3389, 5432}:
                return 'suspicious_port_access', f"Connection to high-risk port: {remote_ip}:{remote_port}"
            
            connection_count = features.get('connection_count', 0)
            if connection_count > 50:
                return 'connection_flooding', f"Excessive connections: {connection_count} active connections"
        
        elif event_type == 'high_bandwidth':
            bytes_sent = metadata.get('bytes_sent_rate', 0)
            bytes_recv = metadata.get('bytes_recv_rate', 0)
            return 'bandwidth_anomaly', f"High bandwidth usage: {bytes_sent/1024/1024:.1f}MB/s sent, {bytes_recv/1024/1024:.1f}MB/s received"
        
        elif event_type == 'connection_flooding':
            return 'network_flooding', f"Connection flooding: {metadata.get('connection_count', 0)} connections in 5 minutes"
        
        elif event_type == 'suspicious_port_connection':
            return 'malicious_port_access', f"Access to attack-vector port: {metadata.get('remote_port', 0)}"
        
        # 2. SECURITY TOOL ANOMALIES (NEW)
        elif event_type == 'suspicious_application':
            risk_level = metadata.get('risk_level', 'unknown')
            keyword = metadata.get('suspicious_keyword', '')
            return 'malicious_tool_usage', f"Suspicious tool detected: {app_name} (keyword: {keyword}, risk: {risk_level})"
        
        elif event_type == 'suspicious_app_combination':
            pattern = metadata.get('pattern_keywords', [])
            return 'attack_pattern_detected', f"Suspicious tool combination: {pattern} including {app_name}"
        
        elif features.get('is_security_tool', False):
            return 'security_tool_usage', f"Security/hacking tool launched: {app_name}"
        
        # 3. APPLICATION FREQUENCY ANOMALIES (ENHANCED)
        elif event_type == 'high_frequency_app':
            launches = metadata.get('launches_per_hour', 0)
            return 'app_abuse_pattern', f"Excessive app launches: {app_name} launched {launches} times in 1 hour"
        
        elif event_type == 'request_flooding':
            rate = metadata.get('launches_per_minute', 0)
            return 'system_flooding', f"Request flooding: {rate} app launches per minute"
        
        elif features.get('is_flooding_behavior', False):
            return 'behavioral_flooding', f"Flooding behavior detected with {app_name}"
        
        # 4. TIME-BASED ANOMALIES (ORIGINAL + ENHANCED)
        if features.get('is_very_late', False) and features.get('is_security_tool', False):
            return 'suspicious_late_activity', f"Security tool usage at suspicious hour: {app_name} at {timestamp.hour:02d}:{timestamp.minute:02d}"
        
        elif features.get('is_very_late', False):
            return 'unusual_time', f"Activity at very late hour ({timestamp.hour:02d}:{timestamp.minute:02d})"
        
        elif features.get('is_very_early', False):
            return 'unusual_time', f"Activity at very early hour ({timestamp.hour:02d}:{timestamp.minute:02d})"
        
        elif features.get('is_weekend', False) and not self._is_weekend_normal():
            return 'unusual_schedule', f"Unusual weekend activity with {app_name}"
        
        # 5. APPLICATION-BASED ANOMALIES (ENHANCED)
        app_rarity = features.get('app_rarity', 0)
        if app_rarity > 0.8:  # Very rare application
            return 'rare_application', f"Very rare application launched: {app_name} (rarity: {app_rarity:.2f})"
        
        elif features.get('is_new_app', False):
            return 'unknown_application', f"First time seeing application: {app_name}"
        
        elif features.get('is_network_tool', False):
            return 'network_tool_usage', f"Network tool launched: {app_name}"
        
        elif features.get('is_admin_tool', False):
            return 'privilege_escalation', f"Administrative tool usage: {app_name}"
        
        # 6. PATTERN-BASED ANOMALIES (ENHANCED)
        apps_in_5min = features.get('apps_in_5min', 0)
        if apps_in_5min > 8:  # Lowered threshold for higher sensitivity
            return 'rapid_switching', f"Rapid application switching: {apps_in_5min} apps in 5 minutes"
        
        time_since_last = features.get('time_since_last', 0)
        if time_since_last < 0.2:  # Less than 12 seconds (more sensitive)
            return 'rapid_activity', f"Very rapid consecutive activity ({time_since_last*60:.1f} seconds apart)"
        
        # 7. SYSTEM-BASED ANOMALIES (ENHANCED)
        cpu_percent = features.get('cpu_percent', 0)
        if cpu_percent > 90:  # Higher threshold
            return 'critical_system_load', f"Critical CPU usage during activity: {cpu_percent:.1f}%"
        elif cpu_percent > 70:
            return 'high_system_load', f"High CPU usage during activity: {cpu_percent:.1f}%"
        
        # 8. WORK PATTERN ANOMALIES (ENHANCED)
        if (not features.get('is_work_hours', False) and 
            (features.get('is_ide', False) or features.get('is_admin_tool', False))):
            return 'suspicious_work_pattern', f"Development/admin activity outside work hours: {app_name}"
        
        # 9. NETWORK PATTERN ANOMALIES (NEW)
        if features.get('is_high_bandwidth', False):
            return 'data_exfiltration_risk', f"High bandwidth usage with {app_name} - potential data exfiltration"
        
        connections_per_hour = features.get('connections_per_hour', 0)
        if connections_per_hour > 100:
            return 'network_scanning', f"Excessive network connections: {connections_per_hour} per hour"
        
        # 10. SECURITY ESCALATION PATTERNS (NEW)
        if features.get('risk_escalation', 0) > 0:
            return 'risk_escalation', f"Security risk escalation detected with {app_name}"
        
        security_tools_per_hour = features.get('security_tools_per_hour', 0)
        if security_tools_per_hour > 3:
            return 'attack_preparation', f"Multiple security tools used: {security_tools_per_hour} tools in 1 hour"
        
        # Default classification for any remaining anomalies
        return 'behavioral_anomaly', f"Unusual behavior pattern detected for {app_name} at {timestamp.strftime('%H:%M')}"
    
    def _is_weekend_normal(self) -> bool:
        """Check if weekend activity is normal based on historical patterns."""
        patterns = self.feature_extractor.usage_patterns
        weekend_usage = patterns.get('weekend_usage', {})
        weekday_usage = patterns.get('weekday_usage', {})
        
        weekend_events = weekend_usage.get('event_count', 0)
        weekday_events = weekday_usage.get('event_count', 0)
        
        # If weekend activity is less than 20% of weekday activity, it's unusual
        if weekday_events > 0:
            weekend_ratio = weekend_events / weekday_events
            return weekend_ratio > 0.2
        
        return True  # Default to normal if no data
    
    def update_model(self, new_events: List[Dict], retrain_threshold: int = 100):
        """
        Update model with new events if enough data accumulated.
        
        Args:
            new_events: New events to potentially include in training
            retrain_threshold: Minimum new events before retraining
        """
        if len(new_events) < retrain_threshold:
            return
        
        logging.info(f"Retraining model with {len(new_events)} new events")
        
        # Get existing training data if possible and combine with new data
        # For simplicity, just retrain on new data (in production, you'd want to combine)
        self.train(new_events, force_retrain=True)
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and information."""
        return {
            'is_trained': self.isolation_forest is not None,
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'training_info': self.training_info,
            'anomaly_thresholds': self.anomaly_thresholds,
            'model_path': str(self.model_path)
        }
    
    def explain_prediction(self, event: Dict) -> Dict[str, Any]:
        """
        Provide explanation for a prediction (for debugging/transparency).
        
        Args:
            event: Event to explain
            
        Returns:
            Explanation dictionary
        """
        if not self.isolation_forest:
            return {'error': 'Model not trained'}
        
        try:
            # Extract features
            df = self.feature_extractor.extract_event_features([event])
            if df.empty:
                return {'error': 'Could not extract features'}
            
            X, _ = self.feature_extractor.prepare_features_for_ml(df)
            if X.size == 0:
                return {'error': 'No ML features available'}
            
            X_scaled = self.scaler.transform(X)
            score = self.isolation_forest.decision_function(X_scaled)[0]
            prediction = self.isolation_forest.predict(X_scaled)[0]
            
            # Get feature values
            feature_values = dict(zip(self.feature_names, X[0]))
            
            explanation = {
                'event_id': event['id'],
                'anomaly_score': float(score),
                'is_anomaly': prediction == -1,
                'severity': self._calculate_severity(score),
                'feature_values': feature_values,
                'thresholds': self.anomaly_thresholds
            }
            
            return explanation
            
        except Exception as e:
            return {'error': str(e)}
