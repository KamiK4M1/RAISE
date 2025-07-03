import pytest
import asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator

from app.main import app
from app.config import settings
from app.core.database import DatabaseManager
from app.core.dependencies import get_db

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a new event loop for the test session.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def test_db() -> AsyncGenerator[None, None]:
    """
    Fixture to set up and tear down a test database.
    This fixture is automatically used for the entire test session.
    """
    # Initialize the database manager with the test database name
    test_db_manager = DatabaseManager(settings.MONGODB_URL, settings.MONGODB_DB_NAME_TEST)
    await test_db_manager.connect()

    # Define an override for the get_db dependency
    async def override_get_db():
        return test_db_manager.db

    # Apply the override to the FastAPI app
    app.dependency_overrides[get_db] = override_get_db

    yield

    # Teardown: drop the test database after all tests are done
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await client.drop_database(settings.MONGODB_DB_NAME_TEST)
    await test_db_manager.disconnect()
    # Clear the dependency override
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an asynchronous test client for making requests to the app.
    """
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest.fixture(scope="module")
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """
    Provides a client that is pre-authenticated.
    This is useful for testing protected endpoints.
    """
    email = "authtest@example.com"
    password = "password123"
    
    # Register a new user for the test module
    await client.post("/auth/register", json={"email": email, "password": password})
    
    # Log in to get an access token
    login_response = await client.post("/auth/token", data={"username": email, "password": password})
    token = login_response.json()["access_token"]
    
    # Set the authorization header for subsequent requests
    client.headers = {"Authorization": f"Bearer {token}"}
    
    return client
