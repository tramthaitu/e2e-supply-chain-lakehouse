#!/usr/bin/env bash
set -e

MODEL_NAME=${1:-"APS_Demand_Forecaster_Prod"}
ALIAS=${2:-"champion"}
VERSION=${3:-"1"}

echo "=========================================================="
echo "🎯 [APS MLOps] SETTING ALIAS '@$ALIAS' TO VERSION $VERSION"
echo "=========================================================="

python -c "
from mlflow import MlflowClient
client = MlflowClient(tracking_uri='http://localhost:5001')
try:
    client.set_registered_model_alias('$MODEL_NAME', '$ALIAS', '$VERSION')
    print(f'✅ Successfully set alias @$ALIAS to $MODEL_NAME version $VERSION!')
except Exception as e:
    print(f'⚠️ Error setting alias: {e}')
"
