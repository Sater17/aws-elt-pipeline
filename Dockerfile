FROM python:3.12-slim

WORKDIR /opt/dagster/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY orchestration ./orchestration
COPY ingestion ./ingestion
COPY dbt ./dbt

ENV PYTHONPATH=/opt/dagster/app