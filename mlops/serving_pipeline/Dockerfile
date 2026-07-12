FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pandas \
    numpy \
    scikit-learn \
    xgboost \
    mlflow \
    pydantic \
    requests

COPY . /app

ENV PYTHONPATH="/app"

EXPOSE 8000

CMD ["uvicorn", "mlops.serving_pipeline.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
