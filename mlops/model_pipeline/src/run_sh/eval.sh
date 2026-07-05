#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=========================================================="
echo "📊 [APS MLOps] RUNNING MODEL EVALUATION & MAPE CHECK"
echo "=========================================================="

python -c "
import sys, os
sys.path.append('$PROJECT_ROOT/src')
from model.demand_evaluator import DemandModelEvaluator
from model.demand_forecaster_trainer import DemandForecasterTrainer
import numpy as np

np.random.seed(42)
X_test = np.random.rand(200, 5) * 100
y_test = X_test[:, 0] * 1.5 + X_test[:, 1] * 0.8 + np.random.normal(0, 10, 200)

trainer = DemandForecasterTrainer()
model = trainer.train(X_test, y_test)
evaluator = DemandModelEvaluator()
evaluator.evaluate(model, X_test, y_test)
"
