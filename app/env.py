"""Load .env before any other module imports.

This module MUST be imported first in app/__init__.py to ensure
environment variables are available for all submodules during import.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Find .env in project root (parent of app/)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)


def get_database_url() -> str:
    """
    Get database URL from environment variable.
    
    Defaults to PostgreSQL connection for production use.
    Falls back to in-memory SQLite for testing if not set.
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql://techno_user:change_me_in_production@postgres:5432/techno_os"
    )
