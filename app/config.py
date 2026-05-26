import logging
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY")
if GEMINI_API_KEY:
    os.environ.setdefault("GOOGLE_API_KEY", GEMINI_API_KEY)
else:
    raise RuntimeError(
        "Gemini API key not found. Set GEMINI_API_KEY in .env or export GOOGLE_API_KEY."
    )

GEMINI_MODEL = (
    os.getenv("GEMINI_MODEL")
    or os.getenv("GOOGLE_MODEL")
    or "google:gemini-3.1-flash-lite"
)

LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("auto_mate")
