#!/usr/bin/env bash
set -e

MODEL_NAME=${1:-"APS_Demand_Forecaster_Prod"}
VERSION=${2:-"1"}
STAGE=${3:-"Production"}

echo "=========================================================="
echo "🚀 [APS MLOps] PROMOTING MODEL TO $STAGE STAGE"
echo "=========================================================="

python -c "
from mlflow import MlflowClient
client = MlflowClient(tracking_uri='http://localhost:5001')
try:
    client.transition_model_version_stage(
        name='$MODEL_NAME',
        version='$VERSION',
        stage='$STAGE'
    )
    print(f'✅ Successfully promoted $MODEL_NAME v$VERSION to $STAGE!')
except Exception as e:
    print(f'⚠️ Notice: {e}')
"
