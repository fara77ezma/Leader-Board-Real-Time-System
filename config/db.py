import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus


# Helper: read Docker secret
def read_secret(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback to env var during testing/local dev
        return os.environ.get("DB_PASSWORD", "fallback_test_password")


# quote_plus is used to safely encode special characters in the password
DB_PASSWORD = quote_plus(read_secret("/run/secrets/passwords"))

# - mysql        → Docker service name (NOT localhost)
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
