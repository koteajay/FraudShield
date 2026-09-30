"""SQLAlchemy SQLite database setup and session management."""

from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import get_settings
from app.logging_config import logger

settings = get_settings()

# Prepare SQLite connection arguments
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

    # Ensure parent directory for sqlite file exists if path is specified
    db_file_part = settings.DATABASE_URL.replace("sqlite:///", "")
    if db_file_part and db_file_part != ":memory:":
        db_path = Path(db_file_part).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> bool:
    """Lightweight check verifying database connectivity."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return False


def init_db() -> None:
    """
    Safely initialize database tables and connection.
    This function is non-destructive: it only creates tables defined in Base metadata
    that do not already exist, and never drops or resets existing data.
    """
    try:
        # Import models so they are registered on Base.metadata
        import app.models  # noqa: F401

        # Create non-existent tables if any models are defined
        Base.metadata.create_all(bind=engine)

        # Ensure schema updates for existing SQLite tables (non-destructive)
        try:
            with engine.begin() as connection:
                cols_result = connection.execute(text("PRAGMA table_info(devices)")).fetchall()
                existing_cols = {row[1] for row in cols_result}
                if existing_cols:
                    if "device_id" not in existing_cols:
                        connection.execute(text("ALTER TABLE devices ADD COLUMN device_id VARCHAR(128)"))
                        connection.execute(text("UPDATE devices SET device_id = fingerprint WHERE device_id IS NULL"))
                    if "updated_at" not in existing_cols:
                        connection.execute(text("ALTER TABLE devices ADD COLUMN updated_at DATETIME"))

                # Check reviews table
                review_cols_result = connection.execute(text("PRAGMA table_info(reviews)")).fetchall()
                existing_review_cols = {row[1] for row in review_cols_result}
                if existing_review_cols:
                    if "reviewer_id" not in existing_review_cols:
                        connection.execute(text("ALTER TABLE reviews ADD COLUMN reviewer_id VARCHAR(64)"))
                    if "previous_status" not in existing_review_cols:
                        connection.execute(text("ALTER TABLE reviews ADD COLUMN previous_status VARCHAR(32)"))
                    if "new_status" not in existing_review_cols:
                        connection.execute(text("ALTER TABLE reviews ADD COLUMN new_status VARCHAR(32)"))
                    if "note" not in existing_review_cols:
                        connection.execute(text("ALTER TABLE reviews ADD COLUMN note TEXT"))
        except Exception as mig_err:
            logger.debug(f"Schema upgrade check note: {mig_err}")

        # Verify connectivity
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Database connection initialized successfully")
    except Exception as exc:
        logger.error(f"Failed to initialize database: {exc}")
        raise

