"""Load .env before any other module imports.

This module MUST be imported first in app/__init__.py to ensure
environment variables are available for all submodules during import.
"""

from pathlib import Path

from dotenv import load_dotenv

# Find .env in project root (parent of app/)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)
