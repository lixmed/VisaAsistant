import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
MAX_AGENT_STEPS = 14
MAX_TOOLS_PER_TURN = 5
REQUEST_TIMEOUT = 15
KNOWLEDGE_FILE = str(BASE_DIR / "data" / "visa_programs.json")
