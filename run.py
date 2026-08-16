"""Start the Veeza AI app (serves API + frontend)."""

import os

import uvicorn

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
