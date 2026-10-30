# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Database Connection & Engine Configuration
Manages SQLAlchemy engine, session factory, connection pooling, and safe error masking.
"""

import os
import re
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("signalsafe.database")

# Environment resolution
DATABASE_URL = os.getenv(
    "SIGNALSAFE_DATABASE_URL",
    f"postgresql://{os.getenv('SIGNALSAFE_DB_USER', 'signalsafe_user')}:"
    f"{os.getenv('SIGNALSAFE_DB_PASSWORD', 'signalsafe_secure_pass_2026')}@"
    f"{os.getenv('SIGNALSAFE_DB_HOST', '127.0.0.1')}:"
    f"{os.getenv('SIGNALSAFE_DB_PORT', '5434')}/"
    f"{os.getenv('SIGNALSAFE_DB_NAME', 'signalsafe_db')}"
)

# Pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

# Connection arguments
connect_args = {
    "connect_timeout": 10,
}

# SQLAlchemy Engine
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,  # Test connections before checkout
        connect_args=connect_args,
    )
except Exception as exc:
    # Mask credentials in log
    safe_err = re.sub(r"://([^:]+):([^@]+)@", r"://\1:******@", str(exc))
    logger.error("Failed to initialize SQLAlchemy engine: %s", safe_err)
    raise

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()


def get_db() -> Generator:
    """
    FastAPI dependency yielding a transactional database session.
    Automatically closes session on completion.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as exc:
        db.rollback()
        safe_msg = re.sub(r"://([^:]+):([^@]+)@", r"://\1:******@", str(exc))
        logger.error("Database transaction rolled back due to error: %s", safe_msg)
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Health check probe executing a lightweight query to verify connectivity.
    Returns True if healthy, False if down. Never exposes credentials.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        safe_err = re.sub(r"://([^:]+):([^@]+)@", r"://\1:******@", str(exc))
        logger.warning("Database connectivity check failed: %s", safe_err)
        return False
