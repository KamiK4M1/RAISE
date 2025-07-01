# Testing Setup Guide for RAISE

This guide provides comprehensive instructions for setting up testing frameworks for both the backend (FastAPI) and frontend (Next.js) components of the RAISE application.

## Backend Testing with Pytest

### 1. Installation

Add the following testing dependencies to your `requirements.txt`:

```text
# Testing Dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
pytest-cov>=4.1.0
httpx>=0.24.0  # For async HTTP client testing
factories-boy>=3.2.0  # For test data factories
freezegun>=1.2.0  # For time-based testing
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Project Structure

Create the following testing structure:

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration and fixtures
│   ├── test_auth.py          # Authentication tests
│   ├── test_documents.py     # Document handling tests
│   ├── test_flashcards.py    # Flashcard functionality tests
│   ├── test_quiz.py          # Quiz system tests
│   ├── test_vector_store.py  # Vector store tests
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_services/    # Service layer tests
│   │   └── test_models/      # Model validation tests
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_api/         # API integration tests
│   └── factories/
│       ├── __init__.py
│       └── test_factories.py # Test data factories
```

### 3. Configuration Files

#### `backend/tests/conftest.py`

```python
import pytest
import asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.config import settings
from app.core.database import db_manager

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["MONGODB_DB_NAME"] = "raise_test_db"
os.environ["DEBUG"] = "true"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database connection."""
    # Use a separate test database
    test_client = AsyncIOMotorClient(settings.mongodb_uri)
    test_db = test_client[f"{settings.database_name}_test"]
    
    yield test_db
    
    # Cleanup: Drop test database after all tests
    await test_client.drop_database(f"{settings.database_name}_test")
    test_client.close()

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user) -> AsyncClient:
    """Create authenticated test client."""
    login_response = await client.post(
        "/api/auth/login",
        json={"email": test_user["email"], "password": "testpassword123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client

@pytest.fixture
async def test_user(test_db):
    """Create test user."""
    from app.core.auth import get_password_hash
    
    user_data = {
        "email": "test@example.com",
        "password": get_password_hash("testpassword123"),
        "name": "Test User",
        "created_at": datetime.utcnow()
    }
    
    users_collection = test_db["users"]
    result = await users_collection.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    
    yield user_data
    
    # Cleanup
    await users_collection.delete_one({"_id": result.inserted_id})
```

#### `backend/tests/factories/test_factories.py`

```python
import factory
from datetime import datetime
from bson import ObjectId

class UserFactory(factory.Factory):
    class Meta:
        model = dict
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    password = "hashed_password_here"
    created_at = factory.LazyFunction(datetime.utcnow)

class DocumentFactory(factory.Factory):
    class Meta:
        model = dict
    
    title = factory.Faker("sentence", nb_words=4)
    content = factory.Faker("text", max_nb_chars=2000)
    file_type = "pdf"
    file_size = factory.Faker("random_int", min=1000, max=10000000)
    status = "completed"
    created_at = factory.LazyFunction(datetime.utcnow)
    user_id = factory.LazyFunction(lambda: ObjectId())

class FlashcardFactory(factory.Factory):
    class Meta:
        model = dict
    
    question = factory.Faker("sentence", nb_words=8, variable_nb_words=True)
    answer = factory.Faker("text", max_nb_chars=500)
    difficulty = factory.Faker("random_element", elements=("easy", "medium", "hard"))
    document_id = factory.LazyFunction(lambda: ObjectId())
    user_id = factory.LazyFunction(lambda: ObjectId())
    created_at = factory.LazyFunction(datetime.utcnow)
```

### 4. Example Test Files

#### `backend/tests/test_auth.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "name": "New User"
    }
    
    response = await client.post("/api/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == user_data["email"]

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, test_user):
    """Test user login."""
    login_data = {
        "email": test_user["email"],
        "password": "testpassword123"
    }
    
    response = await client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client: AsyncClient):
    """Test that protected endpoints require authentication."""
    response = await client.get("/api/documents")
    assert response.status_code == 401
```

#### `backend/tests/test_vector_store.py`

```python
import pytest
import numpy as np
from app.core.vector_store import VectorStore, SimilarityMetric

@pytest.mark.asyncio
async def test_vector_store_initialization():
    """Test vector store initialization."""
    vector_store = VectorStore(embedding_dimension=1024)
    await vector_store.initialize()
    
    assert vector_store._initialized is True
    assert vector_store.embedding_dimension == 1024

@pytest.mark.asyncio
async def test_store_and_search_vectors():
    """Test storing and searching vectors."""
    vector_store = VectorStore(embedding_dimension=128)  # Smaller for testing
    await vector_store.initialize()
    
    # Create test vectors
    test_vectors = [
        {
            "document_id": "doc1",
            "user_id": "user1",
            "text": "This is a test document about AI",
            "embedding": np.random.rand(128).tolist(),
            "metadata": {"type": "test"}
        }
    ]
    
    # Store vectors
    vector_ids = await vector_store.store_vectors(test_vectors)
    assert len(vector_ids) == 1
    
    # Search for similar vectors
    query_embedding = np.random.rand(128).tolist()
    results = await vector_store.similarity_search(
        query_embedding=query_embedding,
        limit=5,
        similarity_threshold=0.0
    )
    
    assert len(results) >= 0  # May or may not find similar vectors
    
    await vector_store.close()
```

### 5. Running Tests

Create a `pytest.ini` configuration file:

```ini
[tool:pytest]
testpaths = tests
asyncio_mode = auto
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --strict-markers
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

Run tests with different options:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## Frontend Testing with Jest and React Testing Library

### 1. Installation

Add testing dependencies to your `package.json`:

```json
{
  "devDependencies": {
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/user-event": "^14.4.3",
    "jest": "^29.5.0",
    "jest-environment-jsdom": "^29.5.0",
    "@types/jest": "^29.5.2",
    "msw": "^1.2.2"
  }
}
```

Install dependencies:
```bash
npm install
```

### 2. Configuration Files

#### `jest.config.js`

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/lib/(.*)$': '<rootDir>/src/lib/$1',
    '^@/types/(.*)$': '<rootDir>/src/types/$1',
    '^@/hooks/(.*)$': '<rootDir>/src/hooks/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/app/layout.tsx',
    '!src/app/globals.css',
  ],
  coverageReporters: ['text', 'lcov', 'html'],
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}',
  ],
}

module.exports = createJestConfig(customJestConfig)
```

#### `jest.setup.js`

```javascript
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      replace: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    }
  },
}))

// Mock Next.js link
jest.mock('next/link', () => {
  return ({ children, href }) => {
    return <a href={href}>{children}</a>
  }
})

// Global test utilities
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))
```

### 3. Test Structure

```
src/
├── __tests__/
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.test.tsx
│   │   │   └── Card.test.tsx
│   │   └── flashcards/
│   │       └── FlashcardPage.test.tsx
│   ├── lib/
│   │   ├── api.test.ts
│   │   └── utils.test.ts
│   ├── hooks/
│   │   └── useApi.test.ts
│   └── mocks/
│       ├── handlers.ts
│       └── server.ts
```

### 4. Example Test Files

#### `src/__tests__/components/ui/Button.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '@/components/ui/button'

describe('Button Component', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('applies correct variant styles', () => {
    render(<Button variant="outline">Outline Button</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('border')
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

#### `src/__tests__/lib/api.test.ts`

```typescript
import { apiService } from '@/lib/api'
import { setupServer } from 'msw/node'
import { rest } from 'msw'

const server = setupServer(
  rest.post('http://localhost:8000/api/auth/login', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        data: {
          access_token: 'fake-token',
          user: { id: '1', email: 'test@example.com' }
        }
      })
    )
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('ApiService', () => {
  beforeEach(() => {
    // Clear any stored tokens
    apiService.setAuthToken(null)
  })

  it('successfully logs in user', async () => {
    const response = await apiService.login('test@example.com', 'password')
    
    expect(response.success).toBe(true)
    expect(response.data.access_token).toBe('fake-token')
    expect(apiService.getAuthToken()).toBe('fake-token')
  })

  it('includes auth token in subsequent requests', async () => {
    server.use(
      rest.get('http://localhost:8000/api/documents', (req, res, ctx) => {
        const authHeader = req.headers.get('Authorization')
        if (authHeader === 'Bearer fake-token') {
          return res(ctx.json({ success: true, data: [] }))
        }
        return res(ctx.status(401))
      })
    )

    apiService.setAuthToken('fake-token')
    const response = await apiService.getDocuments()
    
    expect(response.success).toBe(true)
  })
})
```

### 5. Running Frontend Tests

Add test scripts to `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --watchAll=false"
  }
}
```

Run tests:
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run tests for CI
npm run test:ci
```

## Best Practices

### 1. Test Organization
- Group related tests in describe blocks
- Use descriptive test names that explain what is being tested
- Follow AAA pattern: Arrange, Act, Assert

### 2. Mocking
- Mock external dependencies (APIs, databases)
- Use factories for test data generation
- Mock heavy operations and third-party services

### 3. Coverage Goals
- Aim for 80%+ code coverage
- Focus on critical business logic
- Don't aim for 100% coverage at the expense of test quality

### 4. CI/CD Integration
- Run tests on every commit and pull request
- Fail builds if tests don't pass
- Generate and store coverage reports

### 5. Test Data Management
- Use isolated test databases
- Clean up test data after each test
- Use transactions when possible for faster cleanup

This comprehensive testing setup will help ensure the reliability and maintainability of your RAISE application.