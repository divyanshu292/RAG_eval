from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.
Use ONLY the information from the context to answer. If the context doesn't contain enough information, say so clearly.
Do not make up information that is not in the context."""


async def generate_answer(question: str, chunks: list[dict]) -> str:
    context = "\n\n---\n\n".join(
        f"[Source: {c.get('metadata', {}).get('source_filename', 'unknown')}, "
        f"Chunk {c.get('chunk_index', '?')}]\n{c['text']}"
        for c in chunks
    )

    response = await client.chat.completions.create(
        model=settings.generation_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        temperature=0.2,
        max_completion_tokens=1024,
    )
    return response.choices[0].message.content
