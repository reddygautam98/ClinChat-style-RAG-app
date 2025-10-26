#!/usr/bin/env python3
"""
GitHub Actions Pipeline Monitor for ClinChat HealthAI RAG
Monitors pipeline runs and provides real-time status updates
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Optional

class GitHubActionMonitor:
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
    
    def get_workflow_runs(self, per_page: int = 5) -> List[Dict]:
        """Get recent workflow runs"""
        url = f"{self.base_url}/actions/runs?per_page={per_page}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["workflow_runs"]
        except requests.RequestException as e:
            print(f"❌ Error fetching workflow runs: {e}")
            return []
    
    def get_run_details(self, run_id: int) -> Optional[Dict]:
        """Get detailed information about a specific run"""
        url = f"{self.base_url}/actions/runs/{run_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Error fetching run {run_id}: {e}")
            return None
    
    def get_run_jobs(self, run_id: int) -> List[Dict]:
        """Get jobs for a specific run"""
        url = f"{self.base_url}/actions/runs/{run_id}/jobs"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["jobs"]
        except requests.RequestException as e:
            print(f"❌ Error fetching jobs for run {run_id}: {e}")
            return []
    
    def format_status(self, status: str, conclusion: Optional[str] = None) -> str:
        """Format status with appropriate emoji"""
        if status == "in_progress":
            return "🔄 IN PROGRESS"
        elif status == "queued":
            return "⏳ QUEUED"
        elif status == "completed":
            if conclusion == "success":
                return "✅ SUCCESS"
            elif conclusion == "failure":
                return "❌ FAILURE"
            elif conclusion == "cancelled":
                return "🚫 CANCELLED"
            else:
                return f"⚪ COMPLETED ({conclusion})"
        else:
            return f"❓ {status.upper()}"
    
    def monitor_run(self, run_id: int, check_interval: int = 30):
        """Monitor a specific run until completion"""
        print(f"🔍 Monitoring GitHub Actions Run: {run_id}")
        print("=" * 60)
        
        start_time = datetime.now()
        
        while True:
            run_details = self.get_run_details(run_id)
            
            if not run_details:
                print("❌ Could not fetch run details")
                break
            
            status = run_details["status"]
            conclusion = run_details.get("conclusion")
            
            # Calculate elapsed time
            elapsed = datetime.now() - start_time
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            
            print(f"\n📊 Status Update [{elapsed_str}]")
            print(f"   Status: {self.format_status(status, conclusion)}")
            print(f"   Started: {run_details['created_at']}")
            print(f"   Updated: {run_details['updated_at']}")
            
            if status == "completed":
                print(f"\n🎯 Pipeline Completed!")
                print(f"   Final Result: {self.format_status(status, conclusion)}")
                
                # Get job details for completed run
                jobs = self.get_run_jobs(run_id)
                if jobs:
                    print(f"\n📋 Job Details:")
                    for job in jobs:
                        job_status = self.format_status(job["status"], job.get("conclusion"))
                        print(f"   • {job['name']}: {job_status}")
                
                return conclusion == "success"
            
            print(f"   ⏱️  Next check in {check_interval} seconds...")
            time.sleep(check_interval)
    
    def get_latest_runs_summary(self):
        """Get summary of recent runs"""
        runs = self.get_workflow_runs(5)
        
        print("📈 Recent GitHub Actions Runs")
        print("=" * 60)
        
        for i, run in enumerate(runs, 1):
            status_str = self.format_status(run["status"], run.get("conclusion"))
            created = run["created_at"][:19].replace('T', ' ')
            commit_msg = run["head_commit"]["message"][:50] + "..." if len(run["head_commit"]["message"]) > 50 else run["head_commit"]["message"]
            
            print(f"{i}. Run {run['id']}")
            print(f"   Status: {status_str}")
            print(f"   Created: {created}")
            print(f"   Commit: {commit_msg}")
            print()

def main():
    # ClinChat HealthAI RAG repository details
    monitor = GitHubActionMonitor("reddygautam98", "ClinChat-style-RAG-app")
    
    print("🚀 ClinChat HealthAI RAG - GitHub Actions Monitor")
    print("=" * 60)
    
    # Get latest runs summary
    monitor.get_latest_runs_summary()
    
    # Ask which run to monitor
    print("🔍 Enter the run ID you want to monitor (or press Enter for latest):")
    user_input = input().strip()
    
    if user_input:
        try:
            run_id = int(user_input)
        except ValueError:
            print("❌ Invalid run ID. Using latest run.")
            runs = monitor.get_workflow_runs(1)
            run_id = runs[0]["id"] if runs else None
    else:
        runs = monitor.get_workflow_runs(1)
        run_id = runs[0]["id"] if runs else None
    
    if run_id:
        success = monitor.monitor_run(run_id)
        
        if success:
            print("\n🎉 DEPLOYMENT VALIDATION: ✅ SUCCESS")
            print("✅ All tests passed - Production ready!")
        else:
            print("\n⚠️ DEPLOYMENT VALIDATION: ❌ FAILED")
            print("❌ Pipeline failed - Check logs before deployment")
    else:
        print("❌ No runs found to monitor")

if __name__ == "__main__":
    main()