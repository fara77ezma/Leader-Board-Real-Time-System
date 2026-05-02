import sys
from pathlib import Path
from unittest.mock import Mock
import pytest
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
