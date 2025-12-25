# Sentinel Pipeline

Sentinel Pipeline is a **production-grade, local CI reliability and failure management system** designed to demonstrate modern CI orchestration, failure triage, and incident management practices.

It runs fully on a local machine using Docker and open-source tooling, with zero paid dependencies. The system is intentionally scoped to mirror real-world CI reliability challenges seen in large engineering organizations, while remaining reproducible and easy to evaluate.

This project is suitable for technical interviews, portfolio demonstration, and hands-on learning of distributed systems, CI infrastructure, and production engineering patterns.

---

## What Sentinel Pipeline Does

Sentinel Pipeline provides an end-to-end CI execution and reliability workflow:

* Executes CI jobs (builds and tests) against sample repositories
* Queues and runs jobs asynchronously using a worker model
* Captures logs and test results with structured metadata
* Classifies failures using deterministic triage logic
* Clusters recurring failures across runs
* Detects flaky tests based on historical behavior
* Automatically creates incidents when failure thresholds are exceeded
* Exposes a web dashboard for runs, failures, and incident review

All components run locally using Docker Compose and can be started with a single command.

---

## Key Capabilities

### CI Job Orchestration

* FIFO job queue backed by Redis
* Worker-based execution with retries and timeouts
* Step-level execution tracking
* Robust handling of worker crashes and orphaned jobs
* Deterministic demo jobs for success, failure, flakiness, timeout, and infrastructure errors

### Failure Triage and Clustering

* Signature-based failure classification
* Normalized fingerprinting of error output
* Clustering of repeated failures across runs
* Structured root cause hints with confidence scores
* Evidence extraction from logs
* Actionable remediation suggestions per failure category

### Flaky Test Detection

* Tracks test outcomes across multiple runs
* Computes failure ratios over a sliding window
* Separates flaky failures from deterministic failures
* Exposes flaky tests in a dedicated dashboard view

### Incident Management

* Automatic incident creation based on configurable thresholds
* Incident timelines with related run history
* Impact summaries and suspected root causes
* Status transitions (open, mitigating, resolved)
* Postmortem-style incident review pages

### Dashboard UI

* Overview page with pipeline health metrics
* Runs list and detailed run views
* Failure clusters and flaky test reporting
* Incident list and incident detail pages
* Graceful handling of empty or partial data states

---

## Architecture Overview

Sentinel Pipeline is implemented as a local distributed system using Docker Compose.

### Services

* **API**: FastAPI service exposing REST endpoints
* **Worker**: Python worker executing CI jobs and triage logic
* **Database**: PostgreSQL for persistent metadata
* **Queue**: Redis for job scheduling and coordination
* **UI**: Web dashboard (React or server-rendered)

All services communicate over local Docker networking. Logs and artifacts are stored on the host filesystem via mounted volumes.

---

## Tech Stack

* Python 3.11
* FastAPI
* PostgreSQL
* Redis
* Docker and Docker Compose
* React (UI)
* Pytest (test execution and validation)

Optional components are designed to be pluggable but are not required for the core system.

---

## Getting Started

### Prerequisites

* Docker
* Docker Compose
* Make
* Approximately 8 GB of available system memory
* Free ports: 3000, 8000, 5432, 6379

### Start the System

```bash
make up
```

This command will:

* Build all Docker images
* Start PostgreSQL, Redis, API, Worker, and UI services
* Run database migrations
* Seed sample repositories and demo data
* Print the local URLs for the API and UI

Expected result:

* API available at [http://localhost:8000](http://localhost:8000)
* UI available at [http://localhost:3000](http://localhost:3000)
* System ready for demo commands

### Stop the System

```bash
make down
```

### Reset All Data

```bash
make reset
```

---

## Demo Commands

Sentinel Pipeline includes deterministic demo scenarios.

```bash
make demo:success     # Successful CI run
make demo:testfail    # Deterministic test failure
make demo:flaky       # Intermittent flaky test behavior
make demo:timeout     # Job timeout scenario
make demo:dns         # Simulated network/DNS failure
make demo:disk        # Simulated disk exhaustion
```

These demos are designed to reliably trigger failure clustering, flaky detection, and incident creation.

---

## API Overview

Key endpoints include:

* `POST /repos` create a repository
* `POST /runs` trigger a CI run
* `GET /runs` list runs
* `GET /runs/{id}` run details with steps, logs, and failures
* `GET /clusters` failure clusters
* `GET /incidents` incident list
* `GET /incidents/{id}` incident detail and timeline
* `GET /health` service health check

The API is designed for clarity and debuggability rather than public exposure.

---

## Project Structure

```
sentinel-pipeline/
  docker-compose.yml
  Makefile
  README.md
  RUNBOOK.md
  ARCHITECTURE.md

  api/
  worker/
  ui/
  sample_repos/
  migrations/
  data/
    logs/
```

---

## Testing

The project includes:

* Unit tests for triage logic, fingerprinting, and incident thresholds
* Integration tests covering run execution and data propagation
* Deterministic test scenarios for reproducibility

Run tests with:

```bash
make test
```

---

## Documentation

* **README.md**: Project overview and setup
* **ARCHITECTURE.md**: System design and data flow
* **RUNBOOK.md**: Operational guidance and incident handling

---

## Intended Use

Sentinel Pipeline is intended for:

* Technical interviews and system design discussions
* Portfolio demonstration of production engineering skills
* Learning CI reliability, failure analysis, and incident management
* Local experimentation without cloud dependencies

It is not intended to replace full CI platforms such as GitHub Actions or Buildkite.

---

## Security Note

This project is for local development and demonstration only.
It does not include authentication, authorization, or hardened isolation.
Do not expose it to untrusted networks without additional security controls.

---

## License

MIT License
