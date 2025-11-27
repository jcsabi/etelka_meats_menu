#!/usr/bin/env python3
from datetime import datetime
import json
import os
import subprocess

import openai


def main():
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    # Determine next month
    today = datetime.today()
    year = today.year + (1 if today.month == 12 else 0)
    month = 1 if today.month == 12 else today.month + 1
    next_month_str = f"{year}{month:02d}"

    # PDF URL
    pdf_url = f"https://suli-host.hu/wp-content/uploads/etlap/{next_month_str}/suli_normal_{next_month_str}_a.pdf"

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
    One object per day. No extra text.
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

    meals = json.loads(resp.output_text)

    # Save JSON
    filename = f"{year}-{month:02d}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(meals, f, ensure_ascii=False, indent=2)

    print(f"Meals saved to {filename}")

    # Commit & push
    subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "config", "user.email", "github-actions@github.com"], check=True)
    subprocess.run(["git", "add", filename], check=True)
    subprocess.run(["git", "commit", "-m", f"Add meal data for {year}-{month:02d}"], check=False)
    subprocess.run(["git", "push"], check=True)


if __name__ == "__main__":
    main()
