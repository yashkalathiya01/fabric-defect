"""
Fabric AI Inspection System - Database Configuration & Session
==============================================================

Manages database engine, session lifecycle, and automatic table creation.
Supports PostgreSQL (production) with SQLite fallback for local development.

Configurable via environment variable:
    DATABASE_URL="postgresql://user:password@localhost:5432/fabric_inspection"
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database.models import Base

logger = logging.getLogger(__name__)

# Default to local SQLite database in backend directory if PostgreSQL is not specified
DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fabric_inspection.db")
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"

DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

# Configure engine
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database engine initialized with: %s", "SQLite" if is_sqlite else "PostgreSQL")
except Exception as e:
    logger.warning("Failed to initialize primary database (%s). Falling back to SQLite.", e)
    engine = create_engine(f"sqlite:///{DEFAULT_SQLITE_PATH}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error("Failed to create database tables: %s", e)


def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
