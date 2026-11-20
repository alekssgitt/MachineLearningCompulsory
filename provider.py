from contextlib import asynccontextmanager
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

from config import Settings


@asynccontextmanager
async def open_model(settings: Settings):
    local = "localhost" in settings.base_url or "127.0.0.1" in settings.base_url
    profile = OpenAIModelProfile(
        supports_tools=True,
        supports_json_object_output=True,
        supports_json_schema_output=not local,
    )
    async with AsyncOpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        max_retries=1,
        timeout=settings.timeout,
    ) as client:
        yield OpenAIChatModel(
            settings.model,
            provider=OpenAIProvider(openai_client=client),
            profile=profile,
        )
