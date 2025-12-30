from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

from app.settings import settings   # ← USE NEW SETTINGS


SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ========= DB DEPENDENCY =========
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.exception(f"database session error: {e}")
        raise
    finally:
        db.close()
