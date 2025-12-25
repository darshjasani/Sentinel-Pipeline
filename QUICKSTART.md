# 🚀 Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- [x] Docker Desktop installed and running
- [x] At least 8GB RAM available
- [x] Ports free: 3000, 8000, 5432, 6379

## Step-by-Step Setup

### 1. Start the System (60 seconds)

```bash
cd "Sentinel Pipeline"
make up
```

**Wait for this output:**
```
✔ Postgres ready
✔ Redis ready
✔ API listening on http://localhost:8000
✔ UI available at http://localhost:3000
✔ Seeded sample repos: python-sample
System ready.
```

### 2. Open the UI

Open your browser to: **http://localhost:3000**

You should see:
- Pipeline Health dashboard
- Empty runs table (no runs yet)
- Stats showing 0 runs

### 3. Trigger Your First Run

In a new terminal:

```bash
make demo:testfail
```

**Expected output:**
```json
{
  "run_id": "8f2c1a6e-91d4-4c8a-a2b4-7d23c9cbb812",
  "status": "QUEUED",
  "queued_at": "2025-03-01T10:14:02Z"
}
```

### 4. Watch It Execute

- **Refresh the UI** - you'll see the run appear
- **Click on the Run ID** - see steps execute in real-time
- **Wait ~30 seconds** - run will complete with FAILED status

### 5. Trigger an Incident

Run the same command **2 more times** (3 total failures):

```bash
make demo:testfail
make demo:testfail
```

**After the 3rd failure:**
- Refresh the dashboard
- You'll see "Open Incidents: 1"
- An incident card appears with "INC-0001"
- Click it to see the incident timeline

### 6. Test Flaky Detection

```bash
make demo:flaky
```

This triggers 5 runs of a flaky test. Then:
- Go to **"Flaky Tests"** page in the UI
- See `test_payment_flow` detected with ~50% failure rate

### 7. Trigger a Success

```bash
make demo:success
```

This shows a clean, successful run with all tests passing.

---

## Verify Everything Works

### Check API Health
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

### Check Recent Runs
```bash
make runs
```

### Check Incidents
```bash
make incidents
```

---

## Common Issues

### "Port already in use"
```bash
# Find what's using the port
lsof -i :8000

# Or just change the port in docker-compose.yml
```

### "Container won't start"
```bash
# View logs
make logs

# Try clean start
make clean
make up
```

### "Database connection error"
```bash
# Check database is ready
docker-compose ps

# Restart just postgres
docker-compose restart postgres
```

---

## What to Show a Recruiter

1. **Start the system:** `make up` (shows production setup skills)
2. **Open UI:** Show clean, modern dashboard
3. **Trigger failure:** `make demo:testfail` (3 times)
4. **Show incident:** Click INC-0001, explain clustering logic
5. **Show flaky tests:** Run `make demo:flaky`, explain detection
6. **Explain architecture:** Walk through docker-compose.yml

### Key Talking Points

- "This demonstrates **failure clustering** using SHA-256 fingerprinting"
- "Incidents are **automatically created** after threshold"
- "The system uses **database triggers** for flaky test detection"
- "Architecture is **microservices-based** with async worker processing"
- "Optimized to run on **8GB RAM** using connection pooling"

---

## Cleanup

When done:

```bash
# Stop but keep data
make down

# Stop and delete everything
make clean
```

---

## Next Steps

- Read `README.md` for full documentation
- Explore the codebase (clean, commented code)
- Try modifying `sample-repos/python-sample` tests
- Add your own job templates in `worker/executor.py`

---

**You're ready to go! Start with `make up` and explore.** 🎉

