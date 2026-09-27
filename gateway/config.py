"""Universal API Gateway Configuration.

Supports:
- Gemini (Native Google GenAI)
- OpenRouter (Universal single API key for 200+ models)
- Groq / Nebius / Together / DeepSeek (OpenAI-compatible)
- Local Ollama / vLLM
"""

import os
from pathlib import Path
from typing import Dict, Any, List

# Ensure .env is loaded
def load_env():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

class GatewayConfig:
    # Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    UNIVERSAL_API_KEY = os.getenv("UNIVERSAL_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Base URLs
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1")
    LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
    LOCAL_VLLM_URL = os.getenv("LOCAL_VLLM_URL", "http://localhost:8000/v1")
    LOCAL_MODEL = os.getenv("LOCAL_MODEL", "D:/RAD/model optimizer/quantized_models/MiniCPM5-2B-FP8")

    # Routing
    PREFERRED_PROVIDER = os.getenv("PREFERRED_PROVIDER")

    # Default Models
    DEFAULT_GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-3.8-flash")
    DEFAULT_UNIVERSAL_MODEL = os.getenv("DEFAULT_UNIVERSAL_MODEL", "nvidia/nemotron-3.5-lightning:free")
    DEFAULT_GROQ_MODEL = os.getenv("DEFAULT_GROQ_MODEL", "llama-3.3-70b-versatile")

gateway_config = GatewayConfig()
