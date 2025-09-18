"""
Event collector for behavioral monitoring.
Collects application launches and session events.
Optimized for lightweight operation on Kali Linux.
"""

import os
import sys
import time
import psutil
import logging
import threading
import subprocess
from datetime import datetime
from typing import Dict, Set, Optional
from pathlib import Path

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.database import BehaviorDatabase

class EventCollector:
    """Lightweight event collector for system behavioral monitoring."""
    
    def __init__(self):
        self.running = False
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.session_start_time = datetime.now()
        self.db = BehaviorDatabase()
        self.collector_thread = None
        
        # Initialize tracking sets
        self.known_processes = set()
        self.known_applications = set()
        self.check_interval = 2.0
        self.last_activity_check = time.time()
        
        # Initialize metadata collector
        self.last_app_check = time.time()
        self.app_check_interval = 2.0  # Check every 2 seconds
        
        # Network monitoring state
        self.network_baseline = {}
        self.app_network_usage = {}
        self.connection_history = []
        self.suspicious_ips = set()
        self.last_network_check = time.time()
        self.network_check_interval = 1.0  # Check network every second
        
        # Application launch tracking
        self.app_launch_counts = {}
        self.app_launch_history = []
        self.unusual_apps = set()
        
        # Request pattern tracking
        self.request_patterns = {}
        self.high_frequency_apps = set()
        
        # Initialize known processes
        self._initialize_known_processes()
        
        logging.info(f"Event collector initialized with session ID: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    
    def _initialize_known_processes(self):
        """Initialize the set of currently running processes."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    self.known_processes.add(proc.info['pid'])
                    if proc.info['name']:
                        self.known_applications.add(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logging.error(f"Error initializing known processes: {e}")
    
    def _get_application_name(self, proc) -> Optional[str]:
        """Extract meaningful application name from process."""
        try:
            name = proc.info['name']
            if not name:
                return None
                
            # Filter out system processes and get meaningful names
            if name in ['systemd', 'kthreadd', 'ksoftirqd', 'migration', 'rcu_', 'watchdog']:
                return None
            
            # Clean up common patterns
            if name.endswith('.py'):
                return name[:-3]
            
            # Get more detailed info for GUI applications
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and len(cmdline) > 0:
                    # Look for common application patterns
                    for cmd_part in cmdline:
                        if any(gui_hint in cmd_part.lower() for gui_hint in 
                               ['firefox', 'chrome', 'code', 'terminal', 'nautilus', 'gedit']):
                            return cmd_part.split('/')[-1]
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            return name
            
        except Exception:
            return None
    
    def _detect_new_applications(self):
        """Detect newly launched applications."""
        current_processes = set()
        new_applications = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    pid = proc.info['pid']
                    current_processes.add(pid)
                    
                    # Check if this is a new process
                    if pid not in self.known_processes:
                        app_name = self._get_application_name(proc)
                        
                        if app_name and app_name not in self.known_applications:
                            # This is a new application launch
                            create_time = datetime.fromtimestamp(proc.info['create_time'])
                            
                            # Only log if it's recent (within last check interval + buffer)
                            time_diff = (datetime.now() - create_time).total_seconds()
                            if time_diff <= self.check_interval + 2:
                                new_applications.append({
                                    'app_name': app_name,
                                    'pid': pid,
                                    'create_time': create_time,
                                    'cmdline': ' '.join(proc.info.get('cmdline', [])[:3])  # First 3 parts only
                                })
                                
                                self.known_applications.add(app_name)
                        
                        self.known_processes.add(pid)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logging.error(f"Error detecting new applications: {e}")
        
        # Remove PIDs that no longer exist
        self.known_processes &= current_processes
        
        return new_applications
    
    def _log_session_event(self, event_type: str, metadata: Dict = None):
        """Log session-related events."""
        self.db.add_event(
            event_type=event_type,
            session_id=self.session_id,
            metadata=metadata
        )
    
    def _log_application_event(self, app_name: str, metadata: Dict = None):
        """Log application launch events."""
        event_metadata = {
            'session_id': self.session_id,
            'hour_of_day': datetime.now().hour,
            'weekday': datetime.now().weekday(),
            'is_weekend': datetime.now().weekday() >= 5,
            **(metadata or {})
        }
        
        self.db.add_event(
            event_type='app_launch',
            app_name=app_name,
            session_id=self.session_id,
            metadata=event_metadata
        )
    
    def _check_system_activity(self):
        """Check for system activity and session changes."""
        try:
            # Check CPU and memory usage as indicators of activity
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Check if system seems idle (very low CPU usage)
            is_idle = cpu_percent < 5.0
            
            # Log significant changes
            if hasattr(self, '_last_idle_state') and self._last_idle_state != is_idle:
                state = 'idle' if is_idle else 'active'
                self._log_session_event(f'system_{state}', {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'available_memory_gb': round(memory.available / (1024**3), 2)
                })
            
            self._last_idle_state = is_idle
            self.last_activity_check = datetime.now()
            
        except Exception as e:
            logging.error(f"Error checking system activity: {e}")
    
    def start_session(self):
        """Log session start event."""
        self._log_session_event('session_start', {
            'session_start_time': self.session_start_time.isoformat(),
            'system_info': {
                'python_version': sys.version.split()[0],
                'platform': sys.platform,
                'cpu_count': os.cpu_count()
            }
        })
    
    def end_session(self):
        """Log session end event."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        self._log_session_event('session_end', {
            'session_duration_seconds': session_duration,
            'session_duration_minutes': round(session_duration / 60, 2)
        })
    
    def collect_events(self):
        """Main event collection loop."""
        logging.info("Starting event collection loop")
        
        while self.running:
            try:
                # Collect application events
                current_time = time.time()
                if current_time - self.last_app_check >= self.app_check_interval:
                    self._collect_application_events()
                    self.last_app_check = current_time
                
                # Collect network events (more sensitive)
                if current_time - self.last_network_check >= self.network_check_interval:
                    self._collect_network_events()
                    self._monitor_suspicious_connections()
                    self._detect_request_flooding()
                    self.last_network_check = current_time
                
                time.sleep(0.5)  # More frequent checks
                
            except KeyboardInterrupt:
                logging.info("Event collection interrupted by user")
                break
            except Exception as e:
                logging.error(f"Error in event collection loop: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """Start the event collector in a background thread."""
        if self.running:
            logging.warning("Event collector is already running")
            return
        
        self.running = True
        self.start_session()
        
        self.collector_thread = threading.Thread(target=self.collect_events, daemon=True)
        self.collector_thread.start()
        
        logging.info("Event collector started")
    
    def stop(self):
        """Stop the event collector."""
        if not self.running:
            return
        
        logging.info("Stopping event collector")
        self.running = False
        
        if self.collector_thread and self.collector_thread.is_alive():
            self.collector_thread.join(timeout=5)
        
        self.end_session()
        logging.info("Event collector stopped")
    
    def _collect_application_events(self):
        """Collect and log application launch events with enhanced sensitivity."""
        new_apps = self._detect_new_applications()
        
        for app_data in new_apps:
            app_name = app_data['app_name']
            
            # Track application launches more sensitively
            self._track_app_launch_frequency(app_name)
            
            # Detect unusual application combinations
            self._detect_unusual_app_patterns(app_name)
            
            # Check for known suspicious applications
            self._check_suspicious_applications(app_name)
            
            # Enhanced metadata collection
            enhanced_metadata = {
                'pid': app_data['pid'],
                'cmdline': app_data['cmdline'],
                'create_time': app_data['create_time'].isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'app_launch_count_hour': self.app_launch_counts.get(app_name, {}).get('hour', 0),
                'app_launch_count_day': self.app_launch_counts.get(app_name, {}).get('day', 0),
                'is_unusual_app': app_name in self.unusual_apps,
                'is_high_frequency': app_name in self.high_frequency_apps
            }
            
            self._log_application_event(app_name, enhanced_metadata)
            logging.info(f"Enhanced app launch logged: {app_name}")
    
    def _collect_network_events(self):
        """Collect detailed network traffic and connection events."""
        try:
            # Get network connections
            connections = psutil.net_connections(kind='inet')
            current_time = time.time()
            
            # Track new connections
            active_connections = []
            for conn in connections:
                if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port
                    local_port = conn.laddr.port
                    
                    connection_key = f"{remote_ip}:{remote_port}"
                    active_connections.append(connection_key)
                    
                    # Check if this is a new connection
                    if connection_key not in [c.get('key') for c in self.connection_history[-50:]]:
                        # Log new connection
                        self.db.add_event(
                            event_type="network_connection",
                            app_name="system",
                            session_id=self.session_id,
                            metadata={
                                'remote_ip': remote_ip,
                                'remote_port': remote_port,
                                'local_port': local_port,
                                'connection_status': conn.status,
                                'protocol': 'TCP' if conn.type == 1 else 'UDP',
                                'is_suspicious_ip': remote_ip in self.suspicious_ips,
                                'connection_count': len(active_connections)
                            }
                        )
                        
                        self.connection_history.append({
                            'key': connection_key,
                            'timestamp': current_time,
                            'remote_ip': remote_ip,
                            'remote_port': remote_port
                        })
            
            # Get network I/O statistics
            net_io = psutil.net_io_counters()
            
            # Calculate bandwidth usage if we have a baseline
            if hasattr(self, '_last_net_io'):
                time_diff = current_time - self._last_net_check_time
                bytes_sent_rate = (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_diff
                bytes_recv_rate = (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_diff
                
                # High bandwidth usage threshold (1MB/s)
                if bytes_sent_rate > 1024*1024 or bytes_recv_rate > 1024*1024:
                    self.db.add_event(
                        event_type="high_bandwidth",
                        app_name="network",
                        session_id=self.session_id,
                        metadata={
                            'bytes_sent_rate': bytes_sent_rate,
                            'bytes_recv_rate': bytes_recv_rate,
                            'total_connections': len(active_connections),
                            'packets_sent': net_io.packets_sent,
                            'packets_recv': net_io.packets_recv
                        }
                    )
            
            self._last_net_io = net_io
            self._last_net_check_time = current_time
            
        except Exception as e:
            logging.error(f"Error collecting network events: {e}")
    
    def _monitor_suspicious_connections(self):
        """Monitor for suspicious connection patterns."""
        try:
            recent_connections = [c for c in self.connection_history 
                                if time.time() - c['timestamp'] < 300]  # Last 5 minutes
            
            if len(recent_connections) > 20:  # More than 20 new connections in 5 minutes
                self.db.add_event(
                    event_type="connection_flooding",
                    app_name="network",
                    session_id=self.session_id,
                    metadata={
                        'connection_count': len(recent_connections),
                        'time_window': 300,
                        'unique_ips': len(set(c['remote_ip'] for c in recent_connections)),
                        'most_common_ip': max(set(c['remote_ip'] for c in recent_connections), 
                                            key=lambda ip: sum(1 for c in recent_connections if c['remote_ip'] == ip))
                    }
                )
                logging.warning(f"Connection flooding detected: {len(recent_connections)} connections in 5 minutes")
            
            # Check for connections to suspicious ports
            suspicious_ports = {22, 23, 135, 139, 445, 1433, 3389, 5432}  # Common attack ports
            for conn in recent_connections[-10:]:  # Check last 10 connections
                if conn['remote_port'] in suspicious_ports:
                    self.db.add_event(
                        event_type="suspicious_port_connection",
                        app_name="network",
                        session_id=self.session_id,
                        metadata={
                            'remote_ip': conn['remote_ip'],
                            'remote_port': conn['remote_port'],
                            'port_type': 'high_risk'
                        }
                    )
                    logging.warning(f"Suspicious port connection: {conn['remote_ip']}:{conn['remote_port']}")
                    
        except Exception as e:
            logging.error(f"Error monitoring suspicious connections: {e}")
    
    def _detect_request_flooding(self):
        """Detect high-frequency request patterns."""
        try:
            current_time = time.time()
            
            # Count recent app launches in the last minute
            recent_launches = [a for a in self.app_launch_history 
                             if current_time - a['time'] < 60]
            
            if len(recent_launches) > 15:  # More than 15 app launches per minute
                self.db.add_event(
                    event_type="request_flooding",
                    app_name="system",
                    session_id=self.session_id,
                    metadata={
                        'launches_per_minute': len(recent_launches),
                        'threshold': 15,
                        'unique_apps': len(set(a['app'] for a in recent_launches)),
                        'most_launched_app': max(set(a['app'] for a in recent_launches), 
                                               key=lambda app: sum(1 for a in recent_launches if a['app'] == app))
                    }
                )
                logging.warning(f"App launch flooding detected: {len(recent_launches)} launches in last minute")
                
        except Exception as e:
            logging.error(f"Error detecting request flooding: {e}")
    
    def _track_app_launch_frequency(self, app_name):
        """Track application launch frequency for anomaly detection."""
        current_time = time.time()
        hour_start = current_time - (current_time % 3600)  # Start of current hour
        day_start = current_time - (current_time % 86400)   # Start of current day
        
        if app_name not in self.app_launch_counts:
            self.app_launch_counts[app_name] = {'hour': 0, 'day': 0, 'hour_start': hour_start, 'day_start': day_start}
        
        app_data = self.app_launch_counts[app_name]
        
        # Reset counters if new hour/day
        if hour_start > app_data['hour_start']:
            app_data['hour'] = 0
            app_data['hour_start'] = hour_start
        
        if day_start > app_data['day_start']:
            app_data['day'] = 0
            app_data['day_start'] = day_start
        
        app_data['hour'] += 1
        app_data['day'] += 1
        
        # Check for unusual frequency
        if app_data['hour'] > 5:  # More than 5 launches per hour (more sensitive)
            self.db.add_event(
                event_type="high_frequency_app",
                app_name=app_name,
                session_id=self.session_id,
                metadata={
                    'launches_per_hour': app_data['hour'],
                    'launches_per_day': app_data['day'],
                    'threshold_exceeded': 'hourly'
                }
            )
            self.high_frequency_apps.add(app_name)
            logging.warning(f"High frequency app usage: {app_name} launched {app_data['hour']} times this hour")
    
    def _detect_unusual_app_patterns(self, app_name):
        """Detect unusual application combination patterns."""
        # Keep track of recent app launches
        current_time = time.time()
        self.app_launch_history.append({'app': app_name, 'time': current_time})
        
        # Keep only recent launches (last 10 minutes)
        self.app_launch_history = [a for a in self.app_launch_history 
                                 if current_time - a['time'] < 600]
        
        # Check for unusual combinations
        recent_apps = [a['app'] for a in self.app_launch_history[-5:]]  # Last 5 apps
        
        # Suspicious patterns (more comprehensive)
        suspicious_combinations = [
            ['terminal', 'browser', 'file'],  # Potential data exfiltration
            ['ssh', 'scp', 'rsync'],  # Remote file transfer
            ['netcat', 'nmap', 'wireshark'],  # Network reconnaissance
            ['python', 'curl', 'wget'],  # Script-based downloading
            ['bash', 'nc', 'python'],  # Potential reverse shell
            ['vim', 'nano', 'systemd'],  # System file editing
        ]
        
        for suspicious in suspicious_combinations:
            if len(set(sus_app for sus_app in suspicious 
                     if any(sus_app in app.lower() for app in recent_apps))) >= 2:
                self.db.add_event(
                    event_type="suspicious_app_combination",
                    app_name=app_name,
                    session_id=self.session_id,
                    metadata={
                        'pattern_keywords': suspicious,
                        'recent_apps': recent_apps,
                        'time_window': 600,
                        'match_count': len(set(sus_app for sus_app in suspicious 
                                             if any(sus_app in app.lower() for app in recent_apps)))
                    }
                )
                logging.warning(f"Suspicious app combination detected: {suspicious}")
    
    def _check_suspicious_applications(self, app_name):
        """Check if the launched application is potentially suspicious."""
        # Expanded list of suspicious keywords
        suspicious_keywords = [
            # Network tools
            'netcat', 'ncat', 'nc', 'nmap', 'masscan', 'zmap', 'wireshark', 'tcpdump',
            # Remote access
            'ssh', 'telnet', 'vnc', 'rdp', 'teamviewer', 'anydesk',
            # Security tools  
            'metasploit', 'burp', 'sqlmap', 'nikto', 'dirb', 'gobuster', 'ffuf',
            # Password tools
            'hashcat', 'john', 'hydra', 'medusa', 'crunch',
            # Wireless
            'aircrack', 'kismet', 'wifite', 'reaver',
            # Keyloggers/malware
            'keylog', 'rootkit', 'backdoor', 'trojan',
            # Tor/anonymity
            'tor', 'proxychains', 'torsocks',
            # Privilege escalation
            'sudo', 'su', 'pkexec', 'doas'
        ]
        
        app_lower = app_name.lower()
        
        for keyword in suspicious_keywords:
            if keyword in app_lower:
                risk_level = 'critical' if keyword in ['keylog', 'rootkit', 'backdoor', 'trojan'] else \
                           'high' if keyword in ['metasploit', 'hydra', 'aircrack'] else 'medium'
                
                self.db.add_event(
                    event_type="suspicious_application",
                    app_name=app_name,
                    session_id=self.session_id,
                    metadata={
                        'suspicious_keyword': keyword,
                        'full_app_name': app_name,
                        'risk_level': risk_level,
                        'category': self._categorize_suspicious_app(keyword)
                    }
                )
                self.unusual_apps.add(app_name)
                logging.warning(f"Suspicious application launched: {app_name} (keyword: {keyword}, risk: {risk_level})")
                break
    
    def _categorize_suspicious_app(self, keyword):
        """Categorize the type of suspicious application."""
        categories = {
            'network_recon': ['nmap', 'masscan', 'zmap', 'nikto', 'dirb'],
            'network_tools': ['netcat', 'ncat', 'nc', 'wireshark', 'tcpdump'],
            'remote_access': ['ssh', 'telnet', 'vnc', 'rdp'],
            'exploit_tools': ['metasploit', 'burp', 'sqlmap'],
            'password_attack': ['hashcat', 'john', 'hydra', 'medusa'],
            'wireless_attack': ['aircrack', 'kismet', 'wifite'],
            'malware': ['keylog', 'rootkit', 'backdoor', 'trojan'],
            'anonymity': ['tor', 'proxychains', 'torsocks'],
            'privilege_esc': ['sudo', 'su', 'pkexec']
        }
        
        for category, keywords in categories.items():
            if keyword in keywords:
                return category
        return 'unknown'

    def get_status(self) -> Dict:
        """Get current status of the event collector."""
        uptime = (datetime.now() - self.session_start_time).total_seconds()
        
        # Convert last_activity_check float to datetime for isoformat
        last_check_dt = None
        if self.last_activity_check:
            try:
                last_check_dt = datetime.fromtimestamp(self.last_activity_check).isoformat()
            except Exception:
                last_check_dt = str(self.last_activity_check)
        return {
            'running': self.running,
            'session_id': self.session_id,
            'session_start': self.session_start_time.isoformat(),
            'uptime_seconds': uptime,
            'uptime_minutes': round(uptime / 60, 2),
            'known_processes_count': len(self.known_processes),
            'known_applications_count': len(self.known_applications),
            'last_activity_check': last_check_dt
        }
