from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    response = await client.embeddings.create(
        input=texts,
        model=settings.embedding_model,
    )
    return [item.embedding for item in response.data]


async def embed_query(text: str) -> list[float]:
    result = await embed_texts([text])
    return result[0]
