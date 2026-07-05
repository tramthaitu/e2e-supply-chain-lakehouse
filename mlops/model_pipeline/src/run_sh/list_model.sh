#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "📋 [APS MLOps] LISTING ALL REGISTERED MODELS"
echo "=========================================================="

python -c "
from mlflow import MlflowClient
client = MlflowClient(tracking_uri='http://localhost:5001')
models = client.search_registered_models()
for m in models:
    print(f'📌 Model: {m.name} | Latest Versions: {[v.version for v in m.latest_versions]}')
if not models:
    print('No registered models found yet.')
"
