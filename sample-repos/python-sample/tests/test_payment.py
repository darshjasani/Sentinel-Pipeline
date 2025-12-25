"""
Payment tests
Contains flaky test scenario
"""

import pytest
from app.auth import calculate_payment


def test_payment_flow():
    """
    Flaky test - passes/fails randomly ~50% of the time
    Used for flaky test detection
    """
    # This test is flaky because calculate_payment has random behavior
    amount = -10  # Negative amount
    
    try:
        result = calculate_payment(amount)
        # Sometimes it doesn't validate, test passes
        assert result == 0
    except ValueError as e:
        # Sometimes it validates, raises ValueError, test fails
        pytest.fail(f"Payment validation failed: {e}")


def test_payment_with_discount():
    """
    Stable test - ALWAYS PASSES
    """
    result = calculate_payment(100, discount=10)
    assert result == 90.0


def test_payment_zero_amount():
    """
    Stable test - ALWAYS PASSES
    """
    result = calculate_payment(0)
    assert result == 0

