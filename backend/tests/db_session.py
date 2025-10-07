import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

POSTGRES_TEST_HOST = os.getenv("POSTGRES_TEST_HOST", "localhost")

os.environ["POSTGRES_HOST"] = POSTGRES_TEST_HOST
os.environ["POSTGRES_PORT"] = "5434"
os.environ["POSTGRES_DB"] = "nextbus_test"
os.environ["POSTGRES_USER"] = "nextbus"
os.environ["POSTGRES_PASSWORD"] = "nextbus"

TEST_DATABASE_URL = (
    f"postgresql+psycopg2://nextbus:nextbus@{POSTGRES_TEST_HOST}:5434/nextbus_test"
)


test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_size=20,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False
)
