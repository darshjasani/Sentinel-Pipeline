"""
CI Pipeline Worker
Processes CI job queue and executes runs
"""

import os
import sys
import time
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path

import redis
from rq import Worker, Queue, Connection
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from executor import JobExecutor


# Database setup (replicate from API)
engine = create_engine(
    settings.database_url,
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def execute_ci_run(run_id_str: str):
    """
    Main worker function to execute a CI run.
    This function is queued by the API and executed by RQ worker.
    """
    print(f"[run_id={run_id_str}] Job started")
    
    run_id = uuid_lib.UUID(run_id_str)
    db = SessionLocal()
    
    try:
        # Import models here to avoid circular imports
        from sqlalchemy import Column, String, Integer, DateTime, Text, DECIMAL, Boolean, ARRAY, ForeignKey
        from sqlalchemy.dialects.postgresql import UUID
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import relationship
        from sqlalchemy.sql import func
        
        Base = declarative_base()
        
        # Define minimal models needed for worker
        class Run(Base):
            __tablename__ = "runs"
            id = Column(UUID(as_uuid=True), primary_key=True)
            repo_id = Column(String(100), nullable=False)
            status = Column(String(20), default="QUEUED")
            job_template = Column(String(100), nullable=False)
            timeout_sec = Column(Integer, default=300)
            queued_at = Column(DateTime, default=func.now())
            started_at = Column(DateTime)
            completed_at = Column(DateTime)
            duration_sec = Column(Integer)
            exit_code = Column(Integer)
            log_path = Column(String(500))
        
        class Repository(Base):
            __tablename__ = "repositories"
            id = Column(String(100), primary_key=True)
            name = Column(String(200), nullable=False)
            path = Column(String(500), nullable=False)
        
        class RunStep(Base):
            __tablename__ = "run_steps"
            id = Column(Integer, primary_key=True)
            run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"))
            step_name = Column(String(200), nullable=False)
            status = Column(String(20), default="PENDING")
            started_at = Column(DateTime)
            completed_at = Column(DateTime)
            duration_sec = Column(Integer)
            exit_code = Column(Integer)
            log_path = Column(String(500))
        
        class Failure(Base):
            __tablename__ = "failures"
            id = Column(Integer, primary_key=True)
            run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"))
            cluster_id = Column(String(100))
            category = Column(String(50), nullable=False)
            message = Column(Text)
            stack_trace = Column(Text)
            fingerprint = Column(String(64), nullable=False)
            confidence = Column(DECIMAL(3, 2), default=0.00)
        
        class TestResult(Base):
            __tablename__ = "test_results"
            id = Column(Integer, primary_key=True)
            run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"))
            test_name = Column(String(500), nullable=False)
            status = Column(String(20), nullable=False)
            duration_ms = Column(Integer)
            error_message = Column(Text)
        
        # Get run
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            print(f"[run_id={run_id_str}] Error: Run not found")
            return
        
        # Get repository
        repo = db.query(Repository).filter(Repository.id == run.repo_id).first()
        if not repo:
            print(f"[run_id={run_id_str}] Error: Repository not found")
            _update_run_failed(db, run, 1, "Repository not found")
            return
        
        # Update run to RUNNING
        run.status = "RUNNING"
        run.started_at = datetime.utcnow()
        db.commit()
        
        print(f"[run_id={run_id_str}] Status: RUNNING")
        
        # Create log directory for this run
        log_dir = os.path.join(settings.log_base_path, run_id_str)
        os.makedirs(log_dir, exist_ok=True)
        
        # Execute job
        executor = JobExecutor(run_id_str, repo.path, log_dir)
        start_time = time.time()
        
        try:
            final_status, exit_code, steps = executor.execute_template(run.job_template)
            duration = int(time.time() - start_time)
            
            # Record steps
            for step_data in steps:
                print(f"[run_id={run_id_str}] Step: {step_data['step_name']} - {step_data['status']}")
                
                step = RunStep(
                    run_id=run_id,
                    step_name=step_data["step_name"],
                    status=step_data["status"],
                    duration_sec=step_data["duration_sec"],
                    exit_code=step_data.get("exit_code"),
                    log_path=step_data.get("log_path")
                )
                db.add(step)
                
                # Parse test results from the "Run tests" step
                if "test" in step_data["step_name"].lower() and step_data.get("stdout"):
                    test_results = executor.parse_test_results(step_data["stdout"])
                    for test in test_results:
                        test_result = TestResult(
                            run_id=run_id,
                            test_name=test["test_name"],
                            status=test["status"],
                            error_message=test.get("error_message")
                        )
                        db.add(test_result)
            
            db.commit()
            
            # Update run completion
            run.status = final_status
            run.completed_at = datetime.utcnow()
            run.duration_sec = duration
            run.exit_code = exit_code
            run.log_path = log_dir
            db.commit()
            
            print(f"[run_id={run_id_str}] Completed with status: {final_status} (exit={exit_code}, duration={duration}s)")
            
            # If failed, record failure for clustering
            if final_status == "FAILED":
                _record_failure(db, run, steps)
            
        except Exception as e:
            print(f"[run_id={run_id_str}] Execution error: {e}")
            _update_run_failed(db, run, 1, str(e))
            raise
        
    except Exception as e:
        print(f"[run_id={run_id_str}] Fatal error: {e}")
        db.rollback()
    finally:
        db.close()


def _update_run_failed(db, run, exit_code, error_message):
    """Helper to mark run as failed"""
    run.status = "FAILED"
    run.completed_at = datetime.utcnow()
    run.exit_code = exit_code
    if run.started_at:
        duration = (run.completed_at - run.started_at).total_seconds()
        run.duration_sec = int(duration)
    db.commit()


def _record_failure(db, run, steps):
    """Record failure information for clustering"""
    # Import clustering functions
    sys.path.insert(0, '/app')
    try:
        # Try to import from API directory
        import importlib.util
        spec = importlib.util.spec_from_file_location("clustering", "/app/../api/clustering.py")
        if spec and spec.loader:
            clustering = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(clustering)
            
            # Extract error from failed step
            failed_step = next((s for s in steps if s["status"] == "FAILED"), None)
            if not failed_step:
                return
            
            error_message = failed_step.get("stderr", "") or failed_step.get("stdout", "")
            if not error_message:
                error_message = f"Step '{failed_step['step_name']}' failed with exit code {failed_step.get('exit_code', 1)}"
            
            # Truncate long error messages
            if len(error_message) > 5000:
                error_message = error_message[:5000] + "\n... (truncated)"
            
            # Generate fingerprint and classify
            fingerprint = clustering.extract_failure_fingerprint(error_message, "")
            category = clustering.classify_failure(error_message, "", failed_step.get("exit_code"))
            
            print(f"[run_id={run.id}] Failure classified: {category}")
            print(f"[run_id={run.id}] Fingerprint: {fingerprint}")
            
            # Create failure record (this will trigger clustering in the API layer)
            from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey
            from sqlalchemy.dialects.postgresql import UUID
            from sqlalchemy.ext.declarative import declarative_base
            
            Base = declarative_base()
            
            class Failure(Base):
                __tablename__ = "failures"
                id = Column(Integer, primary_key=True)
                run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id"))
                cluster_id = Column(String(100))
                category = Column(String(50), nullable=False)
                message = Column(Text)
                stack_trace = Column(Text)
                fingerprint = Column(String(64), nullable=False)
                confidence = Column(DECIMAL(3, 2), default=0.00)
            
            # For simplicity, create basic failure record
            # Full clustering will be handled by API when queried
            failure = Failure(
                run_id=run.id,
                category=category,
                message=error_message[:1000],
                stack_trace="",
                fingerprint=fingerprint,
                confidence=0.95
            )
            db.add(failure)
            db.commit()
            
            print(f"[run_id={run.id}] Failure recorded")
            
    except Exception as e:
        print(f"[run_id={run.id}] Warning: Failed to record failure details: {e}")


if __name__ == "__main__":
    print("🔧 CI Pipeline Worker starting...")
    print(f"Database: {settings.database_url}")
    print(f"Redis: {settings.redis_url}")
    
    # Connect to Redis
    redis_conn = redis.from_url(settings.redis_url)
    
    # Test connection
    try:
        redis_conn.ping()
        print("✔ Redis connection successful")
    except Exception as e:
        print(f"✖ Redis connection failed: {e}")
        sys.exit(1)
    
    # Create queue
    with Connection(redis_conn):
        queue = Queue()
        print(f"✔ Listening to queue: {queue.name}")
        print("✔ Worker ready to process jobs")
        
        # Start worker
        worker = Worker([queue])
        worker.work(with_scheduler=True, logging_level='INFO')

