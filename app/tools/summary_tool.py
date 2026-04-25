from app.tools.llm_tool import generate_response

async def summarize(text: str):
    prompt = f"""
    Summarize the following text in 2-3 concise sentences.
    Focus only on key points and remove unnecessary details.

    Text:
    {text}

    Summary:
    """
    return await generate_response(prompt)