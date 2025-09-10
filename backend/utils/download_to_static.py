import pathlib
import requests


def download_to_static(url: str, filename: str):
    script_dir = pathlib.Path(__file__).resolve().parent
    static_data_dir = script_dir / "../../static_data"
    static_data_dir = static_data_dir.resolve()  # normalize path

    path = static_data_dir / filename

    response = requests.get(url)

    if response.status_code == 200:
        with open(path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded updated file: {path}")

        return path
    return None
