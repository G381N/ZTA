#!/usr/bin/env python3
"""
Main entry point for the Behavioral Monitoring System.
This script initializes and runs the complete system.
"""

import sys
import os
import asyncio
import logging
import signal
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.database import BehaviorDatabase
from src.core.trust_scorer import TrustScorer
from src.ml.behavior_model import BehaviorModel
from src.monitoring.event_collector import EventCollector

def setup_logging():
    """Configure logging for the application."""
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'behavioral_monitoring.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logging.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main entry point for the behavioral monitoring system."""
    print("🛡️  Behavioral Monitoring System v1.0")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Initializing Behavioral Monitoring System...")
        
        # Initialize core components
        logger.info("Initializing database...")
        db = BehaviorDatabase()
        
        logger.info("Initializing trust scorer...")
        trust_scorer = TrustScorer(db)
        
        logger.info("Initializing behavior model...")
        behavior_model = BehaviorModel()
        
        logger.info("Initializing event collector...")
        event_collector = EventCollector()
        
        # Start event collection
        logger.info("Starting event collector...")
        event_collector.start()
        
        # Check if we need to train the model
        if not behavior_model.isolation_forest:
            logger.info("No trained model found, checking for training data...")
            recent_events = db.get_recent_events(hours=72, limit=100)  # Last 3 days
            
            if len(recent_events) >= 20:
                logger.info(f"Training model with {len(recent_events)} events...")
                training_result = behavior_model.train(recent_events)
                logger.info(f"Model training result: {training_result['status']}")
            else:
                logger.warning(f"Insufficient training data ({len(recent_events)} events). "
                             "Generate synthetic data or wait for more events to accumulate.")
        else:
            logger.info("Existing trained model found and loaded")
        
        # Start the API server
        logger.info("Starting FastAPI server...")
        
        # Import and run the FastAPI app
        import uvicorn
        from src.api.main import app
        
        print("\n🚀 System initialized successfully!")
        print("📊 Dashboard available at: http://localhost:8080")
        print("📝 API documentation at: http://localhost:8080/api/docs")
        print("🔄 Event collection is running in the background")
        print("\nPress Ctrl+C to stop the system")
        print("=" * 50)
        
        # Run the server
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8080, 
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("System shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            if 'event_collector' in locals():
                event_collector.stop()
            logger.info("System shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    main()
