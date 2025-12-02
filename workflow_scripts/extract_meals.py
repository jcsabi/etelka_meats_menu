#!/usr/bin/env python3
from datetime import datetime
import json
import os
import subprocess
from typing import Any

import openai
import requests


def extract_and_store_meal_for_date(year: int, month: int) -> None:
    already_available = check_meals_for_month_availability(year, month)
    if already_available:
        return
    meals = extract_meals_into_json(year, month)
    store_meals_for_month(year, month, meals)


def extract_meals_into_json(year: int, month: int) -> Any:
    month_str = f"{year}{month:02d}"
    # PDF URL
    pdf_url = f"https://suli-host.hu/wp-content/uploads/etlap/{month_str}/suli_normal_{month_str}_a.pdf"

    if not check_meals_pdf_exists_for_month(pdf_url):
        return

    # Prompt GPT-5 for structured JSON
    prompt = """
Extract the daily meals from this PDF and return JSON in this exact format:
{
  "YYYY-MM-DD": {
    "tizorai": "...",
    "ebed": "...",
    "uzsonna": "..."
  }
}
One object per day. No extra text. Please remove everything from the meals matching the pattern (...)*.
"""

    resp = openai.responses.create(
        model="gpt-5",
        input=[
            {
              "role": "user",
              "content": [
                  {
                      "type": "input_text", "text": prompt
                  },
                  {
                      "type": "input_file",
                      "file_url": pdf_url
                  }
              ]
            }
        ],
    )

    return json.loads(resp.output_text)


def check_meals_pdf_exists_for_month(url: str) -> bool:
    exists = False
    try:
        resp = requests.head(url, timeout=10, allow_redirects=True)
        exists = resp.status_code == 200 and "pdf" in resp.headers.get("Content-Type", "").lower()
    except requests.RequestException:
        pass
    print(f"The given url does not exists: {url}")
    return exists


def check_meals_for_month_availability(year: int, month: int) -> bool:
    filename = os.path.join("data", f"{year}-{month:02d}.json")
    exists = os.path.exists(filename)
    if exists:
        print(
            f"Meals for {year}.{month} already exist at {filename}, skipping.")
    return exists


def store_meals_for_month(year: int, month: int, meals: Any) -> None:
    # Save JSON
    filename = os.path.join("data", f"{year}-{month:02d}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)

    print(f"Meals saved to {filename}")

    # Commit & push
    subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "config", "user.email", "github-actions@github.com"], check=True)
    subprocess.run(["git", "add", filename], check=True)
    subprocess.run(["git", "commit", "-m", f"Add meal data for {year}-{month:02d}"], check=False)
    subprocess.run(["git", "push"], check=True)


def main():
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    # Try to extract meals for current month
    today = datetime.today()
    extract_and_store_meal_for_date(today.year, today.month)

    # Try to extract meals for next month
    year = today.year + (1 if today.month == 12 else 0)
    month = 1 if today.month == 12 else today.month + 1
    extract_and_store_meal_for_date(year, month)


if __name__ == "__main__":
    main()
