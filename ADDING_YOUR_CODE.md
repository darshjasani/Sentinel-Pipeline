# Adding Your Own Code to Sentinel Pipeline

This guide shows you how to run the Sentinel Pipeline on **your real code**, not just demo examples.

---

## 🚀 Quick Start: Test the Calculator Example

We've created a **real working example** for you:

```bash
# 1. Make sure the system is running
make up

# 2. Register the calculator repository
make add-calculator

# 3. Run tests on it
make test-calculator

# 4. View results in the UI
open http://localhost:3000
```

The calculator app is located at: `sample-repos/calculator-app/`

---

## 📦 Adding Your Own Python Project

### Method 1: Quick Manual Add (Recommended)

**Step 1:** Copy your project to `sample-repos`

```bash
# Example: Copy your existing project
cp -r ~/path/to/your/project sample-repos/my-app
```

**Step 2:** Make sure your project has:
- A `tests/` directory with pytest tests
- A `requirements.txt` (optional but recommended)

**Step 3:** Register it with the system

```bash
# Use the helper script
python3 add_repo.py my-app "My Application" my-app

# Or manually via API:
curl -X POST http://localhost:8000/repos \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-app",
    "name": "My Application", 
    "path": "/app/sample-repos/my-app"
  }'
```

**Step 4:** Run tests on it

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "my-app",
    "job_template": "pytest",
    "timeout_sec": 300,
    "triggered_by": "manual"
  }'
```

**Step 5:** View results in the UI at http://localhost:3000

---

### Method 2: Create a Custom Makefile Target

Add this to your `Makefile`:

```makefile
# Add your custom repo
add-myapp:
	@curl -s -X POST http://localhost:8000/repos \
		-H "Content-Type: application/json" \
		-d '{"id":"myapp","name":"My App","path":"/app/sample-repos/myapp"}' \
		| python3 -m json.tool

# Run tests on your repo
test-myapp:
	@curl -s -X POST http://localhost:8000/runs \
		-H "Content-Type: application/json" \
		-d '{"repo_id":"myapp","job_template":"pytest","timeout_sec":300,"triggered_by":"manual"}' \
		| python3 -m json.tool
```

Then use:
```bash
make add-myapp
make test-myapp
```

---

## 📋 Project Requirements

For your project to work with Sentinel Pipeline:

### ✅ Python Projects (Pytest)

Your project should have:

```
your-project/
├── your_code/
│   ├── __init__.py
│   └── module.py
├── tests/
│   ├── __init__.py
│   └── test_module.py
├── requirements.txt (optional)
└── README.md (optional)
```

**Minimum requirements:**
- Tests in a `tests/` directory
- Tests discoverable by pytest (files named `test_*.py` or `*_test.py`)

---

## 🎯 Real World Example: Testing Your API

Let's say you have a FastAPI application:

```bash
# 1. Copy your project
cp -r ~/my-fastapi-app sample-repos/my-api

# 2. Ensure it has tests
ls sample-repos/my-api/tests/
# Should show: test_api.py, test_auth.py, etc.

# 3. Register it
python3 add_repo.py my-api "My API Application" my-api

# 4. Run tests
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "repo_id": "my-api",
    "job_template": "pytest",
    "timeout_sec": 600,
    "triggered_by": "manual"
  }'

# 5. Check results
make runs
```

---

## 🔍 Viewing Results

### Via UI Dashboard
- Open http://localhost:3000
- Navigate to **Runs** page
- Click on your run to see:
  - Test results
  - Logs
  - Failure analysis
  - Recommendations

### Via API
```bash
# List all runs
make runs

# List all repositories
make repos

# Check incidents
make incidents
```

### Via Logs
```bash
# Watch live logs
make logs

# View specific service
make logs-worker
```

---

## 🧪 Understanding Job Templates

Currently available templates:

| Template | Purpose | When to Use |
|----------|---------|-------------|
| `pytest` | Run all tests | Your default choice |
| `pytest-success` | Demo: always passes | Testing the system |
| `pytest-fail` | Demo: always fails | Testing failure detection |
| `pytest-flaky` | Demo: intermittent failures | Testing flaky detection |

For your own code, use: `"job_template": "pytest"`

---

## 🐛 Troubleshooting

### Tests not found?

Make sure your test files follow pytest conventions:
```python
# ✅ Good: tests/test_module.py
def test_something():
    assert True

# ❌ Bad: tests/module_tests.py (wrong naming)
def check_something():  # ❌ (not prefixed with test_)
    assert True
```

### Import errors?

Add an `__init__.py` to your package directories and use relative imports:

```python
# In tests/test_module.py
import sys
sys.path.insert(0, '..')
from your_package import your_module
```

### Dependency issues?

Add a `requirements.txt`:
```txt
pytest>=7.0.0
requests>=2.28.0
# your other dependencies
```

The system will install these automatically.

---

## 📊 What Happens After Running Tests?

1. **Success:** Green status, results appear in UI
2. **Failure:** System analyzes the failure and:
   - Creates a failure cluster
   - Identifies the root cause
   - Suggests fixes
   - If repeated, creates an **Incident**
3. **Flaky Tests:** If same test fails intermittently, marked as flaky

---

## 🎓 Next Steps

1. ✅ Test with the calculator example
2. ✅ Add your own simple project
3. ✅ Run tests and explore the UI
4. ✅ Trigger multiple runs to see incident creation
5. ✅ Check out failure clustering and flaky test detection

---

## 💡 Pro Tips

- **Start small:** Test with a project that has 5-10 tests first
- **Check logs:** If something goes wrong, `make logs-worker` is your friend
- **Use the UI:** It's much easier than curl commands
- **Experiment:** Try triggering the same failure multiple times to see incident creation

---

## 🆘 Getting Help

If you encounter issues:

```bash
# Check system health
make health

# View worker logs
make logs-worker

# Check API logs
make logs-api

# List registered repos
python3 add_repo.py list
```

Still stuck? Check:
- Is Docker running?
- Is `make up` successful?
- Do your tests run locally with `pytest`?

---

**Ready to test your code? Start with `make add-calculator` and `make test-calculator`!** 🚀

