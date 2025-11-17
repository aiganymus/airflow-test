import requests
import sqlite3
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "demo.db"
EXPORT_PATH = BASE_DIR / "merged_output.csv"


def fetch_api_data() -> None:
    """Fetch users from a public API and write them to SQLite (table api_users)."""
    print("Fetching API data...")

    url = "https://jsonplaceholder.typicode.com/users"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data)
    df["city"] = df["address"].apply(
        lambda x: x.get("city") if isinstance(x, dict) else None
    )
    df = df[["id", "name", "email", "city"]].rename(columns={"id": "user_id"})

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("api_users", conn, if_exists="replace", index=False)
    conn.close()

    print("API data saved:", len(df), "rows")


def scrape_quote() -> None:
    """
    Scrape one random quote + author and append to SQLite (table scraped_quotes).
    """
    print("Scraping quote site...")

    url = "https://quotes.toscrape.com/random"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    quote_div = soup.find("div", class_="quote")
    if quote_div is None:
        print("Could not parse quote page correctly")
        return

    text_span = quote_div.find("span", class_="text")
    author_small = quote_div.find("small", class_="author")

    if text_span is None or author_small is None:
        print("Could not find quote or author")
        return

    quote = text_span.text.strip()
    author = author_small.text.strip()

    df = pd.DataFrame([{"quote": quote, "author": author}])

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("scraped_quotes", conn, if_exists="append", index=False)
    conn.close()

    print("Scraped quote:", quote, "—", author)


def merge_and_export() -> None:
    """Read SQLite tables, merge, clean, export to CSV."""
    print("Merging data...")

    conn = sqlite3.connect(DB_PATH)

    api_df = pd.read_sql("SELECT * FROM api_users", conn)
    quotes_df = pd.read_sql("SELECT * FROM scraped_quotes", conn)

    if len(quotes_df) == 0:
        print("No quotes scraped yet, nothing to merge.")
        conn.close()
        return

    sampled = quotes_df.sample(n=len(api_df), replace=True).reset_index(drop=True)
    api_df["quote"] = sampled["quote"]
    api_df["quote_author"] = sampled["author"]

    api_df["email"] = api_df["email"].str.lower()
    api_df = api_df.drop_duplicates(subset=["user_id"]).reset_index(drop=True)

    api_df.to_csv(EXPORT_PATH, index=False)

    conn.close()

    print("Exported merged CSV ->", EXPORT_PATH)


if __name__ == "__main__":
    fetch_api_data()
    scrape_quote()
    merge_and_export()
