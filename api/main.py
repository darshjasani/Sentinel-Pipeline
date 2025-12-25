"""
CI Pipeline FastAPI Application
Main API endpoints for CI run management, incident tracking, and dashboard
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import redis
from rq import Queue
import uuid

from database import get_db, seed_database, engine, Base
from schemas import (
    RunCreate, RunResponse, RunListItem, FailureClusterResponse,
    IncidentResponse, IncidentListItem, FlakyTestResponse,
    DashboardStats, HealthResponse, StepResponse, FailureInfo
)
import crud
from config import settings

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="CI Pipeline API",
    description="Production-grade CI/CD pipeline management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection for job queue
try:
    redis_conn = redis.from_url(settings.redis_url)
    job_queue = Queue(connection=redis_conn, default_timeout=600)
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")
    redis_conn = None
    job_queue = None


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 CI Pipeline API starting...")
    try:
        seed_database()
    except Exception as e:
        print(f"⚠️  Startup warning: {e}")


@app.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    db_status = "ok"
    redis_status = "ok"
    
    try:
        # Test database
        db.execute("SELECT 1")
    except Exception:
        db_status = "error"
    
    try:
        # Test Redis
        if redis_conn:
            redis_conn.ping()
        else:
            redis_status = "error"
    except Exception:
        redis_status = "error"
    
    overall_status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    
    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status
    }


@app.post("/runs", response_model=RunResponse, status_code=201)
def create_run(run_data: RunCreate, db: Session = Depends(get_db)):
    """
    Trigger a new CI run.
    Job will be queued and executed by worker.
    """
    # Validate repository exists
    repo = db.query(crud.Repository).filter(crud.Repository.id == run_data.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{run_data.repo_id}' not found")
    
    # Create run record
    run = crud.create_run(
        db=db,
        repo_id=run_data.repo_id,
        job_template=run_data.job_template,
        timeout_sec=run_data.timeout_sec,
        triggered_by=run_data.triggered_by
    )
    
    # Queue job for worker
    if job_queue:
        try:
            job_queue.enqueue(
                'worker.execute_ci_run',
                str(run.id),
                job_timeout=run_data.timeout_sec + 30  # Add buffer
            )
        except Exception as e:
            print(f"Warning: Failed to queue job: {e}")
    
    return {
        "run_id": run.id,
        "repo": run.repo_id,
        "status": run.status,
        "job_template": run.job_template,
        "triggered_by": run.triggered_by,
        "queued_at": run.queued_at,
        "started_at": None,
        "completed_at": None,
        "duration_sec": None,
        "exit_code": None,
        "steps": [],
        "failure": None
    }


@app.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get detailed information about a specific run"""
    run = crud.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Build response
    steps = []
    for step in run.steps:
        steps.append({
            "step_name": step.step_name,
            "status": step.status,
            "duration_sec": step.duration_sec,
            "exit_code": step.exit_code,
            "started_at": step.started_at,
            "completed_at": step.completed_at
        })
    
    failure_info = None
    if run.failures:
        failure = run.failures[0]
        failure_info = {
            "category": failure.category,
            "cluster_id": failure.cluster_id,
            "confidence": float(failure.confidence) if failure.confidence else None,
            "message": failure.message
        }
    
    return {
        "run_id": run.id,
        "repo": run.repo_id,
        "status": run.status,
        "job_template": run.job_template,
        "triggered_by": run.triggered_by,
        "queued_at": run.queued_at,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "duration_sec": run.duration_sec,
        "exit_code": run.exit_code,
        "steps": steps,
        "failure": failure_info
    }


@app.get("/runs", response_model=List[RunListItem])
def list_runs(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List recent CI runs with optional filtering"""
    runs = crud.get_runs(db, limit=limit, offset=offset, status=status)
    
    return [
        {
            "run_id": run.id,
            "repo": run.repo_id,
            "status": run.status,
            "job_template": run.job_template,
            "queued_at": run.queued_at,
            "duration_sec": run.duration_sec
        }
        for run in runs
    ]


@app.get("/clusters/{cluster_id}", response_model=FailureClusterResponse)
def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    """Get details about a failure cluster"""
    cluster = crud.get_failure_cluster(db, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    return {
        "cluster_id": cluster.id,
        "title": cluster.title,
        "category": cluster.category,
        "first_seen_at": cluster.first_seen_at,
        "last_seen_at": cluster.last_seen_at,
        "occurrence_count": cluster.occurrence_count,
        "recommended_actions": cluster.recommended_actions or []
    }


@app.get("/incidents", response_model=List[IncidentListItem])
def list_incidents(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List incidents with optional status filter"""
    incidents = crud.get_incidents(db, status=status)
    
    return [
        {
            "incident_id": incident.id,
            "status": incident.status,
            "title": incident.title,
            "start_time": incident.start_time
        }
        for incident in incidents
    ]


@app.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    """Get detailed incident information including timeline"""
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    timeline = [
        {
            "event_time": event.event_time,
            "event_type": event.event_type,
            "details": event.details,
            "run_id": event.run_id
        }
        for event in sorted(incident.events, key=lambda e: e.event_time)
    ]
    
    return {
        "incident_id": incident.id,
        "status": incident.status,
        "title": incident.title,
        "impact_summary": incident.impact_summary,
        "suspected_root_cause": incident.suspected_root_cause,
        "start_time": incident.start_time,
        "resolved_at": incident.resolved_at,
        "resolution_notes": incident.resolution_notes,
        "timeline": timeline
    }


@app.patch("/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: str,
    resolution_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Mark an incident as resolved"""
    incident = crud.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    from datetime import datetime
    incident.status = "RESOLVED"
    incident.resolved_at = datetime.utcnow()
    if resolution_notes:
        incident.resolution_notes = resolution_notes
    
    # Add resolution event
    event = crud.IncidentEvent(
        incident_id=incident_id,
        event_type="INCIDENT_RESOLVED",
        details=resolution_notes or "Incident marked as resolved"
    )
    db.add(event)
    
    db.commit()
    
    return {"status": "ok", "message": "Incident resolved"}


@app.get("/flaky-tests", response_model=List[FlakyTestResponse])
def list_flaky_tests(
    repo_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List flaky tests detected in the system"""
    flaky_tests = crud.get_flaky_tests(db, repo_id=repo_id)
    
    return [
        {
            "test_name": test.test_name,
            "repo_id": test.repo_id,
            "total_runs": test.total_runs,
            "failed_runs": test.failed_runs,
            "failure_rate": float(test.failure_rate),
            "is_flaky": test.is_flaky,
            "status": "FLAKY" if test.is_flaky else ("DETERMINISTIC" if test.failure_rate >= 90 else "STABLE")
        }
        for test in flaky_tests
    ]


@app.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard statistics for the last 24 hours"""
    stats = crud.get_dashboard_stats(db)
    return stats


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "CI Pipeline API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "runs": "/runs",
            "incidents": "/incidents",
            "flaky_tests": "/flaky-tests",
            "dashboard": "/dashboard"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

