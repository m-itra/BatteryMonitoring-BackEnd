from pathlib import Path
from dotenv import load_dotenv

import os

BASE_DIR = Path(__file__).resolve().parent        # app/
PROJECT_DIR = BASE_DIR.parent                     # project/
PARENT_DIR = PROJECT_DIR.parent                   # уровень выше project

ENV_PATH = PARENT_DIR / "infrastructure" / ".env"
load_dotenv(ENV_PATH)

USER_DATABASE_URL = os.getenv("USER_DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS"))
USER_SERVICE_GRPC_URL = os.getenv("USER_SERVICE_GRPC_URL")
