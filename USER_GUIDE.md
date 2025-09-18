# 🛡️ ZTA Behavioral Monitoring System - User Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [System Training](#system-training)
3. [Web Dashboard Access](#web-dashboard-access)
4. [Management Tools](#management-tools)
5. [Monitoring Features](#monitoring-features)
6. [Advanced Usage](#advanced-usage)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### 1. Start the System
```bash
cd /home/gebin/Desktop/ZTA
python3 main.py
```

**What you'll see:**
```
🛡️  Behavioral Monitoring System v1.0
==================================================
🚀 System initialized successfully!
📊 Dashboard available at: http://localhost:8080
📝 API documentation at: http://localhost:8080/api/docs
🔄 Event collection is running in the background
```

### 2. Access Your Dashboards

**Main Web Dashboard:**
- Open browser → http://localhost:8080
- Real-time trust score display
- Anomaly alerts
- System status overview

**API Documentation Dashboard:**
- Open browser → http://localhost:8080/api/docs
- Interactive API testing
- Complete endpoint documentation

---

## 🎯 System Training

### Phase 1: Initial Training (2 days)
The system learns your normal behavior patterns:

**What it learns:**
- Your usual work hours (8 AM - 6 PM)
- Applications you normally use
- Network connection patterns
- Session duration habits

**During training, you'll see:**
```
Training phase: initial_training
Events processed: 1,234
Baseline established: false
Anomaly detection active: false
```

### Phase 2: Active Monitoring
After 2 days, anomaly detection activates:

**Features activated:**
- Real-time anomaly detection
- Dynamic trust scoring
- Security alerts
- Behavioral analysis

### Monitor Training Progress
```bash
# Check training status
python3 dashboard_manager.py
# Choose option 1 to validate APIs
```

---

## 🌐 Web Dashboard Access

### Main Dashboard Features

**1. Trust Score Card**
- Current trust level (0-100)
- Risk assessment (Low/Medium/High/Critical)
- Real-time updates

**2. System Status**
- Component health check
- Uptime information
- Performance metrics

**3. Recent Anomalies**
- Latest security alerts
- Anomaly severity levels
- Timeline of events

**4. Activity Monitor**
- Live system activity
- Application launches
- Network connections

**5. Training Progress**
- Current learning phase
- Events processed
- Baseline establishment

### Dashboard URLs

| Feature | URL | Description |
|---------|-----|-------------|
| **Main Dashboard** | `http://localhost:8080` | Primary monitoring interface |
| **API Docs** | `http://localhost:8080/api/docs` | Interactive API documentation |
| **System Status** | `http://localhost:8080/api/status` | JSON system status |
| **Trust Score** | `http://localhost:8080/api/trust` | Current trust information |
| **Anomalies** | `http://localhost:8080/api/anomalies` | Recent anomaly data |

---

## 🛠️ Management Tools

### Dashboard Manager Tool
Your comprehensive management interface:

```bash
python3 dashboard_manager.py
```

**Menu Options:**
1. **Validate All Dashboard APIs** - Test system health
2. **Show System Information** - Database stats, model info
3. **Delete Learned History** - Reset training data
4. **Test Trust Score** - Check current trust status
5. **Exit** - Close manager

### Quick Dashboard Test
Verify all cards are working:

```bash
python3 test_dashboard_cards.py
```

Expected output:
```
🔍 Testing Dashboard Cards Population
=============================================
✅ System Status Card: running
✅ Training Progress Card: initial_training (8492 events)
✅ Trust Score Card: Score 75.0
✅ Anomalies Card: 3 anomalies
✅ Recent Activity Card: 12 activities
✅ Learned Patterns Card: 15 patterns
=============================================
🎉 ALL DASHBOARD CARDS ARE WORKING AND POPULATED!
```

---

## 📊 Monitoring Features

### Real-Time Event Collection
The system automatically monitors:

**Application Events:**
- App launches and closures
- Session starts/ends
- Process changes

**Network Events:**
- Connection attempts
- Data transfer patterns
- Unusual network behavior

**System Events:**
- Login/logout activities
- System resource usage
- Security-related activities

### Anomaly Detection
**Types of anomalies detected:**
- Unusual application launches
- Suspicious network activity
- Off-hours system usage
- Rapid application switching
- High-frequency connections

### Trust Scoring
**Dynamic trust calculation based on:**
- Normal vs. anomalous behavior
- Time-based patterns
- Application usage patterns
- Network behavior
- Security events

---

## 🔧 Advanced Usage

### Custom Training Period
Modify training duration in `config/training_config.json`:

```json
{
    "training_period_days": 3,
    "baseline_events_required": 1000,
    "anomaly_threshold": 0.15
}
```

### API Integration
Use the REST API for custom integrations:

```python
import requests

# Get current trust score
response = requests.get("http://localhost:8080/api/trust")
trust_data = response.json()
print(f"Trust Score: {trust_data['data']['current_score']}")

# Get recent anomalies
response = requests.get("http://localhost:8080/api/anomalies")
anomalies = response.json()
print(f"Anomalies found: {len(anomalies['data']['anomalies'])}")
```

### Manual Trust Score Updates
For testing or administrative purposes:

```python
import requests

# Update trust score manually
data = {
    "score": 85,
    "reason": "Manual administrative update"
}
response = requests.post("http://localhost:8080/api/trust/update", json=data)
```

---

## 🔄 Daily Usage Workflow

### Starting Your Day
1. **Start the system:**
   ```bash
   cd /home/gebin/Desktop/ZTA
   python3 main.py
   ```

2. **Check dashboard:** Open http://localhost:8080

3. **Verify system health:**
   ```bash
   python3 test_dashboard_cards.py
   ```

### During the Day
- System runs automatically in background
- Monitor trust score changes
- Review anomaly alerts
- Check dashboard periodically

### End of Day
- System continues running (optional)
- Or stop with `Ctrl+C`
- Review daily activity summary

---

## 🗂️ Data Management

### View System Statistics
```bash
python3 dashboard_manager.py
# Choose option 2 for system information
```

### Reset Training Data
When you want to start fresh:

```bash
python3 dashboard_manager.py
# Choose option 3: Delete Learned History
# Confirm with 'yes'
# Restart system: python3 main.py
```

### Backup Your Data
```bash
# Backup database
cp data/behavior.db data/behavior_backup_$(date +%Y%m%d).db

# Backup trained model
cp models/behavior_model.pkl models/behavior_model_backup_$(date +%Y%m%d).pkl
```

---

## 🔍 Troubleshooting

### System Won't Start
**Check Python environment:**
```bash
python3 --version  # Should be 3.8+
pip3 list | grep -E "(fastapi|sqlite|requests)"
```

**Install missing packages:**
```bash
pip3 install -r requirements.txt
```

### Dashboard Not Loading
**Verify system is running:**
```bash
curl http://localhost:8080/api/status
```

**Check if port is in use:**
```bash
netstat -tulpn | grep :8080
```

### No Anomalies Detected
- System may still be in training phase (first 2 days)
- Check training status: `python3 dashboard_manager.py` → option 1
- Ensure you're doing varied activities for the system to learn

### Trust Score Not Changing
- Trust score updates based on behavioral patterns
- May take time to establish baseline
- Check recent activity in dashboard

### Database Issues
**Reset database if corrupted:**
```bash
# Backup first
cp data/behavior.db data/behavior_backup.db
# Delete and restart system (will recreate)
rm data/behavior.db
python3 main.py
```

---

## 📱 Mobile Access

Access your dashboard from mobile devices:

**Find your IP address:**
```bash
ip addr show | grep 'inet ' | grep -v '127.0.0.1'
```

**Access from mobile:** `http://YOUR_IP:8080`

---

## 🎮 Example Usage Scenarios

### Scenario 1: Security Monitoring
- Start system before work
- Monitor trust score throughout day
- Investigate any anomaly alerts
- Review end-of-day summary

### Scenario 2: Behavioral Analysis
- Run system for a week
- Analyze learned patterns
- Identify unusual behavior periods
- Optimize work habits

### Scenario 3: System Administration
- Use for server monitoring
- Set up automated alerts
- Track administrative activities
- Detect unauthorized access

---

## 📈 Performance Tips

1. **Let it train:** Allow full 2-day training period
2. **Consistent usage:** Use your computer normally during training
3. **Regular monitoring:** Check dashboard daily
4. **Data cleanup:** Periodically clean old data (option in dashboard manager)
5. **Backup regularly:** Save your trained models and data

---

## 🆘 Getting Help

**Quick health check:**
```bash
python3 test_dashboard_cards.py
```

**Full system validation:**
```bash
python3 dashboard_manager.py
```

**View logs:**
```bash
tail -f logs/api.log
tail -f logs/behavioral_monitoring.log
```

**Reset everything:**
```bash
python3 dashboard_manager.py  # Option 3: Delete learned history
```

---

## 🎯 Success Indicators

You know your system is working perfectly when:

✅ **All dashboard cards show data**
✅ **Trust score updates regularly** 
✅ **Anomalies are detected appropriately**
✅ **Training progresses through phases**
✅ **Web dashboard loads instantly**
✅ **API responses are fast (<500ms)**

**Your ZTA system is now ready for 24/7 behavioral monitoring!** 🛡️

---

*Last updated: September 18, 2025*
*System Version: 1.0.0*
