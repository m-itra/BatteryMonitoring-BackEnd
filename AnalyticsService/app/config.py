from pathlib import Path
from dotenv import load_dotenv

import os

BASE_DIR = Path(__file__).resolve().parent        # app/
PROJECT_DIR = BASE_DIR.parent                     # project/
PARENT_DIR = PROJECT_DIR.parent                   # уровень выше project

ENV_PATH = PARENT_DIR / "infrastructure" / ".env"
load_dotenv(ENV_PATH)

BATTERY_DATABASE_URL = os.getenv("BATTERY_DATABASE_URL")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
USER_SERVICE_GRPC_URL = os.getenv("USER_SERVICE_GRPC_URL")