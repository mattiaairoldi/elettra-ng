from django.conf import settings

from .base import AiProviderError
from .local import LocalAiProvider
from .openai import OpenAIAiProvider


AI_PROVIDER_REGISTRY = {
    LocalAiProvider.provider_name: LocalAiProvider,
    OpenAIAiProvider.provider_name: OpenAIAiProvider,
}


def register_ai_provider(name, provider_class):
    AI_PROVIDER_REGISTRY[name] = provider_class


def get_ai_provider(provider_name=None):
    selected_provider = provider_name or getattr(settings, "AI_PROVIDER", "local")
    provider_class = AI_PROVIDER_REGISTRY.get(selected_provider)
    if provider_class is None:
        supported = ", ".join(sorted(AI_PROVIDER_REGISTRY))
        raise AiProviderError(f"Unsupported AI provider: {selected_provider}. Supported providers: {supported}")
    return provider_class()
