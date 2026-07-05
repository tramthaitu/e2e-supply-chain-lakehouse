import sys
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List

# Thêm path model_pipeline/src vào sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(os.path.join(ROOT_DIR, "mlops", "model_pipeline", "src"))

try:
    from model.inventory_bom_balance import InventoryBOMCalculator
    from model.procurement_lp_solver import ProcurementOptimizer
    from model.production_scheduler_lp import ProductionSchedulerAPS
except ImportError as e:
    print(f"⚠️ Warning importing modules: {e}")

app = FastAPI(
    title="Enterprise Lakehouse APS & MLOps API",
    description="API Phục vụ Kế hoạch Mua hàng (Procurement Scenarios) & Lịch Trình Sản Xuất (Production Scheduling theo OEE & Bảo trì PM10)",
    version="2.0.0"
)

class DemandPlanRequest(BaseModel):
    target_date: str = "2025-08-29"
    forecasted_fg_demand: Dict[str, float] = {"536": 1000.0, "537": 500.0}

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "E2E Lakehouse APS & MLOps Serving Engine"}

@app.post("/api/v1/plan/full-aps-schedule")
def generate_full_aps_schedule(request: DemandPlanRequest):
    inv_calc = InventoryBOMCalculator()
    net_rm_reqs = inv_calc.calculate_net_rm_requirements(request.forecasted_fg_demand)
    
    proc_opt = ProcurementOptimizer()
    procurement_plan = proc_opt.optimize_procurement_plan(net_rm_reqs)
    
    prod_sched = ProductionSchedulerAPS()
    production_schedule = prod_sched.schedule_production_plan(request.forecasted_fg_demand, start_date=request.target_date)
    
    return {
        "status": "SUCCESS",
        "planning_date": request.target_date,
        "summary": {
            "total_fg_products": len(request.forecasted_fg_demand),
            "total_rm_procured": len(procurement_plan),
            "total_production_batches": len(production_schedule)
        },
        "step_1_net_rm_requirements": net_rm_reqs,
        "step_2_procurement_plan": procurement_plan,
        "step_3_production_schedule": production_schedule
    }
