from datetime import datetime
from pathlib import Path
import sys

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# Ensure this directory is on sys.path so we can import pipeline.py
FILE_DIR = Path(__file__).resolve().parent
if str(FILE_DIR) not in sys.path:
    sys.path.append(str(FILE_DIR))

from pipeline import fetch_api_data, scrape_quote, merge_and_export


with DAG(
    dag_id="demo_api_scrape_merge",
    start_date=datetime(2025, 11, 16),
    schedule="@daily",
    catchup=False,
    description="Demo DAG: API + Web Scraping (quotes) + Merge & Export",
) as dag:

    task_api = PythonOperator(
        task_id="extract_api",
        python_callable=fetch_api_data,
    )

    task_scrape = PythonOperator(
        task_id="scrape_website",
        python_callable=scrape_quote,
    )

    task_merge = PythonOperator(
        task_id="merge_and_export",
        python_callable=merge_and_export,
    )

    [task_api, task_scrape] >> task_merge
