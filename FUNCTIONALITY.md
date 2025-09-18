# ⚙️ ZTA Behavioral Monitoring System: Functionality Overview

This document explains how the ZTA Behavioral Monitoring System works, including its architecture, main algorithms, model details, and system flow.

---

## 1. System Architecture

- **Backend:** Python (FastAPI)
- **Frontend:** HTML dashboard (served locally)
- **Database:** SQLite (local file)
- **Machine Learning:** Isolation Forest (scikit-learn)
- **Monitoring:** Real-time event collector

---

## 2. Main Components

### a. Event Collector (`src/monitoring/event_collector.py`)
- Monitors system events (processes, file changes, network activity)
- Collects data at regular intervals
- Stores events in the SQLite database

### b. Feature Extractor (`src/ml/feature_extractor.py`)
- Converts raw events into numerical features
- Features include process counts, file access patterns, network usage, etc.

### c. Behavior Model (`src/ml/behavior_model.py`)
- Uses Isolation Forest to learn normal system behavior
- Trains on extracted features
- Predicts anomalies in real time

### d. Trust Scorer (`src/core/trust_scorer.py`)
- Calculates a trust score (0-100) based on anomaly detection
- Lower score = more suspicious activity
- Score shown live on dashboard

### e. API Server (`src/api/main.py`)
- Serves RESTful endpoints for dashboard and management
- Endpoints for trust score, anomalies, system status, training, and history management

### f. Dashboard (`templates/dashboard.html`)
- Displays trust score, anomalies, system status, training progress, and live activity
- Updates in real time via API calls

---

## 3. How the Model Works

- **Algorithm:** Isolation Forest
- **Purpose:** Detects outliers (anomalies) in system behavior
- **Training:**
  - Collects normal activity for a period (training phase)
  - Fits the Isolation Forest model to extracted features
- **Prediction:**
  - New events are transformed into features
  - Model predicts if the event is normal or anomalous
  - Anomalies lower the trust score

---

## 4. Main Function Flow (`main.py`)

1. **Startup:**
   - Loads configuration
   - Initializes event collector, feature extractor, model, and API server
2. **Training:**
   - Collects baseline data
   - Trains Isolation Forest model
3. **Monitoring:**
   - Continuously collects events
   - Extracts features
   - Predicts anomalies
   - Updates trust score
   - Stores results in database
4. **Dashboard:**
   - API serves live data to dashboard
   - User can view trust score, anomalies, and system status
5. **Management:**
   - User can delete learned history, retrain model, or check system info via management tools

---

## 5. Algorithm Details

- **Isolation Forest:**
  - Unsupervised anomaly detection
  - Builds trees to isolate data points
  - Points that are isolated quickly are considered anomalies
  - Fast, efficient, and works well for behavioral data

- **Feature Extraction:**
  - Aggregates system metrics over time windows
  - Normalizes and encodes features for model input

- **Trust Score Calculation:**
  - Maps anomaly scores to a 0-100 scale
  - Recent anomalies lower the score
  - Score recovers if normal activity resumes

---

## 6. Data Flow

1. **Event Collector** → 2. **Feature Extractor** → 3. **Behavior Model** → 4. **Trust Scorer** → 5. **API Server** → 6. **Dashboard**

---

## 7. Security & Privacy

- All data is stored locally
- No internet connection required
- No personal data, keylogging, or screen capture

---

## 8. Management Tools

- **dashboard_manager.py:**
  - Delete learned history
  - View system info
  - Test trust score
- **quick_start.sh:**
  - Start/stop system
  - Check status
  - Open dashboard

---

## 9. Extending the System

- Add new event types in `event_collector.py`
- Change model in `behavior_model.py`
- Add dashboard cards in `dashboard.html`
- Update API endpoints in `api/main.py`

---

## 10. References

- [Isolation Forest (scikit-learn)](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

For more details, see the code comments and guides in `USER_GUIDE.md` and `PROJECT_SUMMARY.md`.
