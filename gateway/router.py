"""Universal Model Router with Zero-Downtime Auto-Failover."""

import logging
from typing import List, Optional, Dict, Any
from gateway.config import gateway_config
from gateway.providers import (
    BaseProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    LocalMiniCPMProvider,
    GatewayResponse
)

logger = logging.getLogger("UniversalGateway")

class UniversalGateway:
    """Intelligent API Gateway that routes requests across multiple model providers

    with automatic fallback when credits are depleted (402), rates are exceeded (429),
    or services have downtime (503).
    """

    def __init__(self):
        self.providers: List[BaseProvider] = []
        self._initialize_providers()

    def _initialize_providers(self):
        # 0. Local MiniCPM5-2B-FP8 (Hermit base model — free, private, first in chain)
        self.providers.append(LocalMiniCPMProvider())

        # 1. Universal API Key (OpenRouter - connects to 200+ models with 1 key)
        if gateway_config.UNIVERSAL_API_KEY:
            self.providers.append(
                OpenAICompatibleProvider(
                    name="universal_openrouter",
                    base_url=gateway_config.OPENROUTER_BASE_URL,
                    api_key=gateway_config.UNIVERSAL_API_KEY,
                    default_model=gateway_config.DEFAULT_UNIVERSAL_MODEL
                )
            )

        # 2. Native Gemini
        if gateway_config.GEMINI_API_KEY:
            self.providers.append(GeminiProvider())

        # 3. Groq (High-speed free/cheap tier)
        if gateway_config.GROQ_API_KEY:
            self.providers.append(
                OpenAICompatibleProvider(
                    name="groq",
                    base_url=gateway_config.GROQ_BASE_URL,
                    api_key=gateway_config.GROQ_API_KEY,
                    default_model=gateway_config.DEFAULT_GROQ_MODEL
                )
            )

        # 4. Nebius Token Factory
        if gateway_config.NEBIUS_API_KEY:
            self.providers.append(
                OpenAICompatibleProvider(
                    name="nebius",
                    base_url=gateway_config.NEBIUS_BASE_URL,
                    api_key=gateway_config.NEBIUS_API_KEY,
                    default_model="meta-llama/Meta-Llama-3.1-70B-Instruct"
                )
            )

    def get_active_providers(self) -> List[str]:
        return [p.name for p in self.providers if p.is_available()]

    async def complete(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> GatewayResponse:
        """Executes a completion with automatic multi-provider fallback.
        
        If a provider fails due to credit exhaustion (402), rate limits (429),
        or high demand (503), it immediately tries the next provider in the chain.
        """
        preferred_provider = preferred_provider or gateway_config.PREFERRED_PROVIDER
        available = [p for p in self.providers if p.is_available()]
        if not available:
            raise RuntimeError(
                "No API providers are available. Please configure at least one API key "
                "in .env (e.g. GEMINI_API_KEY, UNIVERSAL_API_KEY, or GROQ_API_KEY)."
            )

        # Re-order if preferred provider specified
        if preferred_provider:
            available.sort(key=lambda p: 0 if p.name == preferred_provider else 1)

        errors = []
        for provider in available:
            try:
                # Attempt call
                response = await provider.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    **kwargs
                )
                return response
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Provider '{provider.name}' failed: {err_msg}. Triggering failover...")
                errors.append(f"[{provider.name}]: {err_msg}")
                # Continue loop to next fallback provider

        raise RuntimeError(
            f"All providers in the Universal Gateway chain failed.\nFailures:\n" + "\n".join(errors)
        )

# Global singleton
gateway = UniversalGateway()
