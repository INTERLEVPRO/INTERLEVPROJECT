import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "INTERLEV AI Freelancer Matching Agent"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Placeholder for DB settings later
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./interlev.db")

settings = Settings()
