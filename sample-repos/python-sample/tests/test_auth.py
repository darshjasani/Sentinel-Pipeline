"""
Authentication tests
Contains deterministic success and failure scenarios
"""

import pytest
from app.auth import authenticate_user, authenticate_user_broken


def test_user_login_success():
    """
    Test successful login - ALWAYS PASSES
    Used for demo:success scenario
    """
    response = authenticate_user("admin", "admin123")
    assert response.status_code == 200
    assert "token" in response.body
    assert response.body["user"] == "admin"


def test_user_login_fail():
    """
    Test login failure - ALWAYS FAILS
    Used for demo:testfail scenario
    This demonstrates a deterministic test failure (API returns 500 instead of 200)
    """
    response = authenticate_user_broken("admin", "admin123")
    
    # This assertion will ALWAYS fail because authenticate_user_broken returns 500
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    assert "token" in response.body


def test_invalid_credentials():
    """
    Test invalid credentials - ALWAYS PASSES
    """
    response = authenticate_user("admin", "wrongpassword")
    assert response.status_code == 401


def test_user_not_found():
    """
    Test user not found - ALWAYS PASSES
    """
    response = authenticate_user("nonexistent", "password")
    assert response.status_code == 404

