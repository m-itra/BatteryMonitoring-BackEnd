from dotenv import load_dotenv
from pathlib import Path

import os

BASE_DIR = Path(__file__).resolve().parent        # app/
PROJECT_DIR = BASE_DIR.parent                     # project/
PARENT_DIR = PROJECT_DIR.parent                   # уровень выше project

ENV_PATH = PARENT_DIR / "infrastructure" / ".env"
load_dotenv(ENV_PATH)

BATTERY_DATABASE_URL = os.getenv("BATTERY_DATABASE_URL")