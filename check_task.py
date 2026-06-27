#!/usr/bin/env python
import json
import os
import sys

import requests


API_BASE = os.getenv("INTERLEV_API_BASE", "http://127.0.0.1:8000")
task_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv(
    "INTERLEV_TASK_ID",
    "9adba3ab-f933-409b-b469-cf42e391d749",
)


try:
    response = requests.get(f"{API_BASE}/api/cv/status/{task_id}", timeout=10)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nTask Status:\n{json.dumps(result, indent=2)}")
    else:
        print(f"Response: {response.text[:500]}")

except Exception as exc:
    print(f"Error: {type(exc).__name__}: {exc}")
