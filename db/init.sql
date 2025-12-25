-- CI Pipeline Database Schema
-- Optimized for 8GB RAM systems with proper indexing

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Repositories table
CREATE TABLE repositories (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CI Runs table
CREATE TABLE runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_id VARCHAR(100) NOT NULL REFERENCES repositories(id),
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    job_template VARCHAR(100) NOT NULL,
    triggered_by VARCHAR(100),
    timeout_sec INTEGER DEFAULT 300,
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_sec INTEGER,
    exit_code INTEGER,
    log_path VARCHAR(500)
);

-- Indexes for performance
CREATE INDEX idx_runs_repo_id ON runs(repo_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_runs_queued_at ON runs(queued_at DESC);
CREATE INDEX idx_runs_repo_status ON runs(repo_id, status);

-- Run steps table
CREATE TABLE run_steps (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    step_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_sec INTEGER,
    exit_code INTEGER,
    log_path VARCHAR(500)
);

CREATE INDEX idx_run_steps_run_id ON run_steps(run_id);

-- Failure clusters table (for grouping similar failures)
CREATE TABLE failure_clusters (
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    category VARCHAR(50) NOT NULL,
    fingerprint VARCHAR(64) NOT NULL UNIQUE,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    occurrence_count INTEGER DEFAULT 1,
    recommended_actions TEXT[]
);

CREATE INDEX idx_failure_clusters_category ON failure_clusters(category);
CREATE INDEX idx_failure_clusters_fingerprint ON failure_clusters(fingerprint);

-- Failures table (individual failure instances)
CREATE TABLE failures (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    cluster_id VARCHAR(100) REFERENCES failure_clusters(id),
    category VARCHAR(50) NOT NULL,
    message TEXT,
    stack_trace TEXT,
    fingerprint VARCHAR(64) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_failures_run_id ON failures(run_id);
CREATE INDEX idx_failures_cluster_id ON failures(cluster_id);
CREATE INDEX idx_failures_fingerprint ON failures(fingerprint);

-- Incidents table
CREATE TABLE incidents (
    id VARCHAR(20) PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    title VARCHAR(500) NOT NULL,
    impact_summary TEXT,
    suspected_root_cause TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_start_time ON incidents(start_time DESC);

-- Incident events timeline
CREATE TABLE incident_events (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(20) NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,
    details TEXT,
    run_id UUID REFERENCES runs(id)
);

CREATE INDEX idx_incident_events_incident_id ON incident_events(incident_id);
CREATE INDEX idx_incident_events_event_time ON incident_events(event_time DESC);

-- Flaky tests table
CREATE TABLE flaky_tests (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(500) NOT NULL UNIQUE,
    repo_id VARCHAR(100) NOT NULL REFERENCES repositories(id),
    total_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,
    failure_rate DECIMAL(5,2) DEFAULT 0.00,
    is_flaky BOOLEAN DEFAULT FALSE,
    first_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flaky_tests_repo_id ON flaky_tests(repo_id);
CREATE INDEX idx_flaky_tests_is_flaky ON flaky_tests(is_flaky);
CREATE INDEX idx_flaky_tests_failure_rate ON flaky_tests(failure_rate DESC);

-- Test results table
CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    test_name VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL,
    duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_results_run_id ON test_results(run_id);
CREATE INDEX idx_test_results_test_name ON test_results(test_name);
CREATE INDEX idx_test_results_status ON test_results(status);

-- Function to update flaky test statistics
CREATE OR REPLACE FUNCTION update_flaky_test_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO flaky_tests (test_name, repo_id, total_runs, failed_runs)
    SELECT 
        NEW.test_name,
        r.repo_id,
        1,
        CASE WHEN NEW.status = 'FAILED' THEN 1 ELSE 0 END
    FROM runs r
    WHERE r.id = NEW.run_id
    ON CONFLICT (test_name) DO UPDATE
    SET 
        total_runs = flaky_tests.total_runs + 1,
        failed_runs = flaky_tests.failed_runs + CASE WHEN NEW.status = 'FAILED' THEN 1 ELSE 0 END,
        failure_rate = ROUND(((flaky_tests.failed_runs + CASE WHEN NEW.status = 'FAILED' THEN 1 ELSE 0 END)::DECIMAL / (flaky_tests.total_runs + 1)::DECIMAL * 100), 2),
        is_flaky = (
            (flaky_tests.failed_runs + CASE WHEN NEW.status = 'FAILED' THEN 1 ELSE 0 END)::DECIMAL / 
            (flaky_tests.total_runs + 1)::DECIMAL
        ) BETWEEN 0.1 AND 0.9,
        last_updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update flaky test stats
CREATE TRIGGER trigger_update_flaky_test_stats
AFTER INSERT ON test_results
FOR EACH ROW
EXECUTE FUNCTION update_flaky_test_stats();

-- Initial seed data
INSERT INTO repositories (id, name, path) VALUES
('python-sample', 'Python Sample Project', '/app/sample-repos/python-sample');

