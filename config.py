"""Central configuration for PocketSmart AI.

All settings come from environment variables (loaded from `.env` when present),
so no secret ever lives in the source code.
"""
import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger("pocketsmart.config")

# --- Security / sessions -----------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # A random per-process key is safe; it only logs users out on restart.
    SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning("SECRET_KEY not set - using a temporary random key for this run.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SESSION_IDLE_SECONDS = 30 * 60
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

# --- Gemini ------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# Tried in order when the primary model is retired / unavailable (HTTP 404/429/5xx).
GEMINI_FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "25"))
GEMINI_TOTAL_BUDGET_SECONDS = int(os.getenv("GEMINI_TOTAL_BUDGET_SECONDS", "60"))

# --- Storage -----------------------------------------------------------------
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "pocketsmart.db"))
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
