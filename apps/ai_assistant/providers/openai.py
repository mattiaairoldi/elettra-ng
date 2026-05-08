from django.conf import settings

from .base import AiProviderError, normalize_diagnostic_payload
from .context import build_ai_instructions, build_diagnostic_instructions

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class OpenAIAiProvider:
    provider_name = "openai"

    def __init__(self):
        if OpenAI is None:
            raise AiProviderError("OpenAI SDK is not installed.")

        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise AiProviderError("OPENAI_API_KEY is not configured.")

        client_kwargs = {
            "api_key": api_key,
            "base_url": "https://api.openai.com/v1",
        }
        base_url = getattr(settings, "OPENAI_BASE_URL", "")
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)
        self.model = getattr(settings, "AI_OPENAI_MODEL", "gpt-5.4-mini")

    def build_reply(self, session, messages):
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=build_ai_instructions(session),
                input=messages,
                store=False,
            )
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        reply = getattr(response, "output_text", "") or ""
        reply = reply.strip()
        if not reply:
            raise AiProviderError("OpenAI provider returned an empty response.")
        return reply

    def stream_reply(self, session, messages):
        try:
            stream = self.client.responses.create(
                model=self.model,
                instructions=build_ai_instructions(session),
                input=messages,
                store=False,
                stream=True,
            )
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        emitted = False
        try:
            for event in stream:
                if getattr(event, "type", "") == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        emitted = True
                        yield delta
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        if not emitted:
            raise AiProviderError("OpenAI provider returned an empty response.")

    def build_diagnostic_reply(self, session, messages):
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=build_diagnostic_instructions(session),
                input=messages,
                store=False,
            )
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        reply = getattr(response, "output_text", "") or ""
        if not reply.strip():
            raise AiProviderError("OpenAI provider returned an empty diagnostic response.")
        return normalize_diagnostic_payload(reply)
