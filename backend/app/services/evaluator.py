import json

from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def _llm_judge(prompt: str) -> float:
    response = await client.chat.completions.create(
        model=settings.evaluation_model,
        messages=[
            {
                "role": "system",
                "content": "You are an evaluation judge. Respond ONLY with a JSON object containing a single 'score' field with a float between 0.0 and 1.0.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_completion_tokens=64,
    )
    text = response.choices[0].message.content.strip()
    try:
        return float(json.loads(text)["score"])
    except (json.JSONDecodeError, KeyError, ValueError):
        # Fallback: try to extract a number
        for token in text.split():
            try:
                val = float(token.strip(",."))
                if 0.0 <= val <= 1.0:
                    return val
            except ValueError:
                continue
        return 0.5


async def evaluate_retrieval_relevance(question: str, chunks: list[dict]) -> float:
    chunk_texts = "\n\n".join(
        f"Chunk {i+1}: {c['text']}" for i, c in enumerate(chunks)
    )
    prompt = (
        f"Question: {question}\n\n"
        f"Retrieved chunks:\n{chunk_texts}\n\n"
        "Rate how relevant the retrieved chunks are to answering the question. "
        "Score 1.0 if all chunks are highly relevant, 0.0 if none are relevant. "
        "Respond with JSON: {{\"score\": <float>}}"
    )
    return await _llm_judge(prompt)


async def evaluate_answer_faithfulness(answer: str, chunks: list[dict]) -> float:
    chunk_texts = "\n\n".join(
        f"Chunk {i+1}: {c['text']}" for i, c in enumerate(chunks)
    )
    prompt = (
        f"Source chunks:\n{chunk_texts}\n\n"
        f"Answer: {answer}\n\n"
        "What fraction of claims in the answer are supported by the source chunks? "
        "Score 1.0 if fully faithful, 0.0 if entirely unsupported. "
        "Respond with JSON: {{\"score\": <float>}}"
    )
    return await _llm_judge(prompt)


async def evaluate_hallucination(answer: str, chunks: list[dict]) -> float:
    chunk_texts = "\n\n".join(
        f"Chunk {i+1}: {c['text']}" for i, c in enumerate(chunks)
    )
    prompt = (
        f"Source chunks:\n{chunk_texts}\n\n"
        f"Answer: {answer}\n\n"
        "Identify claims in the answer not supported by the sources. "
        "What fraction of the answer is unsupported? "
        "Score 0.0 if nothing is hallucinated, 1.0 if everything is hallucinated. "
        "Respond with JSON: {{\"score\": <float>}}"
    )
    return await _llm_judge(prompt)


async def evaluate_query(question: str, answer: str, chunks: list[dict]) -> dict:
    import asyncio

    relevance, faithfulness, hallucination = await asyncio.gather(
        evaluate_retrieval_relevance(question, chunks),
        evaluate_answer_faithfulness(answer, chunks),
        evaluate_hallucination(answer, chunks),
    )
    return {
        "retrieval_relevance": round(relevance, 3),
        "answer_faithfulness": round(faithfulness, 3),
        "hallucination_score": round(hallucination, 3),
    }
