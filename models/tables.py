from sqlalchemy import Column, Integer, String, DateTime, Boolean, true, false
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base


# 1. Create a SINGLE "Base" instance.
# Think of this as a shared "Registry" or "Catalog."
# Every class that inherits from this Base will be recorded here.
# This allows SQLAlchemy to:
#   - Handle relationships between different tables.
#   - Create all tables at once using Base.metadata.create_all().
#   - Link Python objects to Database rows.
Base = declarative_base()

# --- EXAMPLE USAGE ---


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_code = Column(String(36), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(15))
    is_verified = Column(Boolean, server_default=false())
    is_active = Column(Boolean, server_default=true())
    email_verification_code = Column(String(255), unique=True, nullable=True)
    email_verification_expiry = Column(DateTime(timezone=True), nullable=True)
    password_reset_code = Column(String(255), unique=True, nullable=True)
    password_reset_expiry = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True)
    user_code = Column(String(36), nullable=False)
    score = Column(Integer, nullable=False)
    game_id = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
