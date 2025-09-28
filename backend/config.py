import logging
from logging.config import dictConfig
import pathlib
import sys
from pydantic_settings import BaseSettings
import os
import dotenv

BASE = "https://bustimes.org"
VEHICLES_BASE = BASE + "/vehicles.json"
STOPS_BASE = BASE + "/stops.json"
API_BASE = BASE + "/api"

dotenv.load_dotenv()


class Config(BaseSettings):
    env: str = "development"
    bods_api_key: str | None = os.getenv("BODS_API_KEY", None)


config = Config()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "standard",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",
            "maxBytes": 1024 * 1024 * 10,
            "backupCount": 5,
        },
    },
    "loggers": {
        "backend": {
            "handlers": ["console", "file"],
            "level": "DEBUG",  # adjust per env
            "propagate": False,
        },
        "apscheduler": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "watchfiles": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": False,
        },
        # "uvicorn": {
        #     "handlers": ["console"],
        #     "level": "INFO",
        #     "propagate": False,
        # },
        # "uvicorn.error": {
        #     "handlers": ["console"],
        #     "level": "INFO",
        #     "propagate": False,
        # },
        # "uvicorn.access": {
        #     "handlers": ["console"],
        #     "level": "INFO",
        #     "propagate": False,
        # },
    },
}


def setup_logging():
    dictConfig(LOGGING_CONFIG)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a logger that respects your package hierarchy,
    even if the module is run as __main__.
    """
    if name == "__main__":
        try:
            file_path = pathlib.Path(sys.modules["__main__"].__file__).resolve()
            pkg_root = "backend"
            parts = file_path.parts
            idx = parts.index(pkg_root)
            module_parts = parts[idx:]
            module_name = ".".join(module_parts).removesuffix(".py")
            name = module_name
        except Exception:
            name = "backend"
    elif not name:
        name = "backend"

    return logging.getLogger(name)
