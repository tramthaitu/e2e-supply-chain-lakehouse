import mlflow
from typing import Any
from contextlib import contextmanager
from mlflow import MlflowClient
from mlflow.entities.run import Run
from mlflow.store.entities.paged_list import PagedList

class ExperimentTracker:
    """
    Wrapper đầy đủ quản lý MLflow Experiment Tracking (Tái sử dụng 100% toàn bộ phương thức từ project mẫu).
    """
    def __init__(
        self,
        tracking_uri: str = "http://localhost:5001",
        experiment_name: str = "Supply_Chain_Demand_Forecasting",
        artifact_location: str | None = None
    ):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.artifact_location = artifact_location

        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri=tracking_uri)
        self.experiment_id = self._get_or_create_experiment()
        print(f"📦 [ExperimentTracker] Initialized: {self.experiment_name} | ID: {self.experiment_id}")

    def _get_or_create_experiment(self) -> str:
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                name=self.experiment_name,
                artifact_location=self.artifact_location
            )
        else:
            experiment_id = experiment.experiment_id
        return experiment_id

    @contextmanager
    def start_run(
        self,
        run_name: str | None = None,
        tags: dict[str, Any] | None = None,
        nested: bool = True
    ):
        with mlflow.start_run(
            experiment_id=self.experiment_id,
            run_name=run_name,
            nested=nested
        ) as run:
            if tags:
                mlflow.set_tags(tags)
            print(f"▶️ [MLflow] Started run: {run.info.run_id} ({run_name})")
            yield run
            print(f"⏹️ [MLflow] Completed run: {run.info.run_id}")

    def log_param(self, key: str, value: Any):
        mlflow.log_param(key, value)

    def log_params(self, params: dict[str, Any]):
        mlflow.log_params(params)

    def log_metric(self, key: str, value: float, step: int | None = None):
        mlflow.log_metric(key, value, step=step)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None):
        mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, local_path: str, artifact_path: str | None = None):
        mlflow.log_artifact(local_path, artifact_path)

    def log_dict(self, dictionary: dict, filename: str):
        mlflow.log_dict(dictionary, filename)

    def set_tag(self, key: str, value: Any):
        mlflow.set_tag(key, value)

    def set_tags(self, tags: dict[str, Any]):
        mlflow.set_tags(tags)

    def get_run(self, run_id: str):
        return self.client.get_run(run_id)

    def search_runs(
        self,
        filter_string: str = "",
        max_results: int = 100,
        order_by: list | None = None,
    ) -> PagedList[Run]:
        return self.client.search_runs(
            experiment_ids=[self.experiment_id],
            filter_string=filter_string,
            max_results=max_results,
            order_by=order_by,
        )

    def get_best_run(self, metric_name: str, ascending: bool = False):
        order = "ASC" if ascending else "DESC"
        runs = self.search_runs(
            max_results=1,
            order_by=[f"metrics.{metric_name} {order}"],
        )
        if not runs:
            return None
        best_run = runs[0]
        print(f"🏆 Best run: {best_run.info.run_id} with {metric_name}={best_run.data.metrics.get(metric_name)}")
        return best_run

    def end_run(self):
        mlflow.end_run()
