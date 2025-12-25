"""
Failure clustering and classification logic
Deterministic approach using fingerprinting and pattern matching
"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


def extract_failure_fingerprint(error_message: str, stack_trace: str) -> str:
    """
    Generate a fingerprint for a failure based on normalized error patterns.
    Similar failures should produce the same fingerprint.
    """
    # Normalize the error message and stack trace
    normalized = normalize_failure_text(error_message, stack_trace)
    
    # Generate SHA-256 hash of normalized text
    fingerprint = hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    return fingerprint


def normalize_failure_text(error_message: str, stack_trace: str) -> str:
    """
    Normalize failure text by removing variable parts (line numbers, IDs, timestamps, etc.)
    This ensures similar failures produce the same fingerprint.
    """
    combined = f"{error_message}\n{stack_trace}"
    
    # Remove line numbers (e.g., ":42", "line 123")
    combined = re.sub(r':\d+', ':N', combined)
    combined = re.sub(r'line \d+', 'line N', combined)
    
    # Remove memory addresses (0x...)
    combined = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', combined)
    
    # Remove UUIDs
    combined = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID', combined)
    
    # Remove timestamps
    combined = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', 'TIMESTAMP', combined)
    
    # Remove specific numeric values
    combined = re.sub(r'\d+\.\d+', 'NUM', combined)
    combined = re.sub(r'\b\d{3,}\b', 'NUM', combined)
    
    # Normalize whitespace
    combined = ' '.join(combined.split())
    
    return combined.lower()


def classify_failure(error_message: str, stack_trace: str, exit_code: Optional[int]) -> str:
    """
    Classify failure into categories based on patterns.
    Returns: TEST_FAILURE, BUILD_FAILURE, TIMEOUT, DEPENDENCY_ERROR, or UNKNOWN
    """
    combined = f"{error_message} {stack_trace}".lower()
    
    # Test failure patterns
    test_patterns = [
        r'assert',
        r'test.*failed',
        r'assertion.*error',
        r'expected.*but.*was',
        r'should.*equal',
        r'\d+ failed.*\d+ passed'
    ]
    
    # Build failure patterns
    build_patterns = [
        r'compilation.*error',
        r'syntax.*error',
        r'import.*error',
        r'module.*not.*found',
        r'cannot.*find.*module',
        r'build.*failed'
    ]
    
    # Timeout patterns
    timeout_patterns = [
        r'timeout',
        r'timed.*out',
        r'deadline.*exceeded'
    ]
    
    # Dependency patterns
    dependency_patterns = [
        r'dependency.*error',
        r'package.*not.*found',
        r'version.*conflict',
        r'requirement.*not.*satisfied'
    ]
    
    if any(re.search(pattern, combined) for pattern in test_patterns):
        return "TEST_FAILURE"
    elif any(re.search(pattern, combined) for pattern in build_patterns):
        return "BUILD_FAILURE"
    elif any(re.search(pattern, combined) for pattern in timeout_patterns):
        return "TIMEOUT"
    elif any(re.search(pattern, combined) for pattern in dependency_patterns):
        return "DEPENDENCY_ERROR"
    elif exit_code and exit_code == 124:  # Common timeout exit code
        return "TIMEOUT"
    else:
        return "UNKNOWN"


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts (0.0 to 1.0)"""
    return SequenceMatcher(None, text1, text2).ratio()


def find_similar_cluster(fingerprint: str, message: str, existing_fingerprints: List[Tuple[str, str]]) -> Optional[Tuple[str, float]]:
    """
    Find a similar existing cluster using fingerprint matching and text similarity.
    Returns: (cluster_id, confidence) or None
    """
    # First, exact fingerprint match
    for fp, cluster_id in existing_fingerprints:
        if fp == fingerprint:
            return (cluster_id, 1.0)
    
    # If no exact match, check for high similarity
    normalized_message = normalize_failure_text(message, "")
    best_match = None
    best_similarity = 0.0
    
    for fp, cluster_id in existing_fingerprints:
        # For similar fingerprints, calculate confidence
        fp_similarity = calculate_similarity(fingerprint, fp)
        if fp_similarity > 0.8:  # High fingerprint similarity threshold
            if fp_similarity > best_similarity:
                best_similarity = fp_similarity
                best_match = cluster_id
    
    if best_match and best_similarity >= 0.85:
        return (best_match, round(best_similarity, 2))
    
    return None


def generate_cluster_title(error_message: str, category: str) -> str:
    """Generate a human-readable title for a failure cluster"""
    # Extract the most relevant part of the error message
    message = error_message.strip()
    
    # Remove common prefixes
    message = re.sub(r'^(Error:|Exception:|Failed:)\s*', '', message, flags=re.IGNORECASE)
    
    # Truncate long messages
    if len(message) > 100:
        message = message[:97] + "..."
    
    return message


def generate_recommendations(category: str, error_message: str, stack_trace: str) -> List[str]:
    """
    Generate context-aware recommendations for fixing the failure.
    Based on failure category and patterns in the error.
    """
    combined = f"{error_message} {stack_trace}".lower()
    recommendations = []
    
    if category == "TEST_FAILURE":
        recommendations.append("Review recent changes that may have affected the failing test")
        
        if "authentication" in combined or "auth" in combined or "login" in combined:
            recommendations.append("Check recent changes to authentication middleware")
            recommendations.append("Verify database connectivity in test environment")
            recommendations.append("Add assertion logging around response payload")
        elif "500" in combined or "internal server error" in combined:
            recommendations.append("Check server logs for detailed error information")
            recommendations.append("Verify all required services are running")
            recommendations.append("Review recent API endpoint changes")
        elif "404" in combined or "not found" in combined:
            recommendations.append("Verify endpoint routes are correctly configured")
            recommendations.append("Check for recent routing changes")
        elif "database" in combined or "sql" in combined:
            recommendations.append("Verify database schema is up to date")
            recommendations.append("Check database migration status")
            recommendations.append("Review test data fixtures")
        else:
            recommendations.append("Add more detailed logging to the failing test")
            recommendations.append("Verify test environment configuration")
    
    elif category == "BUILD_FAILURE":
        recommendations.append("Check for syntax errors in recent commits")
        recommendations.append("Verify all dependencies are properly installed")
        
        if "import" in combined or "module" in combined:
            recommendations.append("Update requirements.txt or package.json")
            recommendations.append("Clear dependency cache and reinstall")
    
    elif category == "TIMEOUT":
        recommendations.append("Check for infinite loops or blocking operations")
        recommendations.append("Increase timeout threshold if operations are legitimately slow")
        recommendations.append("Profile code to identify performance bottlenecks")
    
    elif category == "DEPENDENCY_ERROR":
        recommendations.append("Update dependency versions in manifest")
        recommendations.append("Check for conflicting package versions")
        recommendations.append("Clear package cache and reinstall dependencies")
    
    else:
        recommendations.append("Review recent code changes")
        recommendations.append("Check system logs for more context")
        recommendations.append("Run the test locally to reproduce")
    
    return recommendations[:5]  # Limit to top 5 recommendations


def generate_incident_summary(cluster_title: str, occurrence_count: int, repo_id: str) -> str:
    """Generate incident impact summary"""
    return f"Repeated CI failures blocking {repo_id} pipeline"


def generate_suspected_root_cause(cluster_title: str, category: str) -> str:
    """Generate suspected root cause based on failure pattern"""
    if category == "TEST_FAILURE":
        return f"{cluster_title}"
    elif category == "BUILD_FAILURE":
        return f"Build configuration or code syntax issue: {cluster_title}"
    elif category == "TIMEOUT":
        return f"Performance degradation or infinite loop: {cluster_title}"
    elif category == "DEPENDENCY_ERROR":
        return f"Dependency configuration issue: {cluster_title}"
    else:
        return f"Unknown issue: {cluster_title}"

