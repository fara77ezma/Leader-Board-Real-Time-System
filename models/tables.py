from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    true,
    false,
    ForeignKey,
)
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
    avatar_url = Column(String(255), nullable=True)
    is_admin = Column(Boolean, server_default=false())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True)
    user_code = Column(
        String(36), ForeignKey("users.user_code", ondelete="CASCADE"), nullable=False
    )
    score = Column(Integer, nullable=False)
    game_id = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class Game(Base):
    __tablename__ = "game"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=true())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


# TODO know how docker read the new table and update it in the database without deleting the old one and losing data
# TODO know when docker creates a new table
class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True)
    user_code = Column(
        String(36), ForeignKey("users.user_code", ondelete="CASCADE"), nullable=False
    )
    game_id = Column(
        String(50), ForeignKey("game.name", ondelete="CASCADE"), nullable=False
    )
    score = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
