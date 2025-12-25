"""
CRUD operations for database
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from database import Run, RunStep, Failure, FailureCluster, Incident, IncidentEvent, FlakyTest, Repository, TestResult
from clustering import (
    extract_failure_fingerprint,
    classify_failure,
    generate_cluster_title,
    generate_recommendations,
    find_similar_cluster,
    generate_incident_summary,
    generate_suspected_root_cause
)
from config import settings


def create_run(db: Session, repo_id: str, job_template: str, timeout_sec: int, triggered_by: str) -> Run:
    """Create a new CI run"""
    run = Run(
        id=uuid.uuid4(),
        repo_id=repo_id,
        job_template=job_template,
        timeout_sec=timeout_sec,
        triggered_by=triggered_by,
        status="QUEUED"
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: uuid.UUID) -> Optional[Run]:
    """Get a run by ID"""
    return db.query(Run).filter(Run.id == run_id).first()


def get_runs(db: Session, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Run]:
    """Get list of runs with optional filtering"""
    query = db.query(Run)
    if status:
        query = query.filter(Run.status == status)
    return query.order_by(desc(Run.queued_at)).limit(limit).offset(offset).all()


def update_run_status(db: Session, run_id: uuid.UUID, status: str, **kwargs) -> Run:
    """Update run status and other fields"""
    run = get_run(db, run_id)
    if run:
        run.status = status
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        db.commit()
        db.refresh(run)
    return run


def create_run_step(db: Session, run_id: uuid.UUID, step_name: str) -> RunStep:
    """Create a new run step"""
    step = RunStep(
        run_id=run_id,
        step_name=step_name,
        status="PENDING"
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def update_step_status(db: Session, step_id: int, status: str, **kwargs) -> RunStep:
    """Update step status"""
    step = db.query(RunStep).filter(RunStep.id == step_id).first()
    if step:
        step.status = status
        for key, value in kwargs.items():
            if hasattr(step, key):
                setattr(step, key, value)
        db.commit()
        db.refresh(step)
    return step


def record_test_result(db: Session, run_id: uuid.UUID, test_name: str, status: str, duration_ms: Optional[int], error_message: Optional[str]):
    """Record a test result (triggers flaky test detection via database trigger)"""
    test_result = TestResult(
        run_id=run_id,
        test_name=test_name,
        status=status,
        duration_ms=duration_ms,
        error_message=error_message
    )
    db.add(test_result)
    db.commit()


def create_or_update_failure_cluster(
    db: Session,
    error_message: str,
    stack_trace: str,
    exit_code: Optional[int]
) -> tuple[FailureCluster, float]:
    """
    Create a new failure cluster or update existing one.
    Returns (cluster, confidence)
    """
    # Generate fingerprint and classify
    fingerprint = extract_failure_fingerprint(error_message, stack_trace)
    category = classify_failure(error_message, stack_trace, exit_code)
    
    # Check for existing cluster with same fingerprint
    existing = db.query(FailureCluster).filter(FailureCluster.fingerprint == fingerprint).first()
    
    if existing:
        # Update existing cluster
        existing.last_seen_at = datetime.utcnow()
        existing.occurrence_count += 1
        db.commit()
        db.refresh(existing)
        return existing, 1.0
    
    # Check for similar clusters
    all_clusters = db.query(FailureCluster.fingerprint, FailureCluster.id).all()
    similar = find_similar_cluster(fingerprint, error_message, [(c[0], c[1]) for c in all_clusters])
    
    if similar:
        cluster_id, confidence = similar
        cluster = db.query(FailureCluster).filter(FailureCluster.id == cluster_id).first()
        if cluster:
            cluster.last_seen_at = datetime.utcnow()
            cluster.occurrence_count += 1
            db.commit()
            db.refresh(cluster)
            return cluster, confidence
    
    # Create new cluster
    cluster_id = fingerprint[:8]
    title = generate_cluster_title(error_message, category)
    recommendations = generate_recommendations(category, error_message, stack_trace)
    
    cluster = FailureCluster(
        id=cluster_id,
        title=title,
        category=category,
        fingerprint=fingerprint,
        recommended_actions=recommendations
    )
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    
    return cluster, 1.0


def record_failure(
    db: Session,
    run_id: uuid.UUID,
    error_message: str,
    stack_trace: str,
    exit_code: Optional[int]
) -> Failure:
    """Record a failure and associate with cluster"""
    # Create or update cluster
    cluster, confidence = create_or_update_failure_cluster(db, error_message, stack_trace, exit_code)
    
    # Create failure record
    fingerprint = extract_failure_fingerprint(error_message, stack_trace)
    category = classify_failure(error_message, stack_trace, exit_code)
    
    failure = Failure(
        run_id=run_id,
        cluster_id=cluster.id,
        category=category,
        message=error_message,
        stack_trace=stack_trace,
        fingerprint=fingerprint,
        confidence=confidence
    )
    db.add(failure)
    db.commit()
    db.refresh(failure)
    
    # Check if incident should be created
    check_and_create_incident(db, cluster)
    
    return failure


def check_and_create_incident(db: Session, cluster: FailureCluster):
    """Create incident if failure threshold is exceeded and no open incident exists"""
    if cluster.occurrence_count < settings.incident_threshold:
        return
    
    # Check if there's already an open incident for this cluster
    # We'll associate incidents with clusters by checking recent failures
    recent_failures = db.query(Failure).filter(
        Failure.cluster_id == cluster.id
    ).order_by(desc(Failure.created_at)).limit(settings.incident_threshold).all()
    
    if len(recent_failures) < settings.incident_threshold:
        return
    
    # Check if an open incident already exists for any of these runs
    run_ids = [f.run_id for f in recent_failures]
    existing_incident = db.query(Incident).join(IncidentEvent).filter(
        IncidentEvent.run_id.in_(run_ids),
        Incident.status == "OPEN"
    ).first()
    
    if existing_incident:
        # Add event to existing incident
        event = IncidentEvent(
            incident_id=existing_incident.id,
            event_type="RUN_FAILED",
            details=f"Run {recent_failures[0].run_id} failed with {cluster.category}",
            run_id=recent_failures[0].run_id
        )
        db.add(event)
        db.commit()
        return
    
    # Create new incident
    incident_number = db.query(func.count(Incident.id)).scalar() + 1
    incident_id = f"INC-{incident_number:04d}"
    
    # Get repo_id from the run
    run = db.query(Run).filter(Run.id == recent_failures[0].run_id).first()
    repo_id = run.repo_id if run else "unknown"
    
    incident = Incident(
        id=incident_id,
        status="OPEN",
        title=cluster.title,
        impact_summary=generate_incident_summary(cluster.title, cluster.occurrence_count, repo_id),
        suspected_root_cause=generate_suspected_root_cause(cluster.title, cluster.category)
    )
    db.add(incident)
    db.flush()
    
    # Add events for all related failures
    for failure in recent_failures:
        event = IncidentEvent(
            incident_id=incident_id,
            event_type="RUN_FAILED",
            details=f"Run {failure.run_id} failed with {cluster.category}",
            run_id=failure.run_id,
            event_time=failure.created_at
        )
        db.add(event)
    
    # Add incident creation event
    creation_event = IncidentEvent(
        incident_id=incident_id,
        event_type="INCIDENT_CREATED",
        details="Failure threshold exceeded"
    )
    db.add(creation_event)
    
    db.commit()


def get_failure_cluster(db: Session, cluster_id: str) -> Optional[FailureCluster]:
    """Get failure cluster by ID"""
    return db.query(FailureCluster).filter(FailureCluster.id == cluster_id).first()


def get_incidents(db: Session, status: Optional[str] = None) -> List[Incident]:
    """Get all incidents with optional status filter"""
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    return query.order_by(desc(Incident.start_time)).all()


def get_incident(db: Session, incident_id: str) -> Optional[Incident]:
    """Get incident by ID"""
    return db.query(Incident).filter(Incident.id == incident_id).first()


def get_flaky_tests(db: Session, repo_id: Optional[str] = None) -> List[FlakyTest]:
    """Get flaky tests with optional repo filter"""
    query = db.query(FlakyTest).filter(FlakyTest.total_runs >= settings.flaky_test_min_runs)
    if repo_id:
        query = query.filter(FlakyTest.repo_id == repo_id)
    return query.order_by(desc(FlakyTest.failure_rate)).all()


def get_dashboard_stats(db: Session) -> dict:
    """Get dashboard statistics for last 24 hours"""
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    runs = db.query(Run).filter(Run.queued_at >= cutoff).all()
    total = len(runs)
    success = len([r for r in runs if r.status == "SUCCEEDED"])
    failed = len([r for r in runs if r.status == "FAILED"])
    
    avg_duration = 0
    if runs:
        durations = [r.duration_sec for r in runs if r.duration_sec]
        avg_duration = sum(durations) / len(durations) if durations else 0
    
    open_incidents = db.query(func.count(Incident.id)).filter(Incident.status == "OPEN").scalar()
    flaky_count = db.query(func.count(FlakyTest.id)).filter(FlakyTest.is_flaky == True).scalar()
    
    return {
        "total_runs_24h": total,
        "success_count": success,
        "failure_count": failed,
        "success_rate": round((success / total * 100) if total > 0 else 0, 1),
        "failure_rate": round((failed / total * 100) if total > 0 else 0, 1),
        "avg_duration_sec": round(avg_duration, 1),
        "open_incidents": open_incidents,
        "flaky_tests_detected": flaky_count
    }

