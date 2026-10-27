"""Application entrypoint for production and cloud deployments."""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' imports resolve regardless of current working directory
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    # Cloud platforms (Render, Railway, Heroku) inject PORT into the environment
    port = int(os.environ.get("PORT", settings.port))
    host = os.environ.get("HOST", settings.host)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
