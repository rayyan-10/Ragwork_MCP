from app.tools.llm_tool import generate_response

async def summarize(text: str) -> str:
    """
    Summarizes text into 2-3 concise sentences.
    For very long text, truncates to avoid token limits.
    """
    # Truncate to avoid exceeding LLM context
    if len(text) > 4000:
        text = text[:4000] + "..."

    prompt = f"""Summarize the following text in 2-3 clear, concise sentences.
Focus only on the key points. Do not add any introduction like "Here is a summary".
Just output the summary directly.

Text:
{text}

Summary:"""

    return await generate_response(prompt)
