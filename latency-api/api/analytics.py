import json
import numpy as np
import pandas as pd
import os

# Load data at module level (faster)
with open('q-vercel-latency.json', 'r') as f:
    raw_data = json.load(f)
df = pd.DataFrame(raw_data)

def main(request):
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return 200, {'Access-Control-Allow-Origin': '*'}
    
    # Parse JSON body
    try:
        body = json.loads(request.body)
        regions = body.get('regions', [])
        threshold_ms = body.get('threshold_ms', 180)
    except:
        return 400, {'error': 'Invalid JSON'}
    
    if not regions:
        return 400, {'error': 'No regions'}
    
    # Compute metrics per region
    results = {}
    for region in regions:
        region_df = df[df['region'] == region]
        if region_df.empty:
            results[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue
        
        latencies = region_df['latency_ms'].dropna()
        uptimes = region_df['uptime'].dropna()
        
        results[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": int((latencies > threshold_ms).sum())
        }
    
    headers = {'Access-Control-Allow-Origin': '*'}
    return 200, results

# Vercel REQUIRED export name
export = main
