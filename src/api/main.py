"""
FastAPI backend for behavioral monitoring system.
Provides REST API for event submission and trust score monitoring.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from pydantic import BaseModel, Field

# Import our modules
from src.core.database import BehaviorDatabase
from src.core.trust_scorer import TrustScorer
from src.core.training_manager import TrainingManager
from src.monitoring.event_collector import EventCollector
from src.ml.behavior_model import BehaviorModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Pydantic models for API
class EventSubmission(BaseModel):
    event_type: str = Field(..., description="Type of event (e.g., 'app_launch', 'session_start')")
    app_name: Optional[str] = Field(None, description="Name of the application")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event metadata")

class TrustScoreUpdate(BaseModel):
    score: int = Field(..., ge=0, le=100, description="New trust score (0-100)")
    reason: str = Field(..., description="Reason for the manual update")

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# Initialize FastAPI app
app = FastAPI(
    title="Behavioral Monitoring System",
    description="AI-based behavioral monitoring and dynamic trust scoring for laptop users",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global components (initialized on startup)
db: Optional[BehaviorDatabase] = None
trust_scorer: Optional[TrustScorer] = None
behavior_model: Optional[BehaviorModel] = None
event_collector: Optional[EventCollector] = None

# Background task for anomaly detection
anomaly_detection_task: Optional[asyncio.Task] = None

@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup."""
    global db, trust_scorer, behavior_model, event_collector, training_manager
    
    logger.info("Initializing Behavioral Monitoring System...")
    
    # Initialize database
    db = BehaviorDatabase()
    logger.info("Database initialized")
    
    # Initialize training manager
    training_manager = TrainingManager(db)
    
    # Initialize trust scorer
    trust_scorer = TrustScorer(db)
    logger.info(f"Trust scorer initialized with score: {trust_scorer.current_score}")
    
    # Initialize behavior model
    behavior_model = BehaviorModel()
    logger.info("Behavior model initialized")
    
    # Initialize event collector
    event_collector = EventCollector()
    event_collector.start()
    logger.info("Event collector started")
    
    # Start background anomaly detection
    global anomaly_detection_task
    anomaly_detection_task = asyncio.create_task(anomaly_detection_loop())
    logger.info("Background anomaly detection started")
    
    logger.info("System initialization complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global anomaly_detection_task, event_collector
    
    logger.info("Shutting down Behavioral Monitoring System...")
    
    # Stop background tasks
    if anomaly_detection_task:
        anomaly_detection_task.cancel()
        try:
            await anomaly_detection_task
        except asyncio.CancelledError:
            pass
    
    # Stop event collector
    if event_collector:
        event_collector.stop()
    
    logger.info("System shutdown complete")

async def anomaly_detection_loop():
    """Background task for continuous anomaly detection with training awareness."""
    logger.info("Starting anomaly detection loop")
    
    while True:
        try:
            # Get unprocessed events
            unprocessed = db.get_unprocessed_events()
            
            if unprocessed:
                logger.info(f"Processing {len(unprocessed)} new events for anomaly detection")
                
                # Process events through training manager first
                for event in unprocessed:
                    training_manager.process_training_event(event)
                
                # Only detect anomalies if system is ready
                if training_manager.should_detect_anomalies():
                    # Filter out normal applications during detection
                    filtered_events = []
                    for event in unprocessed:
                        if event.get('event_type') == 'app_launch':
                            app_name = event.get('app_name', '')
                            if not training_manager.is_normal_application(app_name):
                                filtered_events.append(event)
                        else:
                            filtered_events.append(event)
                    
                    if filtered_events:
                        # Detect anomalies on filtered events
                        anomalies = behavior_model.detect_anomalies(filtered_events)
                        
                        # Filter out anomalies for normal time/network
                        filtered_anomalies = []
                        for anomaly in anomalies:
                            should_include = True
                            
                            # Check if it's during normal time
                            if anomaly.get('anomaly_type') == 'unusual_time':
                                if training_manager.is_normal_time():
                                    should_include = False
                            
                            if should_include:
                                filtered_anomalies.append(anomaly)
                        
                        # Update trust score based on filtered anomalies
                        if filtered_anomalies:
                            trust_update = trust_scorer.process_anomalies(filtered_anomalies)
                            logger.warning(f"Detected {len(filtered_anomalies)} anomalies, trust score: {trust_update['new_score']}")
                        else:
                            trust_update = trust_scorer.process_normal_behavior(len(unprocessed))
                            logger.info(f"No anomalies detected, trust score: {trust_update['new_score']}")
                    else:
                        # All events are normal, increase trust
                        trust_update = trust_scorer.process_normal_behavior(len(unprocessed))
                        logger.info(f"All events normal, trust score: {trust_update['new_score']}")
                else:
                    # Still in training phase
                    phase = training_manager.get_current_phase()
                    logger.info(f"Training phase: {phase}, events processed: {len(unprocessed)}")
                
                # Mark events as processed
                event_ids = [e['id'] for e in unprocessed]
                db.mark_events_processed(event_ids)
            
            # Check for model retraining (only after training period)
            if training_manager.should_detect_anomalies() and not behavior_model.isolation_forest:
                # Training period complete, train model on baseline data
                recent_events = db.get_recent_events(hours=168)  # 7 days of data
                if len(recent_events) >= 50:  # Minimum training data
                    logger.info("Training behavior model on established baseline")
                    training_result = behavior_model.train(recent_events)
                    logger.info(f"Model training result: {training_result}")
            
            # Sleep before next check
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except asyncio.CancelledError:
            logger.info("Anomaly detection loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in anomaly detection loop: {e}")
            await asyncio.sleep(60)  # Wait longer on error

def get_db():
    """Dependency to get database instance."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return db

def get_trust_scorer():
    """Dependency to get trust scorer instance."""
    if trust_scorer is None:
        raise HTTPException(status_code=503, detail="Trust scorer not initialized")
    return trust_scorer

def get_behavior_model():
    """Dependency to get behavior model instance."""
    if behavior_model is None:
        raise HTTPException(status_code=503, detail="Behavior model not initialized")
    return behavior_model

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    trust_status = trust_scorer.get_trust_status()
    recent_anomalies = db.get_recent_anomalies(hours=24)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "trust_score": trust_status['current_score'],
        "risk_level": trust_status['risk_level'],
        "anomaly_count": len(recent_anomalies),
        "last_updated": trust_status['last_updated']
    })

@app.post("/api/event", response_model=ApiResponse)
async def submit_event(
    event: EventSubmission,
    background_tasks: BackgroundTasks,
    db: BehaviorDatabase = Depends(get_db)
):
    """Submit a new behavioral event."""
    try:
        event_id = db.add_event(
            event_type=event.event_type,
            app_name=event.app_name,
            session_id=event.session_id,
            metadata=event.metadata
        )
        
        logger.info(f"Event submitted: {event.event_type}, ID: {event_id}")
        
        return ApiResponse(
            success=True,
            message="Event submitted successfully",
            data={"event_id": event_id}
        )
        
    except Exception as e:
        logger.error(f"Error submitting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trust", response_model=ApiResponse)
async def get_trust_score(trust_scorer: TrustScorer = Depends(get_trust_scorer)):
    """Get current trust score and status."""
    try:
        trust_status = trust_scorer.get_trust_status()
        
        return ApiResponse(
            success=True,
            message="Trust status retrieved successfully",
            data=trust_status
        )
        
    except Exception as e:
        logger.error(f"Error getting trust status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trust/history")
async def get_trust_history(
    hours: int = 24,
    db: BehaviorDatabase = Depends(get_db)
):
    """Get trust score history."""
    try:
        history = db.get_trust_history(hours=hours)
        
        return ApiResponse(
            success=True,
            message=f"Trust history for last {hours} hours retrieved",
            data={
                "history": history,
                "period_hours": hours,
                "data_points": len(history)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting trust history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anomalies")
async def get_recent_anomalies(
    hours: int = 24,
    db: BehaviorDatabase = Depends(get_db)
):
    """Get recent anomalies."""
    try:
        anomalies = db.get_recent_anomalies(hours=hours)
        
        return ApiResponse(
            success=True,
            message=f"Recent anomalies for last {hours} hours retrieved",
            data={
                "anomalies": anomalies,
                "count": len(anomalies),
                "period_hours": hours
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activity")
async def get_live_activity(
    minutes: int = 30,
    db: BehaviorDatabase = Depends(get_db)
):
    """Get live system activity for dashboard."""
    try:
        activity = db.get_live_activity(minutes=minutes)
        
        return ApiResponse(
            success=True,
            message=f"Live activity for last {minutes} minutes retrieved",
            data=activity
        )
        
    except Exception as e:
        logger.error(f"Error getting live activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events")
async def get_recent_events(
    hours: int = 24,
    limit: int = 100,
    db: BehaviorDatabase = Depends(get_db)
):
    """Get recent events."""
    try:
        events = db.get_recent_events(hours=hours, limit=limit)
        
        return ApiResponse(
            success=True,
            message=f"Recent events for last {hours} hours retrieved",
            data={
                "events": events,
                "count": len(events),
                "period_hours": hours,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learned-patterns")
async def get_learned_patterns(db: BehaviorDatabase = Depends(get_db)):
    """Get what the system has learned as normal patterns."""
    try:
        patterns = db.get_learned_patterns()
        
        return {
            "success": True,
            "message": "Learned patterns retrieved successfully",
            "data": patterns
        }
        
    except Exception as e:
        logger.error(f"Error getting learned patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/training-status")
async def get_training_status():
    """Get current training status and progress."""
    try:
        status = training_manager.get_training_status()
        
        return {
            "success": True,
            "message": "Training status retrieved successfully",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/anomalies/{anomaly_id}/approve")
async def approve_anomaly(anomaly_id: int):
    """Approve an anomaly as normal behavior."""
    try:
        success = training_manager.approve_anomaly_as_normal(anomaly_id)
        
        if success:
            return {
                "success": True,
                "message": f"Anomaly {anomaly_id} approved as normal behavior"
            }
        else:
            raise HTTPException(status_code=404, detail="Anomaly not found or could not be approved")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving anomaly {anomaly_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/learned-apps/{app_name}")
async def remove_learned_app(app_name: str):
    """Remove an application from the learned normal apps list."""
    try:
        success = training_manager.remove_learned_app(app_name)
        
        if success:
            return {
                "success": True,
                "message": f"Removed {app_name} from learned applications"
            }
        else:
            raise HTTPException(status_code=404, detail="Application not found in learned list")
            
    except Exception as e:
        logger.error(f"Error removing app {app_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learned-apps/{app_name}")
async def add_learned_app(app_name: str):
    """Add an application to the learned normal apps list."""
    try:
        success = training_manager.add_learned_app(app_name)
        
        return {
            "success": True,
            "message": f"Added {app_name} to learned applications"
        }
            
    except Exception as e:
        logger.error(f"Error adding app {app_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_system_status():
    """Get overall system status."""
    try:
        status = {
            "system": "Behavioral Monitoring System",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            
            "components": {
                "database": db is not None,
                "trust_scorer": trust_scorer is not None,
                "behavior_model": behavior_model is not None,
                "event_collector": event_collector is not None and event_collector.running,
            },
            
            "trust_score": trust_scorer.current_score if trust_scorer else None,
            "model_status": behavior_model.get_model_status() if behavior_model else None,
            "collector_status": event_collector.get_status() if event_collector else None
        }
        
        return ApiResponse(
            success=True,
            message="System status retrieved successfully",
            data=status
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trust/update", response_model=ApiResponse)
async def update_trust_score(
    update: TrustScoreUpdate,
    trust_scorer: TrustScorer = Depends(get_trust_scorer)
):
    """Manually update trust score (for testing/admin purposes)."""
    try:
        result = trust_scorer.force_score_update(update.score, update.reason)
        
        return ApiResponse(
            success=True,
            message="Trust score updated successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error updating trust score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trust/reset", response_model=ApiResponse)
async def reset_trust_score(trust_scorer: TrustScorer = Depends(get_trust_scorer)):
    """Reset trust score to initial value."""
    try:
        result = trust_scorer.reset_trust_score("Manual reset via API")
        
        return ApiResponse(
            success=True,
            message="Trust score reset successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error resetting trust score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model/train", response_model=ApiResponse)
async def train_model(
    hours: int = 72,
    force_retrain: bool = False,
    behavior_model: BehaviorModel = Depends(get_behavior_model),
    db: BehaviorDatabase = Depends(get_db)
):
    """Train or retrain the behavior model."""
    try:
        events = db.get_recent_events(hours=hours, limit=1000)
        
        if len(events) < 20:
            return ApiResponse(
                success=False,
                message=f"Insufficient training data: {len(events)} events (minimum 20 required)"
            )
        
        result = behavior_model.train(events, force_retrain=force_retrain)
        
        return ApiResponse(
            success=result['status'] == 'success',
            message=f"Model training: {result['status']}",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model/explain/{event_id}")
async def explain_prediction(
    event_id: int,
    behavior_model: BehaviorModel = Depends(get_behavior_model),
    db: BehaviorDatabase = Depends(get_db)
):
    """Get explanation for a specific event's prediction."""
    try:
        # Get the event
        events = db.get_recent_events(hours=24 * 7, limit=10000)  # Search last week
        event = None
        for e in events:
            if e['id'] == event_id:
                event = e
                break
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        explanation = behavior_model.explain_prediction(event)
        
        return ApiResponse(
            success=True,
            message="Prediction explanation retrieved",
            data=explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
