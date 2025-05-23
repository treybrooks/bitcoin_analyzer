#!/usr/bin/env python3
import uvicorn
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bitcoin_analyzer.web.app import app

def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "bitcoin_analyzer.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes during development
    )

if __name__ == "__main__":
    main()