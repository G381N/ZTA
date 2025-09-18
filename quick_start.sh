#!/bin/bash

# 🛡️ ZTA System Quick Start Script
# This script helps you easily start and manage your ZTA system

echo "🛡️  ZTA Behavioral Monitoring System"
echo "====================================="

# Function to check if system is running
check_system() {
    if curl -s http://localhost:8080/api/status > /dev/null 2>&1; then
        echo "✅ System is running"
        return 0
    else
        echo "❌ System is not running"
        return 1
    fi
}

# Function to start system
start_system() {
    echo "🚀 Starting ZTA System..."
    echo "   Dashboard will be available at: http://localhost:8080"
    echo "   Press Ctrl+C to stop the system"
    echo ""
    python3 main.py
}

# Function to start system in background
start_background() {
    echo "🚀 Starting ZTA System in background..."
    nohup python3 main.py > /dev/null 2>&1 &
    echo "   Process ID: $!"
    sleep 3
    if check_system; then
        echo "   Dashboard available at: http://localhost:8080"
    else
        echo "   ❌ Failed to start system"
    fi
}

# Function to stop system
stop_system() {
    echo "🛑 Stopping ZTA System..."
    pkill -f "python3 main.py"
    sleep 2
    if check_system; then
        echo "   ❌ System still running"
    else
        echo "   ✅ System stopped"
    fi
}

# Function to open dashboard
open_dashboard() {
    if check_system; then
        echo "🌐 Opening dashboard..."
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:8080
        elif command -v open > /dev/null; then
            open http://localhost:8080
        else
            echo "   Please open: http://localhost:8080"
        fi
    else
        echo "   ❌ System is not running. Start it first."
    fi
}

# Function to test system
test_system() {
    echo "🔍 Testing system functionality..."
    python3 test_dashboard_cards.py
}

# Function to manage system
manage_system() {
    echo "🛠️  Opening system manager..."
    python3 dashboard_manager.py
}

# Function to show system status
show_status() {
    echo "📊 System Status:"
    echo "=================="
    
    if check_system; then
        echo "Status: ✅ Running"
        
        # Get trust score
        TRUST_SCORE=$(curl -s http://localhost:8080/api/trust | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['current_score'])" 2>/dev/null)
        if [ ! -z "$TRUST_SCORE" ]; then
            echo "Trust Score: $TRUST_SCORE"
        fi
        
        # Get training status
        TRAINING_PHASE=$(curl -s http://localhost:8080/api/training-status | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['current_phase'])" 2>/dev/null)
        if [ ! -z "$TRAINING_PHASE" ]; then
            echo "Training Phase: $TRAINING_PHASE"
        fi
        
        # Get anomaly count
        ANOMALY_COUNT=$(curl -s http://localhost:8080/api/anomalies | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['data']['anomalies']))" 2>/dev/null)
        if [ ! -z "$ANOMALY_COUNT" ]; then
            echo "Recent Anomalies: $ANOMALY_COUNT"
        fi
        
    else
        echo "Status: ❌ Not Running"
    fi
    echo ""
}

# Main menu
show_menu() {
    echo ""
    echo "🎮 What would you like to do?"
    echo "1. Start System (Foreground)"
    echo "2. Start System (Background)"
    echo "3. Stop System"
    echo "4. Check Status"
    echo "5. Open Dashboard"
    echo "6. Test System"
    echo "7. System Manager"
    echo "8. View User Guide"
    echo "9. Exit"
    echo ""
    read -p "Enter your choice (1-9): " choice
    
    case $choice in
        1) start_system ;;
        2) start_background ;;
        3) stop_system ;;
        4) show_status ;;
        5) open_dashboard ;;
        6) test_system ;;
        7) manage_system ;;
        8) 
            if [ -f "USER_GUIDE.md" ]; then
                echo "📖 Opening user guide..."
                if command -v less > /dev/null; then
                    less USER_GUIDE.md
                else
                    cat USER_GUIDE.md
                fi
            else
                echo "❌ User guide not found"
            fi
            ;;
        9) 
            echo "👋 Goodbye!"
            exit 0 
            ;;
        *) 
            echo "❌ Invalid choice. Please try again."
            show_menu
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Please run this script from the ZTA directory"
    echo "   cd /home/gebin/Desktop/ZTA && ./quick_start.sh"
    exit 1
fi

# Initial status check
show_status

# Show menu if no arguments provided
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        echo ""
        read -p "Press Enter to continue..."
    done
else
    # Handle command line arguments
    case "$1" in
        "start") start_system ;;
        "background") start_background ;;
        "stop") stop_system ;;
        "status") show_status ;;
        "dashboard") open_dashboard ;;
        "test") test_system ;;
        "manage") manage_system ;;
        *) 
            echo "Usage: $0 [start|background|stop|status|dashboard|test|manage]"
            exit 1
            ;;
    esac
fi
