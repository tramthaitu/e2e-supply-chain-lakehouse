#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=========================================================="
echo "🚀 [APS MLOps] RUNNING DEMAND FORECAST TRAINING PIPELINE"
echo "=========================================================="

PYTHON_SCRIPT="$PROJECT_ROOT/src/scripts/train_demand_model.py"

python "$PYTHON_SCRIPT" "$@"
echo "✅ Training pipeline completed successfully!"
