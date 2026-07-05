#!/usr/bin/env bash
set -e

MODEL_NAME=${1:-"APS_Demand_Forecaster_Prod"}

echo "=========================================================="
echo "ℹ️ [APS MLOps] FETCHING MODEL INFO FOR: $MODEL_NAME"
echo "=========================================================="

python -c "
from mlflow import MlflowClient
client = MlflowClient(tracking_uri='http://localhost:5001')
try:
    model = client.get_registered_model('$MODEL_NAME')
    print(f'Name: {model.name}')
    print(f'Description: {model.description}')
    for v in model.latest_versions:
        print(f'  -> Version: {v.version} | Stage: {v.current_stage} | Run ID: {v.run_id}')
except Exception as e:
    print(f'Model not found or error: {e}')
"
