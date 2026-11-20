import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn
from backend.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    print("=" * 60)
    print("Starting AquaGuard Water Surface Pollution Detection Server")
    print(f"Local URL: http://localhost:{PORT}")
    print(f"Host: {HOST}:{PORT} (Debug={DEBUG})")
    print("=" * 60)
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=DEBUG)

