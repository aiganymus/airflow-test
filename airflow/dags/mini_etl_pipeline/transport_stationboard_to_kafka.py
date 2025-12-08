"""
Script: transport_stationboard_to_kafka.py

Description:
    - Fetches live public transport departure data from the Swiss
      public transport API (https://transport.opendata.ch/).
    - Uses the "stationboard" endpoint to get upcoming departures
      for a given station (e.g. Zurich main station).
    - Cleans and normalizes the JSON response into a flat pandas DataFrame.
    - Sends each row as a JSON message to a Kafka topic.

Intended usage:
    - Can be executed as a standalone script (e.g. from terminal).
    - Can be wrapped inside an Airflow task for scheduled runs
      (for example, every 10 minutes).

Requirements:
    - requests
    - pandas
    - kafka-python-ng  (or kafka-python)
"""

import json
from datetime import datetime, timezone

import pandas as pd
import requests
from kafka import KafkaProducer


# === CONFIGURATION ===

# Public transport API endpoint:
# Documentation: https://transport.opendata.ch/docs.html
# We call the "stationboard" endpoint to get upcoming departures
# for a specific station.
TRANSPORT_API_URL = "https://transport.opendata.ch/v1/stationboard"

# Station name for which we want the timetable.
# You can change "Zurich" to e.g. "Bern", "Geneva", etc.
STATION_NAME = "Zurich"

# How many upcoming departures to request.
STATIONBOARD_LIMIT = 20

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "transport_stationboard"


def fetch_stationboard(
    station_name: str = STATION_NAME,
    limit: int = STATIONBOARD_LIMIT,
) -> dict:
    """
    Fetch raw stationboard data (JSON) from the Swiss public transport API.

    Params:
        station_name: Name of the station (e.g. "Zurich").
        limit: Number of upcoming departures to request.

    Returns:
        Parsed JSON (Python dict) from the API response.

    Raises:
        requests.HTTPError if the API returns a non-200 status code.
    """
    params = {
        "station": station_name,
        "limit": limit,
    }

    response = requests.get(TRANSPORT_API_URL, params=params, timeout=10)
    response.raise_for_status()  # raise error if HTTP status is not 200

    return response.json()


def normalize_stationboard(raw_json: dict) -> pd.DataFrame:
    """
    Convert raw stationboard JSON into a flat pandas DataFrame
    and perform basic cleaning / normalization.

    The original JSON structure (simplified):

    {
      "station": {...},
      "stationboard": [
        {
          "name": "IC 8",
          "to": "Bern",
          "category": "IC",
          "number": "8",
          "operator": "SBB",
          "stop": {
            "departure": "2025-02-12T12:07:00+0100",
            "platform": "31"
          },
          ...
        },
        ...
      ]
    }

    We want a flat table like:

    train_name   destination   category   number   operator   platform   departure_time   ingested_at   station_name
    ----------   -----------   --------   ------   --------   --------   --------------   -----------   -----------
    IC 8         Bern          IC         8        SBB        31         2025-02-12 ...   2025-02-12    Zürich HB

    Basic cleaning steps:
        - Extract fields from each stationboard entry (flatten nested "stop").
        - Convert departure timestamp to pandas datetime (UTC).
        - Drop rows without valid departure time.
        - Add ingestion timestamp (UTC).
        - Add station name from the JSON root.
    """
    station_info = raw_json.get("station", {}) or {}
    station_name = station_info.get("name", None)

    # "stationboard" is a list of departures
    stationboard = raw_json.get("stationboard", []) or []

    if not stationboard:
        # No departures – return empty DataFrame with expected columns
        df_empty = pd.DataFrame(
            columns=[
                "train_name",
                "destination",
                "category",
                "number",
                "operator",
                "platform",
                "departure_time",
                "ingested_at",
                "station_name",
            ]
        )
        return df_empty

    # Normalize JSON into a DataFrame.
    # pandas.json_normalize automatically flattens nested keys like "stop.departure".
    df = pd.json_normalize(stationboard)

    # Rename columns to more readable names if they exist
    rename_map = {
        "name": "train_name",
        "to": "destination",
        "category": "category",
        "number": "number",
        "operator": "operator",
        "stop.platform": "platform",
        "stop.departure": "departure_time_raw",
    }
    df = df.rename(columns=rename_map)

    # Keep only relevant columns (ignore extra metadata for now)
    expected_cols = [
        "train_name",
        "destination",
        "category",
        "number",
        "operator",
        "platform",
        "departure_time_raw",
    ]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    # Convert departure_time_raw to a proper datetime.
    # API returns strings like "2025-02-12T12:07:00+0100".
    if "departure_time_raw" in df.columns:
        df["departure_time"] = pd.to_datetime(
            df["departure_time_raw"], errors="coerce"
        )
        # Drop rows where departure_time could not be parsed
        df = df.dropna(subset=["departure_time"])
        # Convert to UTC (optional but recommended)
        df["departure_time"] = df["departure_time"].dt.tz_convert("UTC")
        # We no longer need the raw string column
        df = df.drop(columns=["departure_time_raw"])
    else:
        # If there is no departure column at all, create an empty one
        df["departure_time"] = pd.NaT

    # Add ingestion timestamp (UTC)
    ingested_at = datetime.now(timezone.utc)
    df["ingested_at"] = ingested_at

    # Add station_name column from the root JSON, if available
    df["station_name"] = station_name

    # Optional: ensure all string columns are stripped of whitespace
    for col in ["train_name", "destination", "category", "number", "operator", "platform", "station_name"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    return df


def send_dataframe_to_kafka(df: pd.DataFrame) -> None:
    """
    Send each row of the DataFrame as a JSON message to a Kafka topic.

    - Each DataFrame row becomes one Kafka message.
    - We serialize the row as a Python dict, then dump it to JSON.
    - The message value is sent as UTF-8 encoded bytes.

    If the DataFrame is empty, this function simply prints a message and returns.
    """
    if df.empty:
        print("[INFO] No data to send to Kafka (DataFrame is empty).")
        return

    # Initialize a Kafka producer.
    # Note: `kafka-python-ng` / `kafka-python` must be installed in your `.venv`.
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    sent_count = 0

    # Iterate over DataFrame rows and send each one as a separate message.
    for _, row in df.iterrows():
        # Convert row to a plain Python dict of basic types.
        # We also convert Timestamp objects to ISO strings manually
        # to avoid JSON serialization issues.
        message = row.to_dict()

        # Convert datetime columns to ISO 8601 strings
        if isinstance(message.get("departure_time"), pd.Timestamp):
            message["departure_time"] = message["departure_time"].isoformat()
        if isinstance(message.get("ingested_at"), pd.Timestamp):
            message["ingested_at"] = message["ingested_at"].isoformat()

        # Send message to Kafka
        producer.send(KAFKA_TOPIC, value=message)
        sent_count += 1

    # Make sure all messages are actually sent
    producer.flush()
    producer.close()

    print(f"[INFO] Sent {sent_count} messages to Kafka topic '{KAFKA_TOPIC}'.")


def run_pipeline() -> None:
    """
    High-level function that runs one full cycle of the pipeline:

        1. Fetch raw stationboard JSON from public transport API.
        2. Normalize & clean it into a pandas DataFrame.
        3. Send each row as a JSON message to Kafka.

    This is the function that you would typically call from:
        - a standalone script (manual run), or
        - an Airflow task (scheduled run every 10 minutes).
    """
    print("[INFO] Fetching stationboard data from Swiss Transport API...")
    raw_json = fetch_stationboard()

    print("[INFO] Normalizing and cleaning data with pandas...")
    df = normalize_stationboard(raw_json)

    print(f"[INFO] Data prepared: {len(df)} rows.")
    print("[INFO] Sending data to Kafka...")
    send_dataframe_to_kafka(df)
    print("[INFO] Pipeline run completed.")


if __name__ == "__main__":
    # For manual testing:
    # Run this script directly to perform one pipeline execution.
    run_pipeline()
