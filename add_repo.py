#!/usr/bin/env python3
"""
Helper script to add a new repository to Sentinel Pipeline
Usage: python3 add_repo.py <repo-id> <repo-name> <local-path>
"""

import sys
import requests
import json

API_URL = "http://localhost:8000"

def add_repository(repo_id: str, repo_name: str, local_path: str):
    """Add a new repository via API"""
    
    # Check if API is running
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ API is not healthy. Make sure 'make up' is running.")
            return False
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API. Make sure 'make up' is running.")
        return False
    
    # Add repository
    data = {
        "id": repo_id,
        "name": repo_name,
        "path": f"/app/sample-repos/{local_path}"  # Docker internal path
    }
    
    try:
        response = requests.post(f"{API_URL}/repos", json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Repository '{repo_name}' added successfully!")
            print(f"   ID: {repo_id}")
            print(f"   Path: /app/sample-repos/{local_path}")
            print(f"\n📋 To run tests, use:")
            print(f"   curl -X POST {API_URL}/runs \\")
            print(f"     -H 'Content-Type: application/json' \\")
            print(f"     -d '{{\"repo_id\":\"{repo_id}\",\"job_template\":\"pytest\",\"timeout_sec\":300,\"triggered_by\":\"manual\"}}'")
            return True
        else:
            print(f"❌ Failed to add repository: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def list_repositories():
    """List all registered repositories"""
    try:
        response = requests.get(f"{API_URL}/repos", timeout=10)
        if response.status_code == 200:
            repos = response.json()
            print("\n📦 Registered Repositories:")
            print("-" * 60)
            for repo in repos:
                print(f"  • {repo['id']}: {repo['name']}")
                print(f"    Path: {repo['path']}")
                print()
        else:
            print(f"❌ Failed to list repositories: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "list":
        list_repositories()
    elif len(sys.argv) == 4:
        repo_id = sys.argv[1]
        repo_name = sys.argv[2]
        local_path = sys.argv[3]
        add_repository(repo_id, repo_name, local_path)
    else:
        print("Usage:")
        print("  python3 add_repo.py <repo-id> <repo-name> <folder-name>")
        print("  python3 add_repo.py list")
        print()
        print("Example:")
        print("  python3 add_repo.py my-app 'My Application' my-app")
        print()
        print("Note: Make sure your project folder is in sample-repos/")
        sys.exit(1)

