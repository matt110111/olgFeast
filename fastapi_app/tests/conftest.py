"""
Pytest configuration and fixtures for FastAPI tests
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.menu import FoodItem

# Test database URL (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_staff=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_staff_user(db_session):
    """Create a test staff user."""
    user = User(
        username="teststaff",
        email="staff@example.com",
        hashed_password=get_password_hash("staffpass123"),
        is_active=True,
        is_staff=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_food_items(db_session):
    """Create test food items."""
    items = [
        FoodItem(
            food_group="Appetizers",
            name="Test Wings",
            value=12.99,
            ticket=1
        ),
        FoodItem(
            food_group="Main Course",
            name="Test Burger",
            value=18.99,
            ticket=2
        ),
        FoodItem(
            food_group="Desserts",
            name="Test Cake",
            value=7.99,
            ticket=1
        )
    ]
    
    for item in items:
        db_session.add(item)
    
    db_session.commit()
    
    for item in items:
        db_session.refresh(item)
    
    return items


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_auth_headers(client, test_staff_user):
    """Get authentication headers for test staff user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "teststaff", "password": "staffpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
