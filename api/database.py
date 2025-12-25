from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, DECIMAL, Boolean, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import uuid

from config import settings

# Create engine with connection pooling optimized for low RAM
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    runs = relationship("Run", back_populates="repository", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(String(100), ForeignKey("repositories.id"), nullable=False)
    status = Column(String(20), default="QUEUED")
    job_template = Column(String(100), nullable=False)
    triggered_by = Column(String(100))
    timeout_sec = Column(Integer, default=300)
    queued_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_sec = Column(Integer)
    exit_code = Column(Integer)
    log_path = Column(String(500))
    
    repository = relationship("Repository", back_populates="runs")
    steps = relationship("RunStep", back_populates="run", cascade="all, delete-orphan")
    failures = relationship("Failure", back_populates="run", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="run", cascade="all, delete-orphan")


class RunStep(Base):
    __tablename__ = "run_steps"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False)
    step_name = Column(String(200), nullable=False)
    status = Column(String(20), default="PENDING")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_sec = Column(Integer)
    exit_code = Column(Integer)
    log_path = Column(String(500))
    
    run = relationship("Run", back_populates="steps")


class FailureCluster(Base):
    __tablename__ = "failure_clusters"
    
    id = Column(String(100), primary_key=True)
    title = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)
    fingerprint = Column(String(64), nullable=False, unique=True)
    first_seen_at = Column(DateTime, default=func.now())
    last_seen_at = Column(DateTime, default=func.now())
    occurrence_count = Column(Integer, default=1)
    recommended_actions = Column(ARRAY(Text))
    
    failures = relationship("Failure", back_populates="cluster")


class Failure(Base):
    __tablename__ = "failures"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False)
    cluster_id = Column(String(100), ForeignKey("failure_clusters.id"))
    category = Column(String(50), nullable=False)
    message = Column(Text)
    stack_trace = Column(Text)
    fingerprint = Column(String(64), nullable=False)
    confidence = Column(DECIMAL(3, 2), default=0.00)
    created_at = Column(DateTime, default=func.now())
    
    run = relationship("Run", back_populates="failures")
    cluster = relationship("FailureCluster", back_populates="failures")


class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(String(20), primary_key=True)
    status = Column(String(20), default="OPEN")
    title = Column(String(500), nullable=False)
    impact_summary = Column(Text)
    suspected_root_cause = Column(Text)
    start_time = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(20), ForeignKey("incidents.id"), nullable=False)
    event_time = Column(DateTime, default=func.now())
    event_type = Column(String(50), nullable=False)
    details = Column(Text)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"))
    
    incident = relationship("Incident", back_populates="events")


class FlakyTest(Base):
    __tablename__ = "flaky_tests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_name = Column(String(500), nullable=False, unique=True)
    repo_id = Column(String(100), ForeignKey("repositories.id"), nullable=False)
    total_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    failure_rate = Column(DECIMAL(5, 2), default=0.00)
    is_flaky = Column(Boolean, default=False)
    first_detected_at = Column(DateTime, default=func.now())
    last_updated_at = Column(DateTime, default=func.now())


class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"), nullable=False)
    test_name = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)
    duration_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    run = relationship("Run", back_populates="test_results")


# Database utilities
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database():
    """Seed database with initial data - idempotent"""
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Repository).filter(Repository.id == "python-sample").first()
        if existing:
            print("✔ Database already seeded")
            return
        
        # Add sample repository
        repo = Repository(
            id="python-sample",
            name="Python Sample Project",
            path="/app/sample-repos/python-sample"
        )
        db.add(repo)
        db.commit()
        print("✔ Database seeded successfully")
    except Exception as e:
        print(f"✖ Seeding error: {e}")
        db.rollback()
    finally:
        db.close()

