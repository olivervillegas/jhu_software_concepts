import os

def get_database_url() -> str:
    """Return DATABASE_URL (required in CI)."""
    url = os.getenv("DATABASE_URL")
    if not url:
        # Local convenience default (still works in tests if you set DATABASE_URL)
        return "postgresql://postgres:postgres@localhost:5432/postgres"
    return url

class Config:
    TESTING = False
    DATABASE_URL = get_database_url()
