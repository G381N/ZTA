"""
Dynamic trust scoring system for behavioral monitoring.
Manages trust scores based on anomaly detection results.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from .database import BehaviorDatabase

class TrustScorer:
    """Dynamic trust scoring system that adjusts based on behavioral anomalies."""
    
    def __init__(self, db: BehaviorDatabase, initial_score: int = 100):
        self.db = db
        self.initial_score = initial_score
        
        # Trust score parameters
        self.min_score = 0
        self.max_score = 100
        
        # Enhanced scoring rules with network and security focus
        self.severity_penalties = {
            0.95: 30,  # Critical severity (malware, data exfiltration)
            0.85: 25,  # Very high severity (security tools, privilege escalation)
            0.75: 20,  # High severity (network anomalies, suspicious connections)
            0.60: 15,  # Medium-high severity (rapid patterns, flooding)
            0.45: 10,  # Medium severity (unusual apps, time patterns)
            0.30: 5,   # Low-medium severity (minor anomalies)
            0.15: 2,   # Low severity (slight deviations)
            0.05: 1    # Very low severity (barely unusual)
        }
        
        # Recovery parameters (slightly reduced for security focus)
        self.recovery_rate = 0.8  # Slower recovery for security incidents
        self.max_recovery_per_cycle = 3  # Reduced maximum recovery
        
        # Alert thresholds
        self.alert_thresholds = {
            'critical': 40,  # Critical alert
            'warning': 60,   # Warning alert
            'info': 80       # Info alert
        }
        
        # Initialize current score
        self.current_score = self._get_or_create_initial_score()
        
        logging.info(f"Trust scorer initialized with score: {self.current_score}")
    
    def _get_or_create_initial_score(self) -> int:
        """Get current trust score from database or create initial score."""
        current = self.db.get_current_trust_score()
        
        if current is None:
            # No existing score, create initial score
            self.db.add_trust_score(
                score=self.initial_score,
                change_reason="Initial trust score"
            )
            return self.initial_score
        
        return current
    
    def process_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process detected anomalies and update trust score accordingly.
        
        Args:
            anomalies: List of anomaly detection results
            
        Returns:
            Trust score update summary
        """
        if not anomalies:
            return self._process_normal_behavior()
        
        previous_score = self.current_score
        total_penalty = 0
        anomaly_details = []
        
        for anomaly in anomalies:
            penalty = self._calculate_penalty(anomaly)
            total_penalty += penalty
            
            # Log the anomaly in database
            anomaly_id = self.db.add_anomaly(
                event_id=anomaly['event_id'],
                anomaly_type=anomaly['anomaly_type'],
                severity=anomaly['severity'],
                description=anomaly['description'],
                metadata=anomaly.get('metadata', {})
            )
            
            anomaly_details.append({
                'anomaly_id': anomaly_id,
                'type': anomaly['anomaly_type'],
                'severity': anomaly['severity'],
                'penalty': penalty,
                'description': anomaly['description']
            })
            
            logging.warning(f"Applied penalty of {penalty} points for {anomaly['anomaly_type']} "
                          f"(severity: {anomaly['severity']:.2f})")
        
        # Apply total penalty
        new_score = max(self.min_score, self.current_score - total_penalty)
        
        # Update trust score in database
        self.db.add_trust_score(
            score=new_score,
            previous_score=previous_score,
            change_reason=f"Anomalies detected: {len(anomalies)} anomalies, penalty: {total_penalty}",
            anomaly_data={
                'anomaly_count': len(anomalies),
                'total_penalty': total_penalty,
                'anomaly_types': [a['anomaly_type'] for a in anomalies],
                'max_severity': max(a['severity'] for a in anomalies)
            }
        )
        
        self.current_score = new_score
        
        # Check for alerts (enhanced with threat types)
        alert_level = self._check_alert_level(new_score, previous_score, 
                                            [a['anomaly_type'] for a in anomalies])
        
        result = {
            'previous_score': previous_score,
            'new_score': new_score,
            'score_change': new_score - previous_score,
            'anomaly_count': len(anomalies),
            'total_penalty': total_penalty,
            'anomaly_details': anomaly_details,
            'alert_level': alert_level,
            'timestamp': datetime.now().isoformat()
        }
        
        if alert_level:
            logging.warning(f"Trust score alert ({alert_level}): Score dropped to {new_score} "
                          f"(was {previous_score})")
        
        return result
    
    def _process_normal_behavior(self) -> Dict[str, Any]:
        """Process normal behavior (no anomalies) and potentially recover trust."""
        previous_score = self.current_score
        
        # Check time since last anomaly
        recent_anomalies = self.db.get_recent_anomalies(hours=1)
        
        if not recent_anomalies and self.current_score < self.max_score:
            # No recent anomalies, allow some recovery
            recovery_points = min(
                self.max_recovery_per_cycle,
                self.recovery_rate,
                self.max_score - self.current_score
            )
            
            if recovery_points > 0:
                new_score = self.current_score + recovery_points
                
                self.db.add_trust_score(
                    score=new_score,
                    previous_score=previous_score,
                    change_reason=f"Trust recovery: {recovery_points} points for normal behavior"
                )
                
                self.current_score = new_score
                
                logging.info(f"Trust score recovered: {recovery_points} points "
                           f"({previous_score} -> {new_score})")
                
                return {
                    'previous_score': previous_score,
                    'new_score': new_score,
                    'score_change': recovery_points,
                    'recovery_points': recovery_points,
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'normal_behavior_recovery'
                }
        
        # No change
        return {
            'previous_score': previous_score,
            'new_score': self.current_score,
            'score_change': 0,
            'timestamp': datetime.now().isoformat(),
            'reason': 'no_change'
        }
    
    def _calculate_penalty(self, anomaly: Dict[str, Any]) -> int:
        """Enhanced penalty calculation for network and security anomalies."""
        severity = anomaly['severity']
        anomaly_type = anomaly['anomaly_type']
        
        # Base penalty based on severity
        base_penalty = 0
        for threshold, penalty in sorted(self.severity_penalties.items(), reverse=True):
            if severity >= threshold:
                base_penalty = penalty
                break
        
        # Enhanced type-specific modifiers for security threats
        type_modifiers = {
            # CRITICAL THREATS (highest penalties)
            'malicious_tool_usage': 2.5,           # Malware/hacking tools
            'data_exfiltration_risk': 2.3,         # High bandwidth + suspicious patterns
            'attack_pattern_detected': 2.2,        # Multiple attack tools used together
            'malicious_port_access': 2.0,          # Direct attack vector access
            'suspicious_late_activity': 1.9,       # Security tools at odd hours
            
            # HIGH RISK THREATS  
            'network_scanning': 1.8,               # Network reconnaissance
            'connection_flooding': 1.7,            # Network flooding attacks
            'suspicious_ip_connection': 1.6,       # Connections to bad IPs
            'privilege_escalation': 1.6,           # Admin tool usage
            'attack_preparation': 1.5,             # Multiple security tools
            'security_tool_usage': 1.5,            # Single security tool usage
            
            # MEDIUM RISK PATTERNS
            'network_flooding': 1.4,               # General network flooding
            'bandwidth_anomaly': 1.3,              # High bandwidth usage
            'suspicious_port_access': 1.3,         # Suspicious port connections
            'network_tool_usage': 1.3,             # Network utility usage
            'app_abuse_pattern': 1.2,              # App launch flooding
            'system_flooding': 1.2,                # System request flooding
            'behavioral_flooding': 1.2,            # General flooding behavior
            
            # LOWER RISK ANOMALIES  
            'unknown_application': 1.1,            # New apps (slightly concerning)
            'rare_application': 1.0,               # Rare apps (normal penalty)
            'unusual_time': 1.0,                   # Time anomalies
            'rapid_switching': 0.9,                # App switching patterns
            'risk_escalation': 0.9,                # Risk level increases
            'critical_system_load': 0.8,           # System performance
            'high_system_load': 0.7,               # System performance
            'unusual_schedule': 0.7,               # Schedule anomalies
            'rapid_activity': 0.6,                 # Rapid user activity
            'suspicious_work_pattern': 0.6,        # Work pattern changes
            'behavioral_anomaly': 0.5              # General behavioral anomalies
        }
        
        modifier = type_modifiers.get(anomaly_type, 1.0)
        penalty = int(base_penalty * modifier)
        
        # Additional severity-based multipliers for critical anomalies
        if anomaly_type in ['malicious_tool_usage', 'data_exfiltration_risk', 'attack_pattern_detected']:
            if severity > 0.9:
                penalty = int(penalty * 1.5)  # Extra penalty for very high severity
        
        # Consider metadata for additional context
        metadata = anomaly.get('metadata', {})
        
        # Network-specific penalty adjustments
        if 'connection_count' in metadata and metadata['connection_count'] > 100:
            penalty = int(penalty * 1.2)  # Extra penalty for many connections
        
        if 'risk_level' in metadata:
            risk_multipliers = {'low': 0.8, 'medium': 1.0, 'high': 1.3, 'critical': 1.6}
            penalty = int(penalty * risk_multipliers.get(metadata['risk_level'], 1.0))
        
        if 'launches_per_hour' in metadata and metadata['launches_per_hour'] > 20:
            penalty = int(penalty * 1.3)  # Extra penalty for excessive app launches
        
        if 'bytes_sent_rate' in metadata:
            # Extra penalty for high data transfer rates (potential exfiltration)
            bytes_per_sec = metadata['bytes_sent_rate']
            if bytes_per_sec > 10 * 1024 * 1024:  # > 10MB/s
                penalty = int(penalty * 1.4)
        
        # Ensure minimum penalty for security-related anomalies
        security_types = [
            'malicious_tool_usage', 'attack_pattern_detected', 'suspicious_ip_connection',
            'malicious_port_access', 'data_exfiltration_risk', 'network_scanning',
            'privilege_escalation', 'security_tool_usage'
        ]
        
        if anomaly_type in security_types:
            penalty = max(3, penalty)  # Minimum 3 points for security threats
        else:
            penalty = max(1, penalty)  # Minimum 1 point for any anomaly
        
        return penalty
    
    def _check_alert_level(self, new_score: int, previous_score: int, anomaly_types: List[str] = None) -> Optional[str]:
        """Enhanced alert level checking with threat-specific triggers."""
        # Check threshold crossings
        for level, threshold in self.alert_thresholds.items():
            if previous_score >= threshold > new_score:
                return level
        
        # Enhanced rapid drop detection
        score_drop = previous_score - new_score
        if score_drop >= 25:  # Very severe drop
            return 'critical'
        elif score_drop >= 15:  # Severe drop
            return 'critical'
        elif score_drop >= 10:  # Significant drop
            return 'warning'
        elif score_drop >= 5:   # Moderate drop
            return 'info'
        
        # Threat-specific alert triggers (regardless of score drop)
        if anomaly_types:
            critical_threats = {
                'malicious_tool_usage', 'data_exfiltration_risk', 'attack_pattern_detected',
                'malicious_port_access', 'network_scanning', 'connection_flooding'
            }
            
            high_threats = {
                'suspicious_ip_connection', 'privilege_escalation', 'attack_preparation',
                'security_tool_usage', 'suspicious_late_activity'
            }
            
            # Trigger critical alert for any critical threat
            if any(threat in critical_threats for threat in anomaly_types):
                return 'critical'
            
            # Trigger warning for multiple high threats
            high_threat_count = sum(1 for threat in anomaly_types if threat in high_threats)
            if high_threat_count >= 2:
                return 'warning'
            elif high_threat_count >= 1:
                return 'info'
        
        return None
    
    def get_trust_status(self) -> Dict[str, Any]:
        """Get current trust status and recent history."""
        # Get recent trust history
        history = self.db.get_trust_history(hours=24)
        recent_anomalies = self.db.get_recent_anomalies(hours=24)
        
        # Calculate statistics
        if history:
            score_changes = [h['score'] - (h['previous_score'] or h['score']) for h in history]
            avg_score = sum(h['score'] for h in history) / len(history)
            min_score_24h = min(h['score'] for h in history)
            max_score_24h = max(h['score'] for h in history)
        else:
            score_changes = []
            avg_score = self.current_score
            min_score_24h = self.current_score
            max_score_24h = self.current_score
        
        # Determine current risk level
        risk_level = self._get_risk_level(self.current_score)
        
        status = {
            'current_score': self.current_score,
            'risk_level': risk_level,
            'score_range': f"{self.min_score}-{self.max_score}",
            
            # 24-hour statistics
            'last_24h': {
                'avg_score': round(avg_score, 1),
                'min_score': min_score_24h,
                'max_score': max_score_24h,
                'score_changes': len(score_changes),
                'total_change': sum(score_changes),
                'anomaly_count': len(recent_anomalies)
            },
            
            # Alert thresholds
            'thresholds': self.alert_thresholds,
            
            # Recent activity summary
            'recent_anomalies': [
                {
                    'type': a['anomaly_type'],
                    'severity': a['severity'],
                    'description': a['description'],
                    'timestamp': a['timestamp']
                }
                for a in recent_anomalies[-5:]  # Last 5 anomalies
            ],
            
            'last_updated': datetime.now().isoformat()
        }
        
        return status
    
    def _get_risk_level(self, score: int) -> str:
        """Determine risk level based on current score."""
        if score <= self.alert_thresholds['critical']:
            return 'HIGH'
        elif score <= self.alert_thresholds['warning']:
            return 'MEDIUM'
        elif score <= self.alert_thresholds['info']:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def force_score_update(self, new_score: int, reason: str) -> Dict[str, Any]:
        """
        Manually update trust score (for testing or administrative purposes).
        
        Args:
            new_score: New trust score (0-100)
            reason: Reason for the manual update
            
        Returns:
            Update result
        """
        new_score = max(self.min_score, min(self.max_score, new_score))
        previous_score = self.current_score
        
        self.db.add_trust_score(
            score=new_score,
            previous_score=previous_score,
            change_reason=f"Manual update: {reason}"
        )
        
        self.current_score = new_score
        
        logging.info(f"Trust score manually updated: {previous_score} -> {new_score} ({reason})")
        
        return {
            'previous_score': previous_score,
            'new_score': new_score,
            'score_change': new_score - previous_score,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_trust_score(self, reason: str = "Trust score reset") -> Dict[str, Any]:
        """Reset trust score to initial value."""
        return self.force_score_update(self.initial_score, reason)
    
    def get_trust_trend(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get trust score trend analysis.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Trend analysis
        """
        history = self.db.get_trust_history(hours=hours)
        
        if len(history) < 2:
            return {
                'trend': 'stable',
                'direction': 'none',
                'confidence': 'low',
                'data_points': len(history)
            }
        
        scores = [h['score'] for h in history]
        
        # Calculate trend
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        trend_change = second_avg - first_avg
        
        if abs(trend_change) < 2:
            trend = 'stable'
            direction = 'none'
        elif trend_change > 0:
            trend = 'improving'
            direction = 'up'
        else:
            trend = 'declining'
            direction = 'down'
        
        # Calculate confidence based on data consistency
        score_variance = np.var(scores) if len(scores) > 1 else 0
        confidence = 'high' if score_variance < 25 else 'medium' if score_variance < 100 else 'low'
        
        return {
            'trend': trend,
            'direction': direction,
            'trend_strength': abs(trend_change),
            'confidence': confidence,
            'data_points': len(history),
            'score_variance': round(score_variance, 2),
            'period_hours': hours
        }
