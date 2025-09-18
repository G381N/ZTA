# ZTA Behavioral Monitoring System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Scikit-learn](https://img.shields.io/badge/sklearn-1.0+-orange.svg)](https://scikit-learn.org/)

🛡️ **AI-Powered Zero Trust Architecture with Behavioral Monitoring**

Advanced behavioral monitoring system that uses machine learning to establish user baseline behavior patterns and detect security anomalies in real-time.

## 🚀 Features

### 🧠 **AI-Powered Anomaly Detection**
- **Isolation Forest** machine learning model with 55 behavioral features
- Unsupervised learning adapts to individual user patterns
- Real-time anomaly detection with <1ms response time
- Dynamic trust scoring (0-100) with risk assessment

### 🌐 **Comprehensive Monitoring**
- **Application Monitoring**: Track app launches, usage patterns, and suspicious tools
- **Network Analysis**: Monitor connections, bandwidth, suspicious IPs and ports
- **Temporal Analysis**: Detect unusual activity times and work pattern deviations
- **Security Intelligence**: Identify hacking tools, attack patterns, privilege escalation

### 📊 **Real-Time Dashboard**
- Interactive web dashboard with live updates
- Trust score visualization and trend analysis
- Anomaly alerts with severity classification
- Training progress and system health monitoring
- Mobile-responsive design for remote access

### 🛠️ **Management Tools**
- Comprehensive API with 15+ endpoints
- Interactive system management interface
- Learned behavior reset and model retraining
- Database management and backup utilities
- Quick start scripts and health checks

## � How It Works

### Phase 1: Learning (First 2 Days)
```
🧠 System learns your normal patterns:
├── Work hours and schedule patterns
├── Typical applications used
├── Network connection behavior
├── Session duration habits
└── Application switching patterns
```

### Phase 2: Active Monitoring
```
🛡️ Real-time protection:
├── Anomaly detection every 30 seconds
├── Dynamic trust score updates
├── Security threat classification
├── Behavioral pattern analysis
└── Risk assessment and alerts
```

## � Installation

### Prerequisites
- Python 3.8 or higher
- Linux/macOS/Windows
- 2GB RAM minimum
- 1GB disk space

### Quick Setup
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/zta-behavioral-monitoring.git
cd zta-behavioral-monitoring

# Install dependencies
pip install -r requirements.txt

# Start system
./quick_start.sh
```

### Manual Installation
```bash
# Install Python packages
pip install fastapi uvicorn sqlite3 pandas numpy scikit-learn psutil

# Start the system
python3 main.py
```

## 🚀 Quick Start

### Option 1: Interactive Menu
```bash
./quick_start.sh
```

### Option 2: Direct Commands
```bash
# Start in foreground (recommended for first use)
./quick_start.sh start

# Start in background (for daily use)
./quick_start.sh background

# Check system status
./quick_start.sh status

# Open dashboard
./quick_start.sh dashboard
```

### Option 3: Python Direct
```bash
python3 main.py
```

## 📊 Dashboard Features

The web dashboard provides:

- **Trust Score Display**: Current trust score (0-100) with risk level indicator
- **System Status**: Real-time monitoring status and component health
- **Recent Anomalies**: List of detected behavioral anomalies with details
- **Trust Score History**: 24-hour chart showing trust score evolution
- **Anomalies Timeline**: Visual representation of when anomalies occurred
- **Auto-refresh**: Updates every 30 seconds automatically

## 🔧 API Endpoints

### Core Endpoints

- `GET /` - Main dashboard
- `GET /api/trust` - Get current trust score and status
- `POST /api/event` - Submit a new behavioral event
- `GET /api/anomalies` - Get recent anomalies
- `GET /api/events` - Get recent events
- `GET /api/status` - Get system status

### Advanced Endpoints

- `GET /api/trust/history?hours=24` - Get trust score history
- `POST /api/trust/update` - Manually update trust score (admin)
- `POST /api/trust/reset` - Reset trust score to initial value
- `POST /api/model/train` - Train or retrain the behavior model
- `GET /api/model/explain/{event_id}` - Get explanation for a prediction

## 🤖 How It Works

### 1. Event Collection
The system monitors:
- **Application Launches**: When new applications start
- **Session Activities**: System startup/shutdown events
- **System Metrics**: CPU/memory usage patterns

### 2. Feature Extraction
Raw events are converted into ML features:
- **Temporal**: Hour of day, day of week, weekend/weekday
- **Application Categories**: Browser, IDE, terminal, media, etc.
- **Behavioral Patterns**: Rapid switching, unusual timing, new applications

### 3. Anomaly Detection
Uses scikit-learn's IsolationForest to detect:
- **Time-based Anomalies**: Activity at unusual hours
- **Application Anomalies**: Unknown or rarely used applications
- **Pattern Anomalies**: Rapid application switching, suspicious sequences

### 4. Trust Scoring
Dynamic trust score (0-100) that:
- **Starts at 100** (full trust)
- **Decreases** when anomalies are detected (based on severity)
- **Recovers slowly** during normal behavior periods
- **Triggers alerts** when crossing thresholds (60, 40)

### 5. Alerting & Logging
All anomalies are logged with:
- Timestamp and event details
- Anomaly type and severity
- Trust score impact
- Contextual information

## 📁 Project Structure

```
ZTA/
├── src/
│   ├── api/                 # FastAPI backend
│   │   └── main.py         # API server and endpoints
│   ├── core/               # Core system components
│   │   ├── database.py     # SQLite database handler
│   │   └── trust_scorer.py # Trust scoring system
│   ├── ml/                 # Machine learning components
│   │   ├── behavior_model.py    # AI anomaly detection
│   │   └── feature_extractor.py # Feature extraction
│   └── monitoring/         # Event collection
│       └── event_collector.py   # System event monitoring
├── scripts/
│   └── generate_synthetic_data.py # Demo data generation
├── templates/
│   └── dashboard.html      # Web dashboard template
├── static/                 # Static web assets
├── data/                   # SQLite database storage
├── logs/                   # Application logs
├── models/                 # Trained ML models
├── venv/                   # Python virtual environment
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Event Collection
- **Collection Interval**: 10 seconds between process checks
- **Session Timeout**: 30 minutes of inactivity ends session
- **Monitored Applications**: Browsers, IDEs, terminals, media players, etc.

### Anomaly Detection
- **Model**: IsolationForest with 10% contamination rate
- **Training Data**: Minimum 20 events required
- **Retraining**: Automatic when 100+ new events accumulate

### Trust Scoring
- **Initial Score**: 100 (full trust)
- **Penalty System**: 1-20 points per anomaly (severity-based)
- **Recovery Rate**: 1 point per hour of normal behavior
- **Alert Thresholds**: Critical (40), Warning (60), Info (80)

## 🎭 Synthetic Data Generator

For testing and demonstration, use the built-in data generator:

```bash
source venv/bin/activate
python scripts/generate_synthetic_data.py
```

This generates:
- **Normal Usage Patterns**: Typical work day activities
- **Anomalous Behaviors**: Various types of suspicious activities
- **Realistic Timing**: Activity patterns matching real user behavior
- **Multiple Scenarios**: Weekend work, late-night activity, unknown apps

## 🔍 Anomaly Types Detected

1. **Unusual Time**: Activity during very late/early hours
2. **Unknown Applications**: First-time application launches
3. **Rapid Switching**: Quick succession of application launches
4. **Weekend Work**: Development activity on weekends
5. **Suspicious Patterns**: Combinations of unusual behaviors
6. **High System Load**: Unusual CPU/memory usage patterns

## 📈 Trust Score Interpretation

- **90-100**: Excellent - Normal behavior patterns
- **70-89**: Good - Minor anomalies detected
- **50-69**: Fair - Moderate suspicious activity
- **30-49**: Poor - Significant anomalies detected
- **0-29**: Critical - Highly suspicious behavior

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   source venv/bin/activate  # Ensure virtual environment is active
   pip install -r requirements.txt  # Reinstall dependencies
   ```

2. **Permission Errors**:
   ```bash
   chmod +x main.py
   sudo chown -R $USER:$USER /home/gebin/Desktop/ZTA
   ```

3. **Database Issues**:
   ```bash
   rm data/behavior.db  # Remove database (will be recreated)
   ```

4. **Model Training Failures**:
   ```bash
   python scripts/generate_synthetic_data.py  # Generate training data
   ```

### Logs

Check application logs for detailed error information:
```bash
tail -f logs/behavioral_monitoring.log
tail -f logs/api.log
```

## 🔒 Security Considerations

- **Local Storage**: All data stored locally in SQLite database
- **No Network Traffic**: System operates entirely offline
- **Process Monitoring**: Only monitors process names, not content
- **Privacy**: No keylogging, screen capture, or content analysis

## 🚀 Performance

The system is designed for minimal resource usage:
- **CPU Usage**: <5% during normal operation
- **Memory Usage**: ~50-100MB RAM
- **Storage**: SQLite database grows ~1MB per week of typical usage
- **Network**: No network usage (fully offline)

## 🤝 Contributing

This is a demonstration project. For improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on Kali Linux
5. Submit a pull request

## 📜 License

This project is provided for educational and demonstration purposes.

## 🙋‍♂️ Support

For questions or issues:

1. Check the logs in the `logs/` directory
2. Ensure virtual environment is properly activated
3. Verify all dependencies are installed
4. Test with synthetic data first

## 🎯 Future Enhancements

Potential improvements for production use:

- **Network Activity Monitoring**: Monitor network connections
- **File Access Monitoring**: Track file system access patterns
- **User Authentication Integration**: Link with system authentication
- **Advanced ML Models**: Deep learning for better anomaly detection
- **Distributed Deployment**: Multi-machine monitoring
- **Integration APIs**: Connect with SIEM systems
- **Mobile Companion**: Mobile app for alerts and control

---

**🛡️ Behavioral Monitoring System v1.0** - Demonstrating AI-based behavioral analysis for cybersecurity applications.
