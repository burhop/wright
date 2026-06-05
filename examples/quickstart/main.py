import httpx
import sys

def main():
    base_url = "http://127.0.0.1:8000"
    print(f"Connecting to Wright API at {base_url}...")
    try:
        # Check API Health
        response = httpx.get(f"{base_url}/api/health")
        response.raise_for_status()
        health_data = response.json()
        print(f"API Health: State={health_data.get('state')}, Latency={health_data.get('latencyMs')}ms")
        
        # Get active agent
        agent_response = httpx.get(f"{base_url}/api/agent/active")
        agent_response.raise_for_status()
        agent_data = agent_response.json()
        print(f"Active Agent: {agent_data.get('agent')}")
        print("Success: Quickstart check completed successfully!")
    except Exception as e:
        print(f"Error: Failed to connect to Wright API: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
