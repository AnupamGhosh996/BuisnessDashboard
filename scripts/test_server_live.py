import os
import sys
import time
import threading
import urllib.request
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from server import run_server

# Start server in thread on port 8009
t = threading.Thread(target=run_server, args=(8009,), daemon=True)
t.start()
time.sleep(1)

# Probe health
try:
    with urllib.request.urlopen("http://localhost:8009/api/health") as res:
        health_data = json.loads(res.read().decode())
        print("Live Server Health Check:", health_data)
        assert health_data["status"] == "healthy"

    with urllib.request.urlopen("http://localhost:8009/api/datasets") as res:
        datasets = json.loads(res.read().decode())
        print(f"Live Datasets Endpoint: Found {len(datasets)} dataset(s), Active ID: {datasets[0]['id']}")
        assert len(datasets) > 0

    with urllib.request.urlopen("http://localhost:8009/api/analysis/1/overview") as res:
        overview = json.loads(res.read().decode())
        print(f"Live Overview KPI Count: {len(overview['kpis'])}, Total Revenue: {overview['kpis'][0]['formatted_value']}")
        assert len(overview["kpis"]) >= 4

    print("\n>>> LIVE SERVER HTTP ENDPOINTS VERIFIED SUCCESSFULLY! <<<")
except Exception as e:
    print("Live Server Error:", e)
    sys.exit(1)
