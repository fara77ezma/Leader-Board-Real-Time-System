from unittest.mock import Mock
import pytest

from controllers.auth import (
    hash_password,
)
from models.request import LoginRequest, RegisterRequest
from models.tables import User


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
def mock_user():
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = hash_password("SecurePass123")
    user.user_code = "test-uuid-123"
    return user
