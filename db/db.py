import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus


def read_secret(path: str) -> str:
    with open(path, "r") as f:
        return f.read().strip()


# In Docker test environment DATABASE_URL is injected directly via env var.
# In production Docker it reads the password from a Docker secret.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_PASSWORD = quote_plus(read_secret("/run/secrets/passwords"))
    DATABASE_URL = f"mysql+pymysql://root:{DB_PASSWORD}@mysql:3306/leaderboard_db"

print("Connecting to database at:", DATABASE_URL)
engine = create_engine(
    DATABASE_URL,
    # Sends a lightweight "SELECT 1" before using a pooled connection.
    # If MySQL killed the connection due to idle timeout,
    # SQLAlchemy will automatically reconnect instead of crashing.
    pool_pre_ping=True,
    # Forces connections to be recycled every hour.
    # Prevents "MySQL server has gone away" errors.
    pool_recycle=3600,
)

# A factory that creates Session objects. Think of a session as a single "transaction" or "conversation" with the DB.
SessionLocal = sessionmaker(
    # Prevents automatic commits (safer transactions)
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
