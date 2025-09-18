#!/usr/bin/env python3
"""
Dynamic Trust Scoring System for Zero Trust Architecture
Implements continuous behavioral trust assessment with real-time adjustments.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from .database import BehaviorDatabase

class TrustScorer:
    """
    Dynamic trust scoring system that evaluates user behavior continuously.
    
    Score Rules:
    - Initialization: Starts at neutral score (70/100)
    - Increase: Consistent, verified behavior gradually increases toward 100
    - Decrease: Anomalies decrease score proportionally to severity
    - Thresholds: >80=High trust, 40-80=Medium trust, <40=Low trust (potential intrusion)
    """
    
    def __init__(self, db: BehaviorDatabase, initial_score: float = 70.0):
        """Initialize trust scorer with neutral starting score of 70."""
        self.db = db
        self.initial_score = initial_score
        self.min_score = 0.0
        self.max_score = 100.0
        
        # Trust level thresholds
        self.high_trust_threshold = 80.0    # Above 80: High trust, minimal friction
        self.medium_trust_threshold = 40.0  # 40-80: Medium trust, adaptive friction
        self.low_trust_threshold = 40.0     # Below 40: Low trust, assume potential intrusion
        
        # Scoring adjustment parameters
        self.positive_increment = 2.0       # Gradual increase for normal behavior
        self.recovery_rate = 1.0           # Slower recovery than deduction
        self.max_positive_per_cycle = 5.0  # Maximum increase per evaluation
        
        # Severity-based deductions (matching your specification)
        self.severity_deductions = {
            'low': 8,       # Slight deviations: -5 to -10
            'medium': 20,   # Unusual but not clearly malicious: -20
            'high': 40      # Strong indicators of intrusion/violation: -40+
        }
        
        # Get or create current score
        self.current_score = self._get_or_create_initial_score()
        
        logging.info(f"Trust scorer initialized with score: {self.current_score}")
        
    def _get_or_create_initial_score(self) -> float:
        """Get current trust score from database or create initial neutral score."""
        current = self.db.get_current_trust_score()
        
        if current is None:
            # No existing score, create initial neutral score
            self.db.add_trust_score(
                score=self.initial_score,
                previous_score=self.initial_score,
                change_reason="Session initialized with neutral trust score (70/100)"
            )
            return self.initial_score
            
        return float(current)
        
    def get_trust_level(self, score: Optional[float] = None) -> str:
        """Get trust level category based on score."""
        if score is None:
            score = self.current_score
            
        if score >= self.high_trust_threshold:
            return "HIGH"
        elif score >= self.medium_trust_threshold:
            return "MEDIUM"  
        else:
            return "LOW"
            
    def get_trust_status(self) -> Dict[str, Any]:
        """Get comprehensive trust status."""
        trust_level = self.get_trust_level()
        
        # Determine risk level and response
        if trust_level == "HIGH":
            risk_level = "MINIMAL"
            response = "Continue normal monitoring"
        elif trust_level == "MEDIUM":
            risk_level = "MODERATE"
            response = "Enable adaptive friction (MFA, re-auth, step-up verification)"
        else:
            risk_level = "HIGH"
            response = "POTENTIAL INTRUSION - Alert, restrict access, terminate session"
            
        return {
            'current_score': round(self.current_score, 1),
            'trust_level': trust_level,
            'risk_level': risk_level,
            'recommended_response': response,
            'last_updated': datetime.now().isoformat(),
            'session_state': "safe" if trust_level == "HIGH" else "caution" if trust_level == "MEDIUM" else "danger"
        }
        
    def process_normal_behavior(self, event_count: int = 1) -> Dict[str, Any]:
        """
        Process normal, expected behavior to gradually increase trust score.
        
        Args:
            event_count: Number of normal events processed
            
        Returns:
            Trust score update summary
        """
        if self.current_score >= self.max_score:
            return self._create_update_summary(self.current_score, "Already at maximum trust")
            
        previous_score = self.current_score
        
        # Calculate gradual increase based on consistent behavior
        increase = min(
            self.positive_increment * event_count,
            self.max_positive_per_cycle,
            self.max_score - self.current_score
        )
        
        self.current_score = min(self.current_score + increase, self.max_score)
        
        # Record the change
        change_reason = f"Normal behavior pattern: +{increase:.1f} points"
        self.db.add_trust_score(
            score=self.current_score,
            previous_score=previous_score,
            change_reason=change_reason
        )
        
        return self._create_update_summary(previous_score, change_reason)
        
    def process_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process detected anomalies and update trust score with appropriate deductions.
        
        Args:
            anomalies: List of detected anomalies with severity information
            
        Returns:
            Trust score update summary
        """
        if not anomalies:
            return self.process_normal_behavior()
            
        previous_score = self.current_score
        total_deduction = 0
        anomaly_details = []
        
        for anomaly in anomalies:
            severity = self._determine_anomaly_severity(anomaly)
            deduction = self.severity_deductions.get(severity, 5)
            total_deduction += deduction
            
            anomaly_details.append({
                'type': anomaly.get('anomaly_type', 'unknown'),
                'severity': severity,
                'deduction': deduction,
                'description': anomaly.get('description', 'Anomaly detected')
            })
            
            # Log anomaly in database
            self.db.add_anomaly(
                event_id=anomaly.get('event_id'),
                anomaly_type=anomaly.get('anomaly_type', 'behavioral_anomaly'),
                severity=self._severity_to_float(severity),
                description=anomaly.get('description', 'Behavioral anomaly detected'),
                metadata=anomaly.get('metadata', {})
            )
            
        # Apply total deduction
        self.current_score = max(self.current_score - total_deduction, self.min_score)
        
        # Record the change
        change_reason = f"Anomalies detected: -{total_deduction} points ({len(anomalies)} anomalies)"
        self.db.add_trust_score(
            score=self.current_score,
            previous_score=previous_score,
            change_reason=change_reason,
            anomaly_data={'anomalies': anomaly_details, 'total_deduction': total_deduction}
        )
        
        # Log security alert if score drops to dangerous levels
        if self.current_score < self.low_trust_threshold:
            logging.critical(f"SECURITY ALERT: Trust score dropped to {self.current_score:.1f} - Potential intrusion detected!")
        elif self.current_score < self.medium_trust_threshold:
            logging.warning(f"Trust score dropped to {self.current_score:.1f} - Enabling adaptive friction")
            
        return self._create_update_summary(previous_score, change_reason, anomaly_details)
        
    def _determine_anomaly_severity(self, anomaly: Dict[str, Any]) -> str:
        """Determine severity level of an anomaly."""
        severity_score = anomaly.get('severity', 0.3)
        anomaly_type = anomaly.get('anomaly_type', '').lower()
        
        # High severity indicators
        high_severity_indicators = [
            'malware', 'trojan', 'backdoor', 'keylogger', 'rootkit',
            'data_exfiltration', 'privilege_escalation', 'security_breach',
            'unauthorized_access', 'intrusion'
        ]
        
        # Medium severity indicators  
        medium_severity_indicators = [
            'network_flooding', 'connection_flooding', 'suspicious_app',
            'unknown_application', 'rapid_switching', 'unusual_time'
        ]
        
        # Check for explicit high severity
        if (severity_score >= 0.8 or 
            any(indicator in anomaly_type for indicator in high_severity_indicators)):
            return 'high'
            
        # Check for explicit medium severity
        elif (severity_score >= 0.5 or 
              any(indicator in anomaly_type for indicator in medium_severity_indicators)):
            return 'medium'
            
        # Default to low severity
        else:
            return 'low'
            
    def _severity_to_float(self, severity: str) -> float:
        """Convert severity level to float for database storage."""
        severity_map = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.9
        }
        return severity_map.get(severity, 0.3)
        
    def _create_update_summary(self, previous_score: float, change_reason: str, 
                             anomaly_details: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a comprehensive update summary."""
        trust_status = self.get_trust_status()
        
        return {
            'previous_score': round(previous_score, 1),
            'new_score': round(self.current_score, 1),
            'change': round(self.current_score - previous_score, 1),
            'change_reason': change_reason,
            'trust_level': trust_status['trust_level'],
            'risk_level': trust_status['risk_level'],
            'session_state': trust_status['session_state'],
            'recommended_response': trust_status['recommended_response'],
            'anomaly_details': anomaly_details or [],
            'timestamp': datetime.now().isoformat()
        }
        
    def recover_trust_gradually(self, time_minutes: int = 30) -> Dict[str, Any]:
        """
        Gradually recover trust score over time with good behavior.
        Recovery is intentionally slower than deduction.
        
        Args:
            time_minutes: Minutes of consistent good behavior
            
        Returns:
            Recovery summary
        """
        if self.current_score >= self.max_score:
            return self._create_update_summary(self.current_score, "Already at maximum trust")
            
        previous_score = self.current_score
        
        # Recovery is slower than positive behavior (punishment persistence)
        recovery_amount = min(
            self.recovery_rate * (time_minutes / 30),  # Scale by time
            self.max_score - self.current_score
        )
        
        self.current_score = min(self.current_score + recovery_amount, self.max_score)
        
        change_reason = f"Gradual trust recovery: +{recovery_amount:.1f} points over {time_minutes}min"
        self.db.add_trust_score(
            score=self.current_score,
            previous_score=previous_score,
            change_reason=change_reason
        )
        
        return self._create_update_summary(previous_score, change_reason)
        
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session trust summary."""
        history = self.db.get_trust_history(hours=24)
        recent_anomalies = self.db.get_recent_anomalies(hours=24)
        
        return {
            'current_status': self.get_trust_status(),
            'session_start_score': self.initial_score,
            'score_changes': len(history),
            'anomaly_count': len(recent_anomalies),
            'lowest_score_24h': min([h.get('score', self.current_score) for h in history]) if history else self.current_score,
            'trust_history': history[-10:] if history else []  # Last 10 changes
        }
