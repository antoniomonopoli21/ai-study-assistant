from abc import ABC, abstractmethod

from openai import OpenAI

from app.config import settings


class LLMService(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass


class OpenAILLMService(LLMService):
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=settings.openai_model,
            input=prompt
        )

        return response.output_text


llm_service = OpenAILLMService()