# Architecture Overview 🏗️

Sentinel Pipeline is a **local, production-style CI reliability system** composed of multiple cooperating services.
It is designed to model how modern CI platforms execute jobs, analyze failures, and manage incidents, while remaining lightweight and reproducible on a single machine.

The architecture emphasizes **clear separation of responsibilities**, **deterministic behavior**, and **operational visibility**.

---

## High-Level Architecture

Sentinel Pipeline runs as a small distributed system using Docker Compose.

```
+-------------------+
|        UI         |
|  Web Dashboard    |
|  :3000            |
+---------+---------+
          |
          | HTTP
          |
+---------v---------+        +-------------+
|        API        | <----> |    Redis    |
|     FastAPI       |        |   Queue     |
|     :8000         |        |   :6379     |
+---------+---------+        +------+------+
          |                          |
          |                          |
          |                          v
          |                  +-------+-------+
          |                  |     Worker    |
          |                  |  CI Executor  |
          |                  +-------+-------+
          |                          |
          v                          |
+-------------------+                |
|   PostgreSQL      | <-------------+
|   Metadata DB     |
|   :5432           |
+-------------------+
```

---

## Design Principles

* Deterministic execution for demos and testing
* Clear ownership per service
* Resilience to partial failures
* Explicit state transitions
* No dependency on cloud services or paid tooling

---

## Core Services

### API Service (FastAPI) 🌐

The API service acts as the **control plane** of Sentinel Pipeline.

**Responsibilities**

* Accept CI run requests
* Validate job configuration
* Persist metadata to PostgreSQL
* Expose read APIs for runs, failures, and incidents
* Enqueue jobs into Redis
* Serve structured data to the UI

**Key Characteristics**

* Stateless
* Idempotent where possible
* No direct execution of CI commands
* Clear run and incident lifecycle management

---

### Worker Service ⚙️

The worker is the **execution and analysis engine**.

**Responsibilities**

* Dequeue jobs from Redis
* Execute CI steps sequentially
* Enforce timeouts and basic resource checks
* Stream logs to disk
* Parse test results
* Perform failure triage and clustering
* Trigger incident creation when thresholds are exceeded

**Key Characteristics**

* Stateful during job execution
* Crash-tolerant with heartbeat tracking
* Supports retries for infrastructure-related failures
* Deterministic behavior for demo scenarios

---

### Redis 🧵

Redis is used as a **lightweight coordination layer**.

**Responsibilities**

* FIFO job queue
* Temporary job state
* Worker heartbeat and liveness checks

Redis does not store long-term or authoritative data.

---

### PostgreSQL 🗄️

PostgreSQL is the **system of record**.

**Responsibilities**

* Store repositories, runs, steps, and test results
* Track failure clusters and incidents
* Maintain referential integrity
* Support historical analysis for flaky test detection

The schema is optimized for correctness and clarity rather than massive scale.

---

### UI 📊

The UI is a **read-only operational dashboard**.

**Responsibilities**

* Display pipeline health metrics
* Visualize run execution and logs
* Surface failure clusters and flaky tests
* Present incident timelines and postmortem data

The UI avoids complex client-side state and relies on API queries.

---

## Execution Flow

### CI Run Lifecycle

1. User triggers a run via API or Make command
2. API validates input and creates a run record
3. Job is enqueued in Redis
4. Worker dequeues the job
5. Run status transitions to RUNNING
6. Worker executes steps sequentially
7. Logs are streamed to disk
8. Test results are parsed and stored
9. Failure triage runs if the job fails
10. Failure clusters are updated
11. Incident thresholds are evaluated
12. Run transitions to a terminal state

---

## Failure Triage Architecture 🧠

The triage engine is the core differentiator of Sentinel Pipeline.

**Inputs**

* Step logs
* Exit codes
* Parsed test results
* Known failure signatures

**Processing**

* Normalize error output
* Extract key error lines
* Generate a failure fingerprint
* Match against known signatures
* Assign a failure category
* Generate structured root cause hints

**Outputs**

* Failure classification
* Confidence score
* Evidence excerpts
* Recommended remediation actions

---

## Failure Clustering

Failures are grouped using a **fingerprint-based approach**.

* Error messages are normalized to remove noise
* A stable hash is generated from key error lines
* Repeated fingerprints across runs form a cluster
* Cluster metadata tracks frequency and recency

This enables reliable detection of recurring issues.

---

## Flaky Test Detection 🧪

Flaky detection is performed by analyzing historical test outcomes.

* Test results are tracked per test name
* Failure ratios are computed over a sliding window
* Tests with intermittent failure rates are flagged as flaky
* Flaky failures are treated separately from deterministic failures

---

## Incident Management 🚨

Incidents represent **persistent or high-impact CI failures**.

**Incident Creation**

* Triggered when a failure cluster exceeds defined thresholds
* Automatically linked to related runs

**Incident Lifecycle**

* OPEN when first created
* MITIGATING during investigation
* RESOLVED when failures stop occurring

**Incident Data**

* Timeline of related events
* Suspected root cause
* Evidence excerpts
* Recommended actions
* Postmortem fields

---

## Failure Injection Design

Sentinel Pipeline includes controlled failure injection for demos.

* Deterministic test failures
* Flaky test simulation using seeded randomness
* Timeout simulation via long-running commands
* Network and DNS failure simulation
* Disk exhaustion simulation using configurable thresholds

All failure modes are reproducible across machines.

---

## Extensibility

The architecture is designed to support future enhancements:

* Metrics export and dashboards
* Local LLM integration for summarization
* Authentication and RBAC
* Multi-worker scaling

These are intentionally excluded from the core MVP.

---

## Non-Goals

* Cloud-native deployment
* Full CI platform replacement
* Arbitrary command execution from UI
* Multi-tenant security isolation
