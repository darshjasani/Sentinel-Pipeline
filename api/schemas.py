"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Request schemas
class RunCreate(BaseModel):
    repo_id: str
    job_template: str
    timeout_sec: int = 300
    triggered_by: Optional[str] = "manual"


# Response schemas
class StepResponse(BaseModel):
    step_name: str
    status: str
    duration_sec: Optional[int] = None
    exit_code: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FailureInfo(BaseModel):
    category: str
    cluster_id: Optional[str] = None
    confidence: Optional[float] = None
    message: Optional[str] = None


class RunResponse(BaseModel):
    run_id: UUID
    repo: str
    status: str
    job_template: str
    triggered_by: Optional[str] = None
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    exit_code: Optional[int] = None
    steps: List[StepResponse] = []
    failure: Optional[FailureInfo] = None

    class Config:
        from_attributes = True


class RunListItem(BaseModel):
    run_id: UUID
    repo: str
    status: str
    job_template: str
    queued_at: datetime
    duration_sec: Optional[int] = None

    class Config:
        from_attributes = True


class FailureClusterResponse(BaseModel):
    cluster_id: str
    title: str
    category: str
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int
    recommended_actions: List[str]

    class Config:
        from_attributes = True


class IncidentEventResponse(BaseModel):
    event_time: datetime
    event_type: str
    details: Optional[str] = None
    run_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    incident_id: str
    status: str
    title: str
    impact_summary: Optional[str] = None
    suspected_root_cause: Optional[str] = None
    start_time: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    timeline: List[IncidentEventResponse] = []

    class Config:
        from_attributes = True


class IncidentListItem(BaseModel):
    incident_id: str
    status: str
    title: str
    start_time: datetime

    class Config:
        from_attributes = True


class FlakyTestResponse(BaseModel):
    test_name: str
    repo_id: str
    total_runs: int
    failed_runs: int
    failure_rate: float
    is_flaky: bool
    status: str  # FLAKY or DETERMINISTIC

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_runs_24h: int
    success_count: int
    failure_count: int
    success_rate: float
    failure_rate: float
    avg_duration_sec: float
    open_incidents: int
    flaky_tests_detected: int


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str

