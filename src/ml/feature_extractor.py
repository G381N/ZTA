"""
Feature extraction for behavioral monitoring.
Extracts meaningful features from raw events for ML analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging

class FeatureExtractor:
    """Extract features from raw behavioral events for anomaly detection."""
    
    def __init__(self):
        # Track known applications for anomaly detection
        self.known_applications = set()
        # Track normal usage patterns
        self.usage_patterns = {}
        
    def extract_event_features(self, events: List[Dict]) -> pd.DataFrame:
        """
        Extract features from a list of events.
        
        Args:
            events: List of event dictionaries from database
            
        Returns:
            DataFrame with extracted features
        """
        if not events:
            return pd.DataFrame()
        
        features = []
        
        for event in events:
            try:
                timestamp = pd.to_datetime(event['timestamp'])
                
                # Basic temporal features
                feature_dict = {
                    'event_id': event['id'],
                    'timestamp': timestamp,
                    'event_type': event['event_type'],
                    'app_name': event.get('app_name', 'unknown'),
                    
                    # Time-based features
                    'hour_of_day': timestamp.hour,
                    'minute_of_hour': timestamp.minute,
                    'day_of_week': timestamp.weekday(),
                    'is_weekend': timestamp.weekday() >= 5,
                    'is_workday': timestamp.weekday() < 5,
                    
                    # Time period classifications
                    'is_morning': 6 <= timestamp.hour < 12,
                    'is_afternoon': 12 <= timestamp.hour < 18,
                    'is_evening': 18 <= timestamp.hour < 22,
                    'is_night': timestamp.hour >= 22 or timestamp.hour < 6,
                    
                    # Working hours classification (9-17 weekdays)
                    'is_work_hours': (timestamp.weekday() < 5 and 
                                    9 <= timestamp.hour < 17),
                    
                    # Late night / early morning flags
                    'is_very_late': timestamp.hour >= 23 or timestamp.hour < 5,
                    'is_very_early': 5 <= timestamp.hour < 7,
                    
                    # Enhanced unusual time detection
                    'is_highly_unusual_hour': timestamp.hour in [2, 3, 4],  # Most unusual hours
                    'is_unusual_weekend_work': (timestamp.weekday() >= 5 and 
                                              9 <= timestamp.hour < 17),  # Weekend work hours
                    'is_unusual_weekday_night': (timestamp.weekday() < 5 and 
                                                timestamp.hour >= 23),  # Late weekday activity
                }
                
                # Application-specific features (enhanced sensitivity)
                if event['app_name']:
                    app_name = event['app_name'].lower()
                    
                    # Enhanced categorize applications (more comprehensive)
                    feature_dict.update({
                        'is_browser': any(browser in app_name for browser in 
                                        ['firefox', 'chrome', 'chromium', 'safari', 'edge', 'opera', 'brave']),
                        'is_ide': any(ide in app_name for ide in 
                                    ['code', 'pycharm', 'intellij', 'sublime', 'atom', 'vim', 'nano', 'emacs', 'geany']),
                        'is_terminal': any(term in app_name for term in 
                                         ['terminal', 'bash', 'zsh', 'gnome-terminal', 'konsole', 'xterm', 'terminator']),
                        'is_media': any(media in app_name for media in 
                                      ['vlc', 'spotify', 'youtube', 'music', 'video', 'totem', 'rhythmbox']),
                        'is_office': any(office in app_name for office in 
                                       ['libreoffice', 'word', 'excel', 'powerpoint', 'calc', 'writer', 'impress']),
                        'is_social': any(social in app_name for social in 
                                       ['discord', 'slack', 'telegram', 'whatsapp', 'teams', 'zoom', 'skype']),
                        'is_system': any(sys_app in app_name for sys_app in 
                                       ['systemd', 'kernel', 'dbus', 'udev', 'pulseaudio', 'networkmanager']),
                        
                        # NEW: Security tool detection
                        'is_security_tool': any(sec in app_name for sec in 
                                              ['nmap', 'wireshark', 'metasploit', 'burp', 'hydra', 'aircrack', 'john']),
                        
                        # NEW: Network tool detection  
                        'is_network_tool': any(net in app_name for net in 
                                             ['netcat', 'nc', 'ssh', 'telnet', 'ftp', 'wget', 'curl', 'ping']),
                        
                        # NEW: System admin tool detection
                        'is_admin_tool': any(admin in app_name for admin in 
                                           ['sudo', 'su', 'gparted', 'systemctl', 'service', 'mount']),
                        
                        # NEW: Suspicious tool detection (Enhanced)
                        'is_suspicious_tool': any(sus in app_name for sus in 
                                                ['keylog', 'rootkit', 'backdoor', 'trojan', 'virus', 'malware',
                                                 'metasploit', 'armitage', 'beef', 'burp', 'sqlmap', 'nikto',
                                                 'dirb', 'gobuster', 'hydra', 'john', 'hashcat', 'aircrack',
                                                 'wireshark', 'ettercap', 'nessus', 'openvas', 'masscan',
                                                 'zmap', 'responder', 'mimikatz', 'cobalt', 'empire']),
                        
                        # NEW: Browser-based security tool detection
                        'is_browser_security_tool': any(tool in app_name for tool in
                                                       ['kali', 'parrot', 'blackarch', 'pentoo']),
                    })
                    
                    # Enhanced new application detection
                    feature_dict['is_new_app'] = app_name not in self.known_applications
                    feature_dict['app_rarity'] = self._calculate_app_rarity(app_name)
                    self.known_applications.add(app_name)
                
                # Enhanced metadata features (network & security)
                metadata = event.get('metadata', {})
                if isinstance(metadata, dict):
                    feature_dict.update({
                        'has_metadata': True,
                        'cpu_percent': metadata.get('cpu_percent', 0),
                        'memory_percent': metadata.get('memory_percent', 0),
                        'session_duration': self._parse_duration(
                            metadata.get('session_duration_minutes', 0)
                        ),
                        
                        # NEW: Network-related features
                        'remote_ip': metadata.get('remote_ip', ''),
                        'remote_port': metadata.get('remote_port', 0),
                        'is_suspicious_ip': metadata.get('is_suspicious_ip', False),
                        'connection_count': metadata.get('connection_count', 0),
                        'bytes_sent_rate': metadata.get('bytes_sent_rate', 0),
                        'bytes_recv_rate': metadata.get('bytes_recv_rate', 0),
                        
                        # NEW: App launch frequency features
                        'app_launch_count_hour': metadata.get('app_launch_count_hour', 0),
                        'app_launch_count_day': metadata.get('app_launch_count_day', 0),
                        'is_unusual_app': metadata.get('is_unusual_app', False),
                        'is_high_frequency': metadata.get('is_high_frequency', False),
                        
                        # NEW: Security features
                        'risk_level': metadata.get('risk_level', 'low'),
                        'suspicious_keyword': metadata.get('suspicious_keyword', ''),
                        'launches_per_minute': metadata.get('launches_per_minute', 0),
                        'unique_ips': metadata.get('unique_ips', 0),
                        'port_type': metadata.get('port_type', ''),
                    })
                    
                    # Convert risk level to numeric
                    risk_mapping = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
                    feature_dict['risk_level_numeric'] = risk_mapping.get(
                        feature_dict['risk_level'], 0
                    )
                    
                    # Network pattern features
                    feature_dict.update({
                        'is_high_bandwidth': (feature_dict['bytes_sent_rate'] > 1024*1024 or 
                                            feature_dict['bytes_recv_rate'] > 1024*1024),
                        'is_suspicious_port': feature_dict['remote_port'] in {22, 23, 135, 139, 445, 1433, 3389, 5432},
                        'is_high_frequency_app': feature_dict['app_launch_count_hour'] > 5,
                        'is_flooding_behavior': feature_dict['launches_per_minute'] > 15,
                    })
                else:
                    feature_dict['has_metadata'] = False
                
                features.append(feature_dict)
                
            except Exception as e:
                logging.error(f"Error extracting features from event {event.get('id')}: {e}")
                continue
        
        df = pd.DataFrame(features)
        
        # Add sequential features (enhanced)
        if len(df) > 1:
            df = self._add_sequential_features(df)
            df = self._add_network_patterns(df)
            df = self._add_security_patterns(df)
        
        return df
    
    def _calculate_app_rarity(self, app_name):
        """Calculate how rare/common an application is (0=common, 1=very rare)."""
        if not hasattr(self, 'app_usage_counts'):
            self.app_usage_counts = {}
        
        self.app_usage_counts[app_name] = self.app_usage_counts.get(app_name, 0) + 1
        
        # Calculate rarity based on usage frequency
        total_apps = sum(self.app_usage_counts.values())
        app_frequency = self.app_usage_counts[app_name] / max(total_apps, 1)
        
        # Convert frequency to rarity (inverse)
        if app_frequency > 0.1:  # Very common (>10% of usage)
            return 0.1
        elif app_frequency > 0.05:  # Common (>5% of usage)
            return 0.3
        elif app_frequency > 0.01:  # Uncommon (>1% of usage)
            return 0.6
        else:  # Rare (<1% of usage)
            return 1.0
    
    def _add_sequential_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features based on sequences and patterns."""
        df = df.sort_values('timestamp').copy()
        
        # Time between events
        df['time_since_last'] = df['timestamp'].diff().dt.total_seconds() / 60  # minutes
        df['time_since_last'] = df['time_since_last'].fillna(0)
        
        # Application switching patterns
        df['app_switched'] = (df['app_name'] != df['app_name'].shift(1)).astype(int)
        
        # Rapid application launching (multiple apps in short time)
        df['apps_in_5min'] = df.groupby(
            df['timestamp'].dt.floor('5min')
        )['app_name'].transform('nunique')
        
        # Session patterns (enhanced)
        df['events_in_hour'] = df.groupby(
            [df['timestamp'].dt.floor('h'), 'event_type']  # Fixed deprecation warning
        ).transform('size')
        
        # NEW: Network connection patterns
        df['network_events_in_5min'] = df[df['event_type'].str.contains('network', na=False)].groupby(
            df['timestamp'].dt.floor('5min')
        ).transform('size').fillna(0)
        
        # NEW: Security event patterns
        df['security_events_in_hour'] = df[df['event_type'].str.contains('suspicious|high_frequency|flooding', na=False)].groupby(
            df['timestamp'].dt.floor('h')
        ).transform('size').fillna(0)
        
        return df
    
    def _add_network_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add network-specific pattern features."""
        df = df.copy()
        
        # Network connection frequency
        df['connections_per_hour'] = df.groupby(
            df['timestamp'].dt.floor('h')
        )['connection_count'].transform('sum')
        
        # Bandwidth usage patterns
        df['avg_bandwidth_5min'] = (df['bytes_sent_rate'] + df['bytes_recv_rate']).rolling(
            window=5, min_periods=1
        ).mean()
        
        # Suspicious IP patterns
        df['suspicious_ip_count'] = df.groupby(
            df['timestamp'].dt.floor('10min')
        )['is_suspicious_ip'].transform('sum')
        
        # Port usage patterns
        df['unique_ports_per_hour'] = df.groupby(
            df['timestamp'].dt.floor('h')
        )['remote_port'].transform('nunique')
        
        return df
    
    def _add_security_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add security-specific pattern features."""
        df = df.copy()
        
        # Risk escalation patterns
        df['risk_escalation'] = (df['risk_level_numeric'] > df['risk_level_numeric'].shift(1)).astype(int)
        
        # Suspicious tool usage frequency
        df['security_tools_per_hour'] = df.groupby(
            df['timestamp'].dt.floor('h')
        )['is_security_tool'].transform('sum')
        
        # Admin tool usage patterns
        df['admin_tools_per_hour'] = df.groupby(
            df['timestamp'].dt.floor('h')
        )['is_admin_tool'].transform('sum')
        
        # Application diversity (more apps = potentially more suspicious)
        df['app_diversity_10min'] = df.groupby(
            df['timestamp'].dt.floor('10min')
        )['app_name'].transform('nunique')
        
        return df
    
    def _parse_duration(self, duration_value: Any) -> float:
        """Parse duration value safely."""
        try:
            return float(duration_value)
        except (TypeError, ValueError):
            return 0.0
    
    def extract_usage_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract usage patterns from historical data for anomaly detection baseline.
        
        Args:
            df: DataFrame with extracted features
            
        Returns:
            Dictionary with usage patterns
        """
        if df.empty:
            return {}
        
        patterns = {}
        
        try:
            # Most common usage hours
            hour_counts = df['hour_of_day'].value_counts()
            patterns['common_hours'] = hour_counts.head(8).index.tolist()
            patterns['rare_hours'] = hour_counts.tail(4).index.tolist()
            
            # Most common applications
            if 'app_name' in df.columns:
                app_counts = df[df['app_name'] != 'unknown']['app_name'].value_counts()
                patterns['common_apps'] = app_counts.head(10).index.tolist()
                patterns['rare_apps'] = app_counts.tail(5).index.tolist()
                
                # Application usage by time
                patterns['apps_by_hour'] = {}
                for hour in range(24):
                    hour_apps = df[df['hour_of_day'] == hour]['app_name'].value_counts().head(3).index.tolist()
                    patterns['apps_by_hour'][hour] = hour_apps
            
            # Weekend vs weekday patterns
            patterns['weekend_usage'] = {
                'event_count': len(df[df['is_weekend']]),
                'common_hours': df[df['is_weekend']]['hour_of_day'].value_counts().head(5).index.tolist(),
                'common_apps': df[df['is_weekend']]['app_name'].value_counts().head(5).index.tolist()
            }
            
            patterns['weekday_usage'] = {
                'event_count': len(df[~df['is_weekend']]),
                'common_hours': df[~df['is_weekend']]['hour_of_day'].value_counts().head(5).index.tolist(),
                'common_apps': df[~df['is_weekend']]['app_name'].value_counts().head(5).index.tolist()
            }
            
            # Activity intensity patterns
            hourly_activity = df.groupby('hour_of_day').size()
            patterns['peak_activity_hours'] = hourly_activity.nlargest(3).index.tolist()
            patterns['low_activity_hours'] = hourly_activity.nsmallest(3).index.tolist()
            
            # Application category usage
            categories = ['is_browser', 'is_ide', 'is_terminal', 'is_media', 'is_office', 'is_social']
            for cat in categories:
                if cat in df.columns:
                    cat_usage = df[df[cat]]['hour_of_day'].value_counts()
                    if not cat_usage.empty:
                        patterns[f'{cat}_common_hours'] = cat_usage.head(3).index.tolist()
            
            # Time patterns
            patterns['avg_session_duration'] = df['session_duration'].mean() if 'session_duration' in df.columns else 0
            patterns['total_events'] = len(df)
            patterns['unique_apps'] = df['app_name'].nunique()
            
            # Update internal patterns for anomaly detection
            self.usage_patterns = patterns
            
        except Exception as e:
            logging.error(f"Error extracting usage patterns: {e}")
            patterns = {}
        
        return patterns
    
    def prepare_features_for_ml(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features for machine learning model.
        
        Args:
            df: DataFrame with extracted features
            
        Returns:
            Tuple of (feature matrix, feature names)
        """
        if df.empty:
            return np.array([]), []
        
        # Select numerical and categorical features for ML (enhanced)
        ml_features = [
            # Time features
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_workday',
            'is_morning', 'is_afternoon', 'is_evening', 'is_night',
            'is_work_hours', 'is_very_late', 'is_very_early',
        ]
        
        # Enhanced application category features
        app_features = [
            'is_browser', 'is_ide', 'is_terminal', 'is_media', 
            'is_office', 'is_social', 'is_system', 'is_new_app',
            # NEW security features
            'is_security_tool', 'is_network_tool', 'is_admin_tool', 'is_suspicious_tool',
            'app_rarity'
        ]
        
        for feature in app_features:
            if feature in df.columns:
                ml_features.append(feature)
        
        # Enhanced sequential features
        seq_features = [
            'time_since_last', 'app_switched', 'apps_in_5min', 'events_in_hour',
            # NEW network patterns
            'network_events_in_5min', 'security_events_in_hour', 'connections_per_hour',
            # NEW security patterns  
            'risk_escalation', 'security_tools_per_hour', 'admin_tools_per_hour',
            'app_diversity_10min'
        ]
        for feature in seq_features:
            if feature in df.columns:
                ml_features.append(feature)
        
        # Enhanced metadata features
        meta_features = [
            'cpu_percent', 'memory_percent', 'session_duration',
            # NEW network features
            'connection_count', 'bytes_sent_rate', 'bytes_recv_rate',
            'suspicious_ip_count', 'unique_ports_per_hour', 'avg_bandwidth_5min',
            # NEW app frequency features
            'app_launch_count_hour', 'app_launch_count_day', 'launches_per_minute',
            # NEW security features  
            'risk_level_numeric', 'unique_ips',
            # NEW pattern flags
            'is_high_bandwidth', 'is_suspicious_port', 'is_high_frequency_app', 
            'is_flooding_behavior', 'is_unusual_app', 'is_high_frequency'
        ]
        for feature in meta_features:
            if feature in df.columns:
                ml_features.append(feature)
        
        # Filter features that exist in DataFrame
        available_features = [f for f in ml_features if f in df.columns]
        
        if not available_features:
            return np.array([]), []
        
        # Extract feature matrix
        X = df[available_features].fillna(0).astype(float).values
        
        return X, available_features
    
    def get_feature_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics of extracted features."""
        if df.empty:
            return {}
        
        summary = {
            'total_events': len(df),
            'unique_applications': df['app_name'].nunique(),
            'time_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat(),
                'duration_hours': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
            },
            'hourly_distribution': df['hour_of_day'].value_counts().to_dict(),
            'weekday_distribution': df['day_of_week'].value_counts().to_dict(),
            'weekend_ratio': df['is_weekend'].mean(),
            'work_hours_ratio': df['is_work_hours'].mean() if 'is_work_hours' in df.columns else 0,
        }
        
        # Application category distribution
        app_categories = ['is_browser', 'is_ide', 'is_terminal', 'is_media', 'is_office', 'is_social']
        for cat in app_categories:
            if cat in df.columns:
                summary[f'{cat}_ratio'] = df[cat].mean()
        
        return summary
