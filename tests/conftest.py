import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import Mock
import pytest
from sqlalchemy import text
from models.request import LoginRequest, RegisterRequest
from models.response import UserProfileResponse


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_db():
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def sample_register_request():
    return RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="Secure@Pass123",
        phone_number="01234567890",
    )


@pytest.fixture
def sample_login_request():
    return LoginRequest(username="testuser", password="SecurePass123")


@pytest.fixture
def mock_user(mocker):
    user = mocker.Mock(id=1, username="testuser", password_hash="hashed")
    return user


@pytest.fixture
def db_session(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_user_from_db():
    user = Mock()
    user.id = 1
    user.username = "testuser"
    user.avatar_url = "https://example.com/avatar.jpg"
    user.is_verified = True
    user.created_at = "2024-01-01"
    user.is_active = True
    return user


@pytest.fixture
def mock_different_user():
    user = Mock()
    user.id = 2
    user.username = "otheruser"
    user.avatar_url = "https://example.com/other.jpg"
    return user


@pytest.fixture
def mock_current_user():
    return UserProfileResponse(
        id=1,
        username="testuser",
        avatar_url="https://example.com/avatar.jpg",
        games={"game_001": {"score": 100, "rank": 1}},
        is_verified=True,
        created_at="2024-01-01",
    )


@pytest.fixture
def mock_upload_file():
    file = Mock()
    file.filename = "avatar.jpg"
    file.file = Mock()
    return file


@pytest.fixture
def client(mocker):
    from app import app
    from config.db import engine
    from config.redis import redis_client
    from models.tables import Base

    for attempt in range(10):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            break
        except Exception:
            if attempt == 9:
                raise
            time.sleep(1)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    redis_client.flushdb()

    async def fake_send_verification_email(*args, **kwargs):
        return True

    mocker.patch(
        "controllers.auth.send_verification_email",
        side_effect=fake_send_verification_email,
    )
    mocker.patch(
        "controllers.auth.fast_mail.send_message",
        new=AsyncMock(return_value=None),
    )

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    redis_client.flushdb()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def get_user():
    from config.db import SessionLocal
    from models.tables import User

    def _get_user(username: str):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.username == username).first()
        finally:
            db.close()

    return _get_user


@pytest.fixture
def register_verified_user(client, get_user):
    def _register_verified_user(
        username: str,
        email: str,
        phone_number: str,
        password: str = "Secure@Pass123",
    ):
        register_response = client.post(
            "/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "phone_number": phone_number,
            },
        )
        assert register_response.status_code == 201, register_response.json()

        user = get_user(username)
        client.get("/auth/verify-email", params={"code": user.email_verification_code})

        login_response = client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert login_response.status_code == 200, login_response.json()
        token = login_response.json()["token"]

        return {
            "username": username,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    return _register_verified_user
