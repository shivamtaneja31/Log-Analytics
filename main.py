from fastapi import FastAPI, WebSocket, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict
import json
import asyncio
import logging
from collections import defaultdict

from .database import get_db, Log, Alert, AnomalyMetrics
from .models import LogCreate, AlertCreate, LogAnalytics, AlertSummary
from .log_generator import LogGenerator

app = FastAPI(title="Log Aggregation POC")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize log generator
log_generator = LogGenerator()

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Anomaly detection thresholds
THRESHOLDS = {
    "error_rate": 0.05,  # 5% error rate threshold
    "error_burst": 5,    # 5 errors within burst_window
    "burst_window": 60,  # 60 seconds window
}

# In-memory storage for recent errors (for burst detection)
recent_errors: List[datetime] = []

async def broadcast_message(message: Dict):
    """Broadcast message to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            logger.error("Error broadcasting message to client")

def check_for_anomalies(log: Dict, db: Session) -> bool:
    """Check for anomalies in log patterns"""
    is_anomaly = False
    
    # Clean up old errors from recent_errors
    current_time = datetime.utcnow()
    global recent_errors
    recent_errors = [t for t in recent_errors if t > current_time - timedelta(seconds=THRESHOLDS["burst_window"])]
    
    if log["level"] == "ERROR":
        recent_errors.append(current_time)
        
        # Check for error burst
        if len(recent_errors) >= THRESHOLDS["error_burst"]:
            is_anomaly = True
            create_alert(db, {
                "severity": "HIGH",
                "message": f"Error burst detected: {len(recent_errors)} errors in {THRESHOLDS['burst_window']} seconds",
                "log_id": log.get("id", 0)
            })
    
    return is_anomaly

def create_alert(db: Session, alert_data: Dict):
    """Create a new alert"""
    alert = Alert(**alert_data)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        active_connections.append(websocket)
        
        # Keep the connection alive
        while True:
            try:
                # Wait for any message
                data = await websocket.receive_text()
                # Echo back to confirm connection is alive
                await websocket.send_text(data)
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.post("/logs/", response_model=None)
async def create_log(log: LogCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create a new log entry"""
    db_log = Log(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    # Check for anomalies in background
    background_tasks.add_task(check_for_anomalies, log.dict(), db)
    
    # Broadcast log to connected clients
    background_tasks.add_task(broadcast_message, {"type": "new_log", "data": log.dict()})
    
    # Convert SQLAlchemy model to dict for response
    return {
        "id": db_log.id,
        "timestamp": db_log.timestamp,
        "level": db_log.level,
        "service": db_log.service,
        "message": db_log.message,
        "error_code": db_log.error_code,
        "stack_trace": db_log.stack_trace
    }

@app.get("/logs/", response_model=None)
def get_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get paginated logs"""
    logs = db.query(Log).order_by(Log.timestamp.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp,
            "level": log.level,
            "service": log.service,
            "message": log.message,
            "error_code": log.error_code,
            "stack_trace": log.stack_trace
        }
        for log in logs
    ]

@app.get("/alerts/", response_model=None)
def get_alerts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get paginated alerts"""
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": alert.id,
            "timestamp": alert.timestamp,
            "severity": alert.severity,
            "message": alert.message,
            "log_id": alert.log_id,
            "is_resolved": alert.is_resolved,
            "resolved_at": alert.resolved_at
        }
        for alert in alerts
    ]

@app.get("/analytics/logs", response_model=None)
def get_log_analytics(db: Session = Depends(get_db)):
    """Get log analytics"""
    total_logs = db.query(Log).count()
    error_count = db.query(Log).filter(Log.level == "ERROR").count()
    warning_count = db.query(Log).filter(Log.level == "WARNING").count()
    error_rate = error_count / total_logs if total_logs > 0 else 0
    recent_errors = db.query(Log).filter(Log.level == "ERROR").order_by(Log.timestamp.desc()).limit(5).all()
    
    return {
        "total_logs": total_logs,
        "error_count": error_count,
        "warning_count": warning_count,
        "error_rate": error_rate,
        "recent_errors": [
            {
                "id": log.id,
                "timestamp": log.timestamp,
                "level": log.level,
                "service": log.service,
                "message": log.message,
                "error_code": log.error_code,
                "stack_trace": log.stack_trace
            }
            for log in recent_errors
        ]
    }

@app.get("/analytics/alerts", response_model=None)
def get_alert_analytics(db: Session = Depends(get_db)):
    """Get alert analytics"""
    total_alerts = db.query(Alert).count()
    active_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
    
    # Count alerts by severity
    severity_counts = defaultdict(int)
    for alert in db.query(Alert).all():
        severity_counts[alert.severity] += 1
    
    recent_alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(5).all()
    
    return {
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "alerts_by_severity": dict(severity_counts),
        "recent_alerts": [
            {
                "id": alert.id,
                "timestamp": alert.timestamp,
                "severity": alert.severity,
                "message": alert.message,
                "log_id": alert.log_id,
                "is_resolved": alert.is_resolved,
                "resolved_at": alert.resolved_at
            }
            for alert in recent_alerts
        ]
    }

@app.post("/simulate/normal")
async def simulate_normal_traffic(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Simulate normal traffic with occasional warnings and errors"""
    log_data = log_generator.simulate_normal_traffic()
    log = LogCreate(**log_data)
    return await create_log(log, background_tasks, db)

@app.post("/simulate/incident")
async def simulate_incident(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Simulate an incident with burst errors"""
    logs = []
    for log_data in log_generator.simulate_incident():
        log = LogCreate(**log_data)
        db_log = await create_log(log, background_tasks, db)
        logs.append(db_log)
    return {"message": "Incident simulated", "logs_generated": len(logs)}

# Mount static files after all API routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
