import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_searchable import sync_trigger

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sync_search_vectors():
    with engine.begin() as conn:
        sync_trigger(
            conn,
            "stop",
            "search_vector",
            [
                "common_name",
                "common_short_name",
                "landmark",
                "street",
                "suburb",
                "town",
            ],
        )
        sync_trigger(
            conn,
            "service",
            "search_vector",
            [
                "line_name",
                "line_brand",
                "description",
                "vias",
            ],
        )
        sync_trigger(
            conn,
            "operator",
            "search_vector",
            ["name", "noc"],
        )
        sync_trigger(
            conn,
            "locality",
            "search_vector",
            [
                "name",
                "qualifier_name",
            ],
        )
