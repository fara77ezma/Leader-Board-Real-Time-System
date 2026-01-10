import sys
from pathlib import Path
from unittest.mock import Mock
import pytest
from models.request import LoginRequest, RegisterRequest


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
        password="SecurePass123",
        phone_number="1234567890",
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