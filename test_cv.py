#!/usr/bin/env python
import json
import os

import requests


API_BASE = os.getenv("INTERLEV_API_BASE", "http://127.0.0.1:8000")


try:
    with open("sample_cv.txt", "rb") as file_handle:
        files = {"file": file_handle}
        response = requests.post(f"{API_BASE}/api/cv/upload", files=files, timeout=30)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("SUCCESS: CV uploaded successfully")
        print(f"Full Response:\n{json.dumps(result, indent=2)}")
    else:
        print(f"FAILED: {response.status_code}")
        print(f"Response: {response.text[:500]}")

except Exception as exc:
    print(f"Error: {type(exc).__name__}: {exc}")
