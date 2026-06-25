"""Ping the API /health endpoint; exit non-zero on failure.

Intended for Docker/Kubernetes liveness probes.

Usage:
    python -m scripts.healthcheck            # checks http://localhost:8000
    HEALTH_URL=http://api:8000 python -m scripts.healthcheck
"""

import os
import sys

import httpx

URL = os.getenv("HEALTH_URL", "http://localhost:8000") + "/health"


def main() -> int:
    try:
        resp = httpx.get(URL, timeout=5.0)
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            print(f"OK: {URL}")
            return 0
        print(f"UNHEALTHY: {URL} -> {resp.status_code} {resp.text}")
        return 1
    except Exception as e:
        print(f"UNREACHABLE: {URL} -> {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
