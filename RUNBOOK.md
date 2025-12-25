# Sentinel Pipeline Runbook 🧭

This document describes how to **operate, monitor, and troubleshoot Sentinel Pipeline** during normal operation and failure scenarios.

It is written from the perspective of an **on-call engineer** responsible for CI reliability and system health.

---

## 1. System Overview

Sentinel Pipeline is a local CI reliability system composed of:

* API service (control plane)
* Worker service (job execution and triage)
* PostgreSQL (persistent metadata)
* Redis (job queue and coordination)
* UI (operational dashboard)

All services run via Docker Compose.

---

## 2. Starting and Stopping the System

### Start All Services

```bash
make up
```

Expected outcome:

* All containers start successfully
* Database migrations run automatically
* Sample repositories and demo data are seeded
* API and UI URLs are printed

Healthy system indicators:

* API responds at `http://localhost:8000/health`
* UI loads at `http://localhost:3000`
* No crash loops in container logs

---

### Stop All Services

```bash
make down
```

This stops all containers without deleting data.

---

### Full Reset (Data Wipe)

```bash
make reset
```

This will:

* Stop all services
* Delete database and Redis volumes
* Recreate schema and seed data

Use this when system state becomes inconsistent.

---

## 3. Normal Operation

### Trigger a CI Run

Use demo commands or API endpoints.

Example:

```bash
make demo:success
```

Expected behavior:

* Run appears in the UI
* Status transitions from QUEUED → RUNNING → SUCCEEDED
* Logs and step details are visible

---

### Monitor Runs

Steps:

1. Open the UI
2. Navigate to the Runs page
3. Select a run to view:

   * Step execution
   * Logs
   * Test results
   * Failure information (if any)

---

## 4. Failure Scenarios and Expected Behavior

### Deterministic Test Failure

```bash
make demo:testfail
```

Expected behavior:

* Run fails during test step
* Failure classified as `TEST_FAILURE`
* Failure cluster is created or updated
* Recommended actions are shown in UI

---

### Flaky Test Behavior

```bash
make demo:flaky
```

Expected behavior:

* Multiple runs execute
* Same test alternates between pass and fail
* Flake score increases
* Test appears in the Flaky Tests view
* Flaky failures are separated from deterministic ones

---

### Timeout Failure

```bash
make demo:timeout
```

Expected behavior:

* Job exceeds configured timeout
* Process tree is terminated
* Failure classified as `TIMEOUT`
* Logs indicate timeout enforcement

---

### Network or DNS Failure

```bash
make demo:dns
```

Expected behavior:

* Command fails due to unreachable host
* Failure classified as `NETWORK` or `DNS`
* Recommended actions reference connectivity checks

---

### Disk Exhaustion Simulation

```bash
make demo:disk
```

Expected behavior:

* Job fails when simulated disk threshold is reached
* Failure classified as `RESOURCE_EXHAUSTION`
* Recommended actions reference cleanup or capacity planning

---

## 5. Incident Management 🚨

### When Incidents Are Created

An incident is automatically created when:

* The same failure cluster occurs three times within recent history
* Or burst thresholds are exceeded in a short time window

No manual action is required to create incidents.

---

### Viewing Incidents

Steps:

1. Open the UI
2. Navigate to the Incidents page
3. Select an incident to view:

   * Timeline of related runs
   * Evidence excerpts
   * Suspected root cause
   * Recommended actions

---

### Incident Status Lifecycle

Incidents move through these states:

* **OPEN**: Incident newly created
* **MITIGATING**: Actively being investigated
* **RESOLVED**: Failures no longer occurring

Status updates can be made via UI or API.

---

### Adding Incident Notes

Notes can be appended to an incident to document:

* Investigation steps
* Mitigation actions
* Decisions or observations

Notes appear in the incident timeline.

---

## 6. Troubleshooting Guide

### API Not Responding

Steps:

```bash
make logs-api
```

Checks:

* API container is running
* Database connectivity is healthy
* `/health` endpoint returns success

If needed:

```bash
docker compose restart api
```

---

### Worker Not Executing Jobs

Steps:

```bash
make logs-worker
```

Checks:

* Worker container is running
* Redis is reachable
* Jobs are present in the queue
* No orphaned runs are accumulating

If needed:

```bash
docker compose restart worker
```

---

### Database Errors

Steps:

```bash
make shell-db
```

Checks:

* Tables exist
* Migrations ran successfully
* No schema mismatches

If state is corrupted:

```bash
make reset
```

---

### Logs Missing or Incomplete

Checks:

* `data/logs/` directory exists
* Docker volume mounts are correct
* Worker has write permissions
* Disk space is available

---

## 7. Adding New Failure Signatures

To add a new failure signature:

1. Locate the triage signature definitions
2. Add a regex pattern and category
3. Define recommended remediation actions
4. Add unit tests for the new signature
5. Restart services

This ensures new failures are classified consistently.

---

## 8. Recovery Procedures

If the system enters an unrecoverable state:

```bash
make down
make reset
make up
```

This restores Sentinel Pipeline to a clean, known-good state.

---

## 9. Known Limitations

* No authentication or access control
* Local-only execution model
* Not hardened for untrusted code execution
* Not designed for horizontal scaling

These limitations are intentional for a demo system.

---

## 10. Summary

This runbook defines how Sentinel Pipeline is **operated in practice**.

If something breaks:

* Check logs first
* Inspect run and incident state
* Follow deterministic recovery steps

Sentinel Pipeline is designed so failures are **visible, explainable, and recoverable**.
