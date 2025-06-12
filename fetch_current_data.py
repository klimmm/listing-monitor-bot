#!/usr/bin/env python3
import requests
import json
import os

def fetch_latest_data():
    """Fetch latest current_data.json from GitHub"""
    # Try to get GitHub token from environment variable first, then file
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("ERROR: No GitHub token found!")
        return

    # Use GitHub API to get the file
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
        headers["Accept"] = "application/vnd.github.v3.raw"

    url = "https://api.github.com/repos/klimmm/cian-telegram-bot/contents/current_data.json"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        with open("current_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Updated local data: {len(data)} offers")
    else:
        print(f"❌ Failed to fetch data: {response.status_code}")
        if response.status_code == 404:
            print("Make sure the repository exists and is accessible")


if __name__ == "__main__":
    fetch_latest_data()
