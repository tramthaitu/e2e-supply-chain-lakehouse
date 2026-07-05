import mlflow
from mlflow import MlflowClient
from mlflow.entities.model_registry import ModelVersion

class ModelRegistry:
    """
    Wrapper đầy đủ quản lý Đăng ký, Alias và Chuyển trạng thái mô hình (Tái sử dụng 100% đầy đủ các hàm từ mẫu).
    """
    def __init__(self, tracking_uri: str = "http://localhost:5001"):
        self.client = MlflowClient(tracking_uri=tracking_uri)
        mlflow.set_tracking_uri(tracking_uri)

    def retrieve_eval_metrics_based_on_run_id(self, run_id: str, metric: str):
        all_experiments = mlflow.search_runs(search_all_experiments=True)
        evaluation = all_experiments[
            (all_experiments["tags.source_run_id"] == f"{run_id}") &
            (all_experiments["status"] == "FINISHED")
        ]
        if evaluation.empty:
            try:
                run = self.client.get_run(run_id)
                return run.data.metrics.get(metric)
            except Exception:
                return None
        latest_eval = evaluation.sort_values(by="end_time", ascending=False).head(1)
        eval_run_id = latest_eval['run_id'].values.tolist()[0]
        eval_run = self.client.get_run(eval_run_id)
        return eval_run.data.metrics.get(metric)

    def register_model(
        self,
        model_uri: str,
        model_name: str,
        tags: dict[str, str] | None = None,
        description: str | None = None
    ) -> ModelVersion:
        print(f"🔖 [ModelRegistry] Registering model: {model_name} from {model_uri}")
        try:
            self.client.get_registered_model(model_name)
        except Exception:
            print(f"Registered model '{model_name}' not found. Creating it.")
            self.client.create_registered_model(name=model_name, description=description)

        model_version = self.client.create_model_version(
            name=model_name,
            source=model_uri,
            run_id=model_uri.split("/")[1] if "runs:" in model_uri else None,
            description=description,
        )

        if tags:
            for k, v in tags.items():
                self.client.set_model_version_tag(
                    name=model_name,
                    version=model_version.version,
                    key=k,
                    value=v
                )
        return model_version

    def create_registered_model(self, name: str, tags: dict[str, str] | None = None, description: str | None = None):
        try:
            self.client.create_registered_model(name=name, tags=tags, description=description)
        except Exception as e:
            print(f"Notice: Model {name} may already exist: {e}")

    def set_model_version_alias(self, model_name: str, version: str, alias: str):
        print(f"🎯 Setting alias '{alias}' for {model_name} v{version}")
        self.client.set_registered_model_alias(name=model_name, alias=alias, version=version)

    def delete_model_version_alias(self, model_name: str, alias: str):
        self.client.delete_registered_model_alias(name=model_name, alias=alias)

    def get_model_version_by_alias(self, model_name: str, alias: str) -> ModelVersion:
        return self.client.get_model_version_by_alias(name=model_name, alias=alias)

    def get_latest_versions(self, model_name: str, stages: list[str] | None = None) -> list[ModelVersion]:
        return self.client.get_latest_versions(name=model_name, stages=stages)

    def search_model_versions(self, filter_string: str = "", max_results: int = 100) -> list[ModelVersion]:
        return self.client.search_model_versions(filter_string=filter_string, max_results=max_results)

    def transition_model_version_stage(self, model_name: str, version: str, stage: str, archive_existing_versions: bool = True):
        print(f"🔄 Transitioning {model_name} v{version} to {stage}")
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=archive_existing_versions,
        )

    def delete_model_version(self, model_name: str, version: str):
        self.client.delete_model_version(name=model_name, version=version)

    def get_model_info(self, model_name: str) -> dict:
        model = self.client.get_registered_model(model_name)
        versions = self.client.search_model_versions(f"name='{model_name}'")
        return {
            "name": model.name,
            "description": model.description,
            "creation_timestamp": model.creation_timestamp,
            "last_updated_timestamp": model.last_updated_timestamp,
            "versions": [
                {
                    "version": v.version,
                    "stage": v.current_stage,
                    "status": v.status,
                    "run_id": v.run_id,
                }
                for v in versions
            ],
        }

    def list_registered_models(self, max_results: int = 100):
        models = self.client.search_registered_models(max_results=max_results)
        return [model.name for model in models]

    def promote_model(
        self,
        model_name: str,
        version: str | None,
        from_alias: str = "staging",
        to_alias: str = "champion",
        metric_name: str = "mape_pct",
        require_improvement: bool = True,
    ):
        print(f"🏆 Promoting {model_name} v{version} as global {to_alias}")
        if version is None:
            versions = self.get_latest_versions(model_name=model_name)
            if not versions:
                return False
            version = max(versions, key=lambda v: int(v.version)).version

        try:
            self.delete_model_version_alias(model_name=model_name, alias=from_alias)
        except Exception:
            pass

        self.set_model_version_alias(model_name=model_name, version=version, alias=to_alias)
        print(f"✅ Global champion is now {model_name} v{version}")
        return True
