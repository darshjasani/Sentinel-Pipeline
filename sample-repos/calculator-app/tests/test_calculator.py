"""
Tests for Calculator - Real working tests
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator import Calculator, fibonacci, is_prime


class TestCalculator:
    """Test the Calculator class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.calc = Calculator()
    
    def test_add(self):
        """Test addition"""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0, 0) == 0
    
    def test_subtract(self):
        """Test subtraction"""
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(0, 5) == -5
        assert self.calc.subtract(10, 10) == 0
    
    def test_multiply(self):
        """Test multiplication"""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(0, 100) == 0
        assert self.calc.multiply(-2, 3) == -6
    
    def test_divide(self):
        """Test division"""
        assert self.calc.divide(10, 2) == 5
        assert self.calc.divide(9, 3) == 3
        assert self.calc.divide(7, 2) == 3.5
    
    def test_divide_by_zero(self):
        """Test that division by zero raises error"""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calc.divide(10, 0)
    
    def test_power(self):
        """Test exponentiation"""
        assert self.calc.power(2, 3) == 8
        assert self.calc.power(5, 0) == 1
        assert self.calc.power(10, 2) == 100


class TestFibonacci:
    """Test Fibonacci function"""
    
    def test_fibonacci_basic(self):
        """Test basic Fibonacci sequences"""
        assert fibonacci(0) == []
        assert fibonacci(1) == [0]
        assert fibonacci(2) == [0, 1]
        assert fibonacci(5) == [0, 1, 1, 2, 3]
    
    def test_fibonacci_longer(self):
        """Test longer Fibonacci sequence"""
        result = fibonacci(10)
        assert len(result) == 10
        assert result == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


class TestPrimeNumbers:
    """Test prime number checker"""
    
    def test_is_prime_true(self):
        """Test that prime numbers are identified correctly"""
        assert is_prime(2) == True
        assert is_prime(3) == True
        assert is_prime(5) == True
        assert is_prime(7) == True
        assert is_prime(11) == True
        assert is_prime(13) == True
    
    def test_is_prime_false(self):
        """Test that non-prime numbers are identified correctly"""
        assert is_prime(0) == False
        assert is_prime(1) == False
        assert is_prime(4) == False
        assert is_prime(6) == False
        assert is_prime(8) == False
        assert is_prime(9) == False
        assert is_prime(10) == False

