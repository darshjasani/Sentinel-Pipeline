"""
CI Job Executor
Handles actual execution of CI jobs with different templates
"""

import subprocess
import os
import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from config import settings


class JobExecutor:
    """Execute CI jobs based on templates"""
    
    def __init__(self, run_id: str, repo_path: str, log_dir: str):
        self.run_id = run_id
        self.repo_path = repo_path
        self.log_dir = log_dir
        self.steps = []
        
    def execute_template(self, template: str) -> Tuple[str, int, List[Dict]]:
        """
        Execute a job template and return (status, exit_code, steps)
        """
        if template == "pytest-fail":
            return self._execute_pytest_deterministic_fail()
        elif template == "pytest-success":
            return self._execute_pytest_success()
        elif template == "pytest-flaky":
            return self._execute_pytest_flaky()
        elif template == "pytest":
            return self._execute_pytest_default()
        else:
            return self._execute_pytest_default()
    
    def _execute_pytest_deterministic_fail(self) -> Tuple[str, int, List[Dict]]:
        """Execute pytest with deterministic failure scenario"""
        steps = []
        
        # Step 1: Install dependencies
        step1 = self._run_step(
            "Install dependencies",
            ["pip", "install", "-q", "pytest"],
            timeout=60
        )
        steps.append(step1)
        
        if step1["status"] != "SUCCEEDED":
            return "FAILED", step1["exit_code"], steps
        
        # Step 2: Run tests with deterministic failure
        step2 = self._run_step(
            "Run tests",
            ["pytest", "-v", "tests/test_auth.py::test_user_login_fail", "--tb=short"],
            cwd=self.repo_path,
            timeout=120
        )
        steps.append(step2)
        
        # This should fail deterministically
        if step2["exit_code"] != 0:
            return "FAILED", step2["exit_code"], steps
        
        return "SUCCEEDED", 0, steps
    
    def _execute_pytest_success(self) -> Tuple[str, int, List[Dict]]:
        """Execute pytest with successful scenario"""
        steps = []
        
        # Step 1: Install dependencies
        step1 = self._run_step(
            "Install dependencies",
            ["pip", "install", "-q", "pytest"],
            timeout=60
        )
        steps.append(step1)
        
        if step1["status"] != "SUCCEEDED":
            return "FAILED", step1["exit_code"], steps
        
        # Step 2: Run successful tests
        step2 = self._run_step(
            "Run tests",
            ["pytest", "-v", "tests/test_auth.py::test_user_login_success", "--tb=short"],
            cwd=self.repo_path,
            timeout=120
        )
        steps.append(step2)
        
        if step2["exit_code"] != 0:
            return "FAILED", step2["exit_code"], steps
        
        return "SUCCEEDED", 0, steps
    
    def _execute_pytest_flaky(self) -> Tuple[str, int, List[Dict]]:
        """Execute pytest with flaky test (50% failure rate)"""
        steps = []
        
        # Step 1: Install dependencies
        step1 = self._run_step(
            "Install dependencies",
            ["pip", "install", "-q", "pytest"],
            timeout=60
        )
        steps.append(step1)
        
        if step1["status"] != "SUCCEEDED":
            return "FAILED", step1["exit_code"], steps
        
        # Step 2: Run flaky tests
        step2 = self._run_step(
            "Run tests",
            ["pytest", "-v", "tests/test_payment.py::test_payment_flow", "--tb=short"],
            cwd=self.repo_path,
            timeout=120
        )
        steps.append(step2)
        
        if step2["exit_code"] != 0:
            return "FAILED", step2["exit_code"], steps
        
        return "SUCCEEDED", 0, steps
    
    def _execute_pytest_default(self) -> Tuple[str, int, List[Dict]]:
        """Execute all pytest tests"""
        steps = []
        
        # Step 1: Install dependencies
        step1 = self._run_step(
            "Install dependencies",
            ["pip", "install", "-q", "pytest"],
            timeout=60
        )
        steps.append(step1)
        
        if step1["status"] != "SUCCEEDED":
            return "FAILED", step1["exit_code"], steps
        
        # Step 2: Run all tests
        step2 = self._run_step(
            "Run tests",
            ["pytest", "-v", "--tb=short"],
            cwd=self.repo_path,
            timeout=120
        )
        steps.append(step2)
        
        if step2["exit_code"] != 0:
            return "FAILED", step2["exit_code"], steps
        
        return "SUCCEEDED", 0, steps
    
    def _run_step(
        self,
        step_name: str,
        command: List[str],
        cwd: Optional[str] = None,
        timeout: int = 300
    ) -> Dict:
        """
        Run a single step and return result dictionary
        """
        log_file = os.path.join(self.log_dir, f"{step_name.lower().replace(' ', '_')}.log")
        start_time = time.time()
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = int(time.time() - start_time)
            
            # Write log
            with open(log_file, 'w') as f:
                f.write(f"Command: {' '.join(command)}\n")
                f.write(f"Working directory: {cwd or 'default'}\n")
                f.write(f"Exit code: {result.returncode}\n")
                f.write(f"Duration: {duration}s\n\n")
                f.write("=== STDOUT ===\n")
                f.write(result.stdout)
                f.write("\n=== STDERR ===\n")
                f.write(result.stderr)
            
            status = "SUCCEEDED" if result.returncode == 0 else "FAILED"
            
            return {
                "step_name": step_name,
                "status": status,
                "exit_code": result.returncode,
                "duration_sec": duration,
                "log_path": log_file,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            duration = int(time.time() - start_time)
            with open(log_file, 'w') as f:
                f.write(f"Command: {' '.join(command)}\n")
                f.write(f"Status: TIMEOUT after {timeout}s\n")
            
            return {
                "step_name": step_name,
                "status": "FAILED",
                "exit_code": 124,  # Standard timeout exit code
                "duration_sec": duration,
                "log_path": log_file,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds"
            }
        
        except Exception as e:
            duration = int(time.time() - start_time)
            with open(log_file, 'w') as f:
                f.write(f"Command: {' '.join(command)}\n")
                f.write(f"Error: {str(e)}\n")
            
            return {
                "step_name": step_name,
                "status": "FAILED",
                "exit_code": 1,
                "duration_sec": duration,
                "log_path": log_file,
                "stdout": "",
                "stderr": str(e)
            }
    
    def parse_test_results(self, output: str) -> List[Dict]:
        """
        Parse pytest output to extract individual test results
        """
        test_results = []
        
        # Parse pytest output format
        # Looking for patterns like: tests/test_auth.py::test_user_login PASSED
        test_pattern = re.compile(r'([\w/\.]+)::([\w]+)\s+(PASSED|FAILED|SKIPPED)')
        
        for match in test_pattern.finditer(output):
            file_path, test_name, status = match.groups()
            test_results.append({
                "test_name": f"{file_path}::{test_name}",
                "status": status
            })
        
        # Also look for failure details
        failure_pattern = re.compile(r'_+ (.*) _+\n(.*?)(?=_+|$)', re.DOTALL)
        failures = {}
        
        for match in failure_pattern.finditer(output):
            test_name, details = match.groups()
            failures[test_name.strip()] = details.strip()
        
        # Merge failure details
        for result in test_results:
            if result["status"] == "FAILED":
                test_simple_name = result["test_name"].split("::")[-1]
                if test_simple_name in failures:
                    result["error_message"] = failures[test_simple_name][:500]  # Limit length
        
        return test_results

