import os

def get_database_url() -> str:
    """Return DATABASE_URL (required in CI)."""
    url = os.getenv("DATABASE_URL")
    return url

class Config:
    TESTING = False
    DATABASE_URL = get_database_url()
