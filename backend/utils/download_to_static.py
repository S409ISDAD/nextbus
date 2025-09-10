import requests

from backend.deps import STATIC_DATA_DIR


def download_to_static(url: str, filename: str):
    path = STATIC_DATA_DIR / filename

    response = requests.get(url)

    if response.status_code == 200:
        with open(path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded updated file: {path}")

        return path
    return None
