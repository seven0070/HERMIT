"""Multi-provider adapters for Universal API Gateway."""

import time
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from gateway.config import gateway_config

@dataclass
class GatewayResponse:
    text: str
    provider: str
    model: str
    latency_ms: float
    usage: Optional[Dict[str, Any]] = None

class BaseProvider:
    name: str

    def is_available(self) -> bool:
        raise NotImplementedError

    async def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> GatewayResponse:
        raise NotImplementedError

class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or gateway_config.GEMINI_API_KEY
        self.model = model or gateway_config.DEFAULT_GEMINI_MODEL
        self._client = None

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if not self._client:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> GatewayResponse:
        client = self._get_client()
        start = time.perf_counter()
        
        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
            
        # Use asyncio executor since google-genai client generate_content is synchronous
        import asyncio
        loop = asyncio.get_running_loop()
        
        history = kwargs.get("history") or []
        contents = []
        for msg in history[-40:]:
            role = "model" if msg.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        def _call():
            return client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config_kwargs if config_kwargs else None
            )
            
        response = await loop.run_in_executor(None, _call)
        latency = (time.perf_counter() - start) * 1000
        
        return GatewayResponse(
            text=response.text or "",
            provider=self.name,
            model=self.model,
            latency_ms=round(latency, 2)
        )

class OpenAICompatibleProvider(BaseProvider):
    """Universal provider for OpenRouter, Groq, Nebius, Together, Ollama, etc."""

    def __init__(self, name: str, base_url: str, api_key: Optional[str], default_model: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> GatewayResponse:
        start = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # OpenRouter optional ranking headers
        if "openrouter" in self.base_url.lower():
            headers["HTTP-Referer"] = "https://github.com/seven0070/HERMIT"
            headers["X-Title"] = "Hermit Agent"

        messages: List[Dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        history = kwargs.get("history") or []
        messages.extend(history[-40:])
        messages.append({"role": "user", "content": prompt})

        model = kwargs.get("model") or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 800),
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - start) * 1000
        choice = data["choices"][0]
        msg = choice.get("message", {})
        reply_text = msg.get("content") or msg.get("reasoning_content") or ""

        return GatewayResponse(
            text=reply_text,
            provider=self.name,
            model=model,
            latency_ms=round(latency, 2),
            usage=data.get("usage")
        )


class LocalMiniCPMProvider(OpenAICompatibleProvider):
    """Local vLLM-served MiniCPM5-2B-FP8 — health-checked before routing."""

    def __init__(self):
        super().__init__(
            name="local_minicpm",
            base_url=gateway_config.LOCAL_VLLM_URL,
            api_key="",
            default_model=gateway_config.LOCAL_MODEL,
        )

    def is_available(self) -> bool:
        """True only if a real OpenAI-compatible server (vLLM) answers /models.

        A raw socket check false-positives on ANY service bound to the port
        (including this project's own web UI when it shares the port).
        """
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(f"{self.base_url}/models")
                return resp.status_code == 200
        except Exception:
            return False
