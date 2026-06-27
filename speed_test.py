#!/usr/bin/env python
import os
import time
from datetime import datetime

import requests


API_BASE = os.getenv("INTERLEV_API_BASE", "http://127.0.0.1:8000")


print(f"Starting CV test at {datetime.now().strftime('%H:%M:%S')}")
start_time = time.time()

try:
    with open("sample_cv.txt", "rb") as file_handle:
        files = {"file": file_handle}
        response = requests.post(f"{API_BASE}/api/cv/upload", files=files, timeout=30)

    elapsed = time.time() - start_time

    print(f"Status: {response.status_code}")
    print(f"Response time: {elapsed:.2f}s")

    if response.status_code == 200:
        result = response.json()
        print("\nCV uploaded successfully")
        print(f"Task ID: {result.get('task_id')}")
        print(f"File: {result.get('file_path')}")
        print("\nPerformance Metrics:")
        print(f"   - Upload to API: {elapsed:.2f}s")
        print("   - Backend processing: Async (background task)")
    else:
        print(f"Response: {response.text[:300]}")

except Exception as exc:
    print(f"Error: {type(exc).__name__}: {exc}")
