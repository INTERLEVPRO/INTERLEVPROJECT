import os
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local SQLite for testing without Docker/Postgres
    if os.getenv("VERCEL"):
        runtime_dir = Path(tempfile.gettempdir()) / "interlev-agent"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        DATABASE_URL = f"sqlite:///{runtime_dir / 'interlev.db'}"
    else:
        DATABASE_URL = "sqlite:///./interlev.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
