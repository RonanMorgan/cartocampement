from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session # Added Session for type hint
import os # For environment variable

# Default database URL
DATABASE_URL_DEFAULT = "sqlite:///./sql_app.db"
# Get database URL from environment variable or use default
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", DATABASE_URL_DEFAULT)

# Determine connect_args based on whether the DB is SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session - this will be overridden in tests
def get_db() -> Session: # Changed type hint to Session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
