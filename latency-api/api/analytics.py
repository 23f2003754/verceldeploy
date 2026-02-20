import json
import numpy as np
import pandas as pd
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import os

# Load the static JSON data (in real app, this might come from a DB/S3)
with open('q-vercel-latency.json', 'r') as f:
    raw_data = json.load(f)

# Convert to DataFrame for easy stats (one row per ping)
df = pd.DataFrame(raw_data)

def handler(request: Request):
    # Parse POST body
    body = request.body()
    if not body:
        return JSONResponse({"error": "No body"}, status_code=400)
    
    try:
        data = json.loads(body)
        regions = data.get("regions", [])
        threshold_ms = data.get("threshold_ms", 180)
    except:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    
    if not regions:
        return JSONResponse({"error": "No regions"}, status_code=400)
    
    # Filter data for requested regions
    region_data = df[df['region'].isin(regions)]
    
    if region_data.empty:
        return JSONResponse({"error": "No data for regions"}, status_code=404)
    
    # Group by region and compute metrics
    results = {}
    for region in regions:
        region_df = df[df['region'] == region]
        if region_df.empty:
            results[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue
        
        latencies = region_df['latency_ms'].values
        uptimes = region_df['uptime'].values  # assuming uptime is 0-1 or percentage
        
        results[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": int(np.sum(latencies > threshold_ms))
        }
    
    # CORS headers for POST from anywhere
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }
    
    return JSONResponse(results, headers=headers)

# Vercel serverless handler
def main(request: Request):
    if request.method == "OPTIONS":
        return Response(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
    return handler(request)
