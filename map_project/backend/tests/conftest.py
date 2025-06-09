import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool # To ensure single connection for in-memory SQLite
import os

# Import base for table creation, and the app an get_db for overriding
from app.main import app
from app.database import Base, get_db # The get_db from app.database

# --- Test Database Setup ---
#SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:" # In-memory SQLite
# For file-based test DB:
TEST_DB_FILE = "./test.db"
SQLALCHEMY_DATABASE_URL_TEST = f"sqlite:///{TEST_DB_FILE}"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    # connect_args is critical for in-memory SQLite to work with multiple threads/accesses in tests
    # For file-based, it's less critical but good practice.
    connect_args={"check_same_thread": False},
    # For in-memory only, StaticPool can be useful:
    # poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db_session_wide():
    # Remove old test DB file if it exists before starting session
    if SQLALCHEMY_DATABASE_URL_TEST.startswith("sqlite:///") and os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    Base.metadata.create_all(bind=engine_test) # Create tables
    yield
    # Teardown: Remove test DB file after session, uncomment if needed
    # if SQLALCHEMY_DATABASE_URL_TEST.startswith("sqlite:///") and os.path.exists(TEST_DB_FILE):
    #     os.remove(TEST_DB_FILE)


@pytest.fixture(scope="function")
def db_session_test() -> Session: # Type hint for clarity
    """
    Creates a new database session for a test, with transaction rollback.
    """
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback() # Rollback any changes made during the test
    connection.close()


@pytest.fixture(scope="function")
def client(db_session_test: Session) -> TestClient: # Type hint for clarity
    """
    Provides a TestClient with the get_db dependency overridden.
    Ensures each test gets a fresh DB state due to rollback.
    """
    def override_get_db():
        try:
            yield db_session_test
        finally:
            # The session is managed by db_session_test fixture (closed, rolled back there)
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    del app.dependency_overrides[get_db] # Clean up/restore original dependency
