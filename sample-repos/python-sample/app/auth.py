"""
Authentication module for sample project
Contains mock authentication logic for testing
"""

class AuthResponse:
    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self.body = body or {}


def authenticate_user(username, password):
    """
    Mock authentication function
    Returns AuthResponse with appropriate status code
    """
    # Simulate database lookup
    valid_users = {
        "admin": "admin123",
        "user": "user123"
    }
    
    if username not in valid_users:
        return AuthResponse(404, {"error": "User not found"})
    
    if valid_users[username] != password:
        return AuthResponse(401, {"error": "Invalid password"})
    
    return AuthResponse(200, {"token": f"token_{username}", "user": username})


def authenticate_user_broken(username, password):
    """
    Broken authentication function - always returns 500
    Used for deterministic failure testing
    """
    # Simulate server error
    return AuthResponse(500, {"error": "Internal server error"})


def calculate_payment(amount, discount=0):
    """
    Mock payment calculation
    Used for flaky test scenario
    """
    import random
    
    # Introduce randomness for flaky behavior
    if random.random() < 0.5:
        # Sometimes fail validation
        if amount < 0:
            raise ValueError("Amount cannot be negative")
    
    final_amount = amount * (1 - discount / 100)
    return max(0, final_amount)

