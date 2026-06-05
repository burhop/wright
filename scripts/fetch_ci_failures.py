#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional

def run_command(cmd: List[str], env: Optional[Dict[str, str]] = None, input_data: Optional[str] = None) -> subprocess.CompletedProcess:
    """Helper to run a shell command and return the completed process."""
    return subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
        env=env,
        check=False
    )

def get_git_remote_url() -> Optional[str]:
    """Retrieve the remote origin URL of the repository."""
    result = run_command(["git", "config", "--get", "remote.origin.url"])
    if result.returncode == 0:
        return result.stdout.strip()
    return None

def get_github_token(remote_url: str) -> Optional[str]:
    """Attempts to retrieve the GitHub token using git credential fill."""
    if not remote_url:
        return None
    
    # Format input for git credential fill
    input_data = f"url={remote_url}\n"
    result = run_command(["git", "credential", "fill"], input_data=input_data)
    
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1]
    return None

def get_current_branch() -> str:
    """Retrieve the active git branch name."""
    result = run_command(["git", "branch", "--show-current"])
    if result.returncode == 0:
        branch = result.stdout.strip()
        if branch:
            return branch
    return "dev"

def check_gh_installed() -> bool:
    """Check if GitHub CLI (gh) is installed and accessible."""
    result = run_command(["gh", "--version"])
    return result.returncode == 0

def fetch_failed_runs(env: Dict[str, str], branch: Optional[str], limit: int) -> List[Dict]:
    """Fetch failed run metadata from GitHub Actions via gh CLI."""
    cmd = ["gh", "run", "list", "--status", "failure", "--limit", str(limit), "--json", "databaseId,name,conclusion,url,createdAt,headBranch,headSha"]
    if branch:
        cmd.extend(["--branch", branch])
        
    result = run_command(cmd, env=env)
    if result.returncode != 0:
        print(f"Error fetching runs: {result.stderr}", file=sys.stderr)
        return []
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Failed to parse JSON response from GitHub CLI.", file=sys.stderr)
        return []

def fetch_failed_log(env: Dict[str, str], run_id: int) -> str:
    """Fetch the failed steps log for a specific workflow run."""
    result = run_command(["gh", "run", "view", str(run_id), "--log-failed"], env=env)
    if result.returncode == 0:
        return result.stdout
    return f"Failed to retrieve log details for run ID {run_id}.\n{result.stderr}"

def format_failed_runs_markdown(runs: List[Dict], env: Dict[str, str]) -> str:
    """Format the list of failed runs and logs into a Markdown report."""
    if not runs:
        return "# CI Failure Report\n\nNo failed CI runs were found matching the criteria.\n"

    md = [
        "# CI Failure Report",
        f"Generated automatically for local triage and AI code patching.\n",
        "---",
        ""
    ]
    
    for i, run in enumerate(runs, 1):
        run_id = run["databaseId"]
        name = run["name"]
        branch = run["headBranch"]
        sha = run["headSha"]
        url = run["url"]
        created = run["createdAt"]
        
        md.append(f"## {i}. {name} (Run #{run_id})")
        md.append(f"- **Branch**: `{branch}`")
        md.append(f"- **Commit SHA**: `{sha}`")
        md.append(f"- **Time**: {created}")
        md.append(f"- **URL**: [View run on GitHub]({url})")
        md.append("")
        md.append("### Failed Log Output")
        md.append("```text")
        
        log_content = fetch_failed_log(env, run_id)
        if not log_content.strip():
            log_content = "No failed log output captured (run may have been cancelled or timed out)."
        md.append(log_content.strip())
        
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")
        
    return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub Actions failure logs locally for AI troubleshooting.")
    parser.add_argument("--branch", type=str, help="Target git branch to fetch failures for. Defaults to current active branch.")
    parser.add_argument("--all", action="store_true", help="Fetch failed runs from all branches instead of restricting to current branch.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of failed runs to fetch. Default is 5.")
    parser.add_argument("--output", type=str, default="ci_failures.md", help="File path to write the markdown report. Default is ci_failures.md.")
    parser.add_argument("--token", type=str, help="Explicit GitHub Personal Access Token.")
    
    args = parser.parse_args()
    
    if not check_gh_installed():
        print("Error: GitHub CLI ('gh') is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)
        
    # Setup environment for sub-commands
    env = os.environ.copy()
    
    token = args.token
    if not token:
        remote_url = get_git_remote_url()
        if remote_url:
            token = get_github_token(remote_url)
            
    if token:
        env["GH_TOKEN"] = token
        env["GITHUB_TOKEN"] = token
    else:
        print("Warning: Could not auto-detect GitHub token from Git credentials. Falling back to default gh CLI session.", file=sys.stderr)

    # Determine branch filtering
    target_branch = None
    if not args.all:
        target_branch = args.branch if args.branch else get_current_branch()
        print(f"Filtering CI failures for branch: '{target_branch}'")
    else:
        print("Fetching CI failures for all branches.")
        
    print(f"Fetching up to {args.limit} failed runs...")
    runs = fetch_failed_runs(env, target_branch, args.limit)
    
    print(f"Found {len(runs)} failed runs. Retrieving logs and compiling report...")
    markdown_report = format_failed_runs_markdown(runs, env)
    
    output_path = os.path.abspath(args.output)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        print(f"\nSuccess! Failure report written to: {output_path}")
        print("You can now open this file in your IDE to review the logs and request fixes from the AI.")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
