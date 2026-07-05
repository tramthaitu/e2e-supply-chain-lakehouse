#!/usr/bin/env bash
set -e

MODEL_NAME=${1:-"APS_Demand_Forecaster_Prod"}
RUN_ID=${2:-"latest"}

echo "=========================================================="
echo "🔖 [APS MLOps] REGISTERING MODEL TO MLFLOW REGISTRY"
echo "=========================================================="

python -c "
import mlflow
from mlflow import MlflowClient
client = MlflowClient(tracking_uri='http://localhost:5001')
print(f'Attempting to register model: $MODEL_NAME')
"
