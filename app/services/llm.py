from abc import ABC, abstractmethod

from openai import OpenAI

from app.config import settings

import openai


class LLMService(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        instructions: str | None = None
    ) -> str:
        pass


class OpenAILLMService(LLMService):
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=30.0
        )

    def generate(
        self,
        prompt: str,
        instructions: str | None = None
    ) -> str:
        request = {
            "model": settings.openai_model,
            "input": prompt
        }

        if instructions is not None:
            request["instructions"] = instructions


        try:
            response = self.client.responses.create(**request)

        except (
            openai.APITimeoutError,
            openai.APIConnectionError,
            openai.RateLimitError,
            openai.APIStatusError
        ) as exc:
            raise LLMServiceError(
                "LLM provider request failed"
            ) from exc

        return response.output_text


llm_service = OpenAILLMService()


class LLMServiceError(Exception):
    pass

