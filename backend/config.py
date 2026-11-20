import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Server
PORT = int(os.getenv("PORT", 7860))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Security
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "").strip()
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

# Model configuration
_raw_model_path = os.getenv("MODEL_PATH", str(BASE_DIR / "Models")).strip()
if (BASE_DIR / _raw_model_path).exists():
    MODEL_PATH = str((BASE_DIR / _raw_model_path).resolve())
elif Path(_raw_model_path).exists():
    MODEL_PATH = str(Path(_raw_model_path).resolve())
else:
    MODEL_PATH = _raw_model_path

DEVICE = os.getenv("DEVICE", "auto")

# Detection defaults
DEFAULT_BOX_THRESHOLD = float(os.getenv("DEFAULT_BOX_THRESHOLD", 0.25))
DEFAULT_TEXT_THRESHOLD = float(os.getenv("DEFAULT_TEXT_THRESHOLD", 0.25))

# File and media limits
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", 25))
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", 150))
MAX_VIDEO_DURATION_SEC = int(os.getenv("MAX_VIDEO_DURATION_SEC", 180))

# Video acceleration defaults
VIDEO_DEFAULT_INTERVAL_SEC = float(os.getenv("VIDEO_DEFAULT_INTERVAL_SEC", 2.0)) # 1 frame every 2 seconds
VIDEO_MAX_SAMPLED_FRAMES = int(os.getenv("VIDEO_MAX_SAMPLED_FRAMES", 10))        # Max frames to process
VIDEO_SAMPLE_FPS = float(os.getenv("VIDEO_SAMPLE_FPS", 0.5))                     # Backward-compatible sample fps
VIDEO_INFERENCE_SIZE = {"shortest_edge": 320, "longest_edge": 480}              # Accelerated resolution

# Supported file formats
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mkv"}

# Directories
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Predefined target classes for water pollution detection
TARGET_CLASSES = [
    "plastic bottle",
    "plastic bag",
    "plastic wrapper",
    "floating garbage",
    "fishing net",
    "wood debris",
    "water hyacinth",
    "aquatic weeds",
    "oil spill",
    "surface foam",
    "dead fish",
    "dead animal",
    "ship",
    "sea creature on water surface",
]

# Category groupings for dashboard analysis and UI color tags
CATEGORY_GROUPS = {
    "Plastic & Synthetics": {
        "classes": ["plastic bottle", "plastic bag", "plastic wrapper", "fishing net"],
        "color": "#ef4444",  # Red
        "badge": "bg-red-500/10 text-red-400 border-red-500/20"
    },
    "Organic Debris": {
        "classes": ["wood debris", "water hyacinth", "aquatic weeds"],
        "color": "#10b981",  # Green
        "badge": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    },
    "Chemical & Industrial": {
        "classes": ["oil spill", "surface foam", "floating garbage"],
        "color": "#f59e0b",  # Amber / Orange
        "badge": "bg-amber-500/10 text-amber-400 border-amber-500/20"
    },
    "Biological & Wildlife": {
        "classes": ["dead fish", "dead animal", "sea creature on water surface"],
        "color": "#ec4899",  # Pink / Purple
        "badge": "bg-pink-500/10 text-pink-400 border-pink-500/20"
    },
    "Vessels & Marine Objects": {
        "classes": ["ship"],
        "color": "#3b82f6",  # Blue
        "badge": "bg-blue-500/10 text-blue-400 border-blue-500/20"
    }
}
