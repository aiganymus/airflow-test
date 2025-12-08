"""
DAG: transport_stationboard_to_kafka

Purpose:
    - Run the "public transport stationboard → Kafka" pipeline every 10 minutes.
    - The pipeline itself is implemented in `transport_stationboard_to_kafka.py`,
      in the function `run_pipeline_once()`.

Context:
    - This DAG is part of a teaching demo for the course
      "Data Collection and Preparation".
    - It shows how Airflow can orchestrate a small streaming-like pipeline
      that fetches public transport data from a REST API, cleans it with pandas,
      and publishes the result to a Kafka topic.

Files:
    - dag.py
    - transport_stationboard_to_kafka.py

Both files should live in the same directory under the Airflow DAGs folder, e.g.:

    $AIRFLOW_HOME/dags/transport_demo/dag.py
    $AIRFLOW_HOME/dags/transport_demo/transport_stationboard_to_kafka.py
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# -------------------------------------------------------------------
# Ensure that Airflow can import the pipeline module
# -------------------------------------------------------------------
# This assumes the current file (dag.py) is in the same directory as
# `transport_stationboard_to_kafka.py`. We add that directory to sys.path
# so that "import transport_stationboard_to_kafka" works reliably.
FILE_DIR = Path(__file__).resolve().parent
if str(FILE_DIR) not in sys.path:
    sys.path.append(str(FILE_DIR))

# Now we can import the function that runs one full pipeline execution.
# The module `transport_stationboard_to_kafka.py` should define:
#     def run_pipeline_once() -> None: ...
from transport_stationboard_to_kafka import run_pipeline


# -------------------------------------------------------------------
# Default arguments for the DAG
# -------------------------------------------------------------------
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    # If a run fails, Airflow will retry it once after 5 minutes.
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    # Do not send emails by default (can be changed if needed).
    "email_on_failure": False,
    "email_on_retry": False,
}


# -------------------------------------------------------------------
# DAG definition
# -------------------------------------------------------------------
with DAG(
    dag_id="transport_stationboard_to_kafka",
    description=(
        "Fetch public transport stationboard data from Swiss Transport API, "
        "clean it with pandas, and send it to a Kafka topic. "
        "Scheduled every 10 minutes."
    ),
    # Start date in the past: Airflow will be able to schedule from this date.
    start_date=datetime(2025, 1, 1),
    # Run every 10 minutes
    schedule="*/10 * * * *",
    catchup=False,  # do not backfill historical runs
    default_args=default_args,
    tags=["demo", "transport", "kafka", "api"],
) as dag:

    # Single Python task that runs the full pipeline:
    #   1) fetch JSON from public transport API
    #   2) normalize & clean with pandas
    #   3) send each row as a JSON message to Kafka
    run_transport_pipeline = PythonOperator(
        task_id="run_transport_stationboard_pipeline",
        python_callable=run_pipeline,
    )

    # If you ever add more tasks (e.g. additional checks, notifications),
    # you can define dependencies here. For now we have just one task.
    run_transport_pipeline
