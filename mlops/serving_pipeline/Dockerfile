FROM python:3.10-slim

WORKDIR /app

# Cài đặt các thư viện cần thiết cho FastAPI và APS Solver
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# Copy toàn bộ code mlops vào container
COPY . /app/mlops

WORKDIR /app/mlops/serving_pipeline

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
