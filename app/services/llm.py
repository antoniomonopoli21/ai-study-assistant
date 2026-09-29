from abc import ABC, abstractmethod

from openai import OpenAI

from app.config import settings


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
            api_key=settings.openai_api_key
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

        response = self.client.responses.create(**request)

        return response.output_text


llm_service = OpenAILLMService()