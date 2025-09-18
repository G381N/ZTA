# 🛡️ ZTA Behavioral Monitoring System

Welcome! This guide will help you set up, run, and use the ZTA Behavioral Monitoring System on your computer. No advanced knowledge required—just follow the steps below!

---

## 🚀 What is This?

ZTA is an AI-powered system that monitors your computer's behavior, detects security threats, and shows everything in a live dashboard. It works on Linux, macOS, and Windows.

---

## 📦 How to Get Started

### 1. **Install Prerequisites**
- **Python 3.8 or newer**
- **Git** (optional, but recommended)

#### Check Python:
```bash
python3 --version
```
If you see a version like `Python 3.8.0` or higher, you're good!

#### Check Git:
```bash
git --version
```
If you see a version, you're good!

---

### 2. **Download the Project**

#### Option A: Using Git (Recommended)
```bash
git clone https://github.com/YOUR_USERNAME/zta-behavioral-monitoring.git
cd zta-behavioral-monitoring
```

#### Option B: Manual Download
- Go to the GitHub page
- Click "Code" > "Download ZIP"
- Extract the ZIP file
- Open a terminal in the extracted folder

---

### 3. **Install Python Packages**

#### Recommended: Use a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 4. **Start the System**

#### Easiest Way: Quick Start Script
```bash
./quick_start.sh
```
If you see a menu, you're ready! Choose "Start System" or "Start in Background".

#### Or, Start Manually
```bash
python3 main.py
```

---

### 5. **Open the Dashboard**

- Open your web browser
- Go to: [http://localhost:8080](http://localhost:8080)
- You should see your live dashboard!

---

## 🛠️ Useful Commands

- **Check system status:**
  ```bash
  ./quick_start.sh status
  ```
- **Open dashboard in browser:**
  ```bash
  ./quick_start.sh dashboard
  ```
- **Run health check:**
  ```bash
  python3 test_dashboard_cards.py
  ```
- **Manage system (delete history, view info):**
  ```bash
  python3 dashboard_manager.py
  ```

---

## 🌐 Dashboard Features

- **Trust Score:** Shows your computer's security level (0-100)
- **Anomalies:** Lists suspicious activities
- **System Status:** Shows if everything is working
- **Training Progress:** Shows how much the system has learned
- **Live Activity:** See what's happening right now

---

## 🧑‍💻 Common Issues & Fixes

- **Missing Python packages?**
  ```bash
  pip install -r requirements.txt
  ```
- **Port already in use?**
  Stop other running instances:
  ```bash
  pkill -f "python3 main.py"
  ```
- **Dashboard not loading?**
  Make sure the system is running (`python3 main.py`)

---

## 🔒 Security & Privacy

- All data stays on your computer
- No internet connection required
- No keylogging or screen capture

---

## 📚 More Help

- **User Guide:** See `USER_GUIDE.md` for advanced features
- **Dashboard Guide:** Open `DASHBOARD_GUIDE.html` in your browser
- **Project Summary:** See `PROJECT_SUMMARY.md` for technical details

---

## 📝 License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## 🎉 You're Ready!

Enjoy your new AI-powered behavioral monitoring dashboard!
