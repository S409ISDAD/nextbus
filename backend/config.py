from pydantic_settings import BaseSettings

BASE = "https://bustimes.org"
VEHICLES_BASE = BASE + "/vehicles.json"
STOPS_BASE = BASE + "/stops.json"
API_BASE = BASE + "/api"


class Config(BaseSettings):
    env: str = "development"


config = Config()
