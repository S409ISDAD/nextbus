import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from backend.config import get_logger, setup_logging

setup_logging()
log = get_logger(__name__)

BASE = "https://data.discoverpassenger.com/"
HEADERS = {
    "User-Agent": "nextbus/1.0 (contact@orbitix.dev)",
}


def scrape_passenger_data():
    r = requests.get(BASE, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    seen = set()
    sources = []
    for a in soup.select("a[href^='/operator/']"):
        href = str(a["href"])
        name = a.get_text(strip=True).removeprefix("View open data for ")
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        operator_url = urljoin(BASE, href)
        url = urljoin(operator_url + "/", "dataset/current/download/txc")
        sources.append({"name": name, "url": url})
    return sources


if __name__ == "__main__":
    data = scrape_passenger_data()
    log.debug(f"Found {len(data)} sources")
    print(json.dumps(data, indent=2))
