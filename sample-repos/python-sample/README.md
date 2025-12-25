# Python Sample Project

This is a sample Python project used for CI pipeline testing.

## Test Scenarios

### Deterministic Success
- `test_user_login_success` - Always passes
- `test_invalid_credentials` - Always passes
- `test_user_not_found` - Always passes

### Deterministic Failure
- `test_user_login_fail` - Always fails (API returns 500 instead of 200)

### Flaky Tests
- `test_payment_flow` - Randomly passes/fails (~50% failure rate)

## Running Tests

```bash
pytest -v
```

## Test for Specific Scenario

```bash
# Success scenario
pytest tests/test_auth.py::test_user_login_success -v

# Failure scenario
pytest tests/test_auth.py::test_user_login_fail -v

# Flaky scenario
pytest tests/test_payment.py::test_payment_flow -v
```

