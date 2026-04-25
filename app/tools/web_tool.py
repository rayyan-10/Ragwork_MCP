import httpx

async def web_search(query: str) -> str:
    """
    Searches the web using DuckDuckGo Instant Answer API.
    Returns top results as a readable string.
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            data = response.json()

        results = []

        if data.get("AbstractText"):
            results.append(data["AbstractText"])

        if data.get("RelatedTopics"):
            for topic in data["RelatedTopics"]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append(topic["Text"])
                elif isinstance(topic, dict) and "Topics" in topic:
                    for sub in topic["Topics"]:
                        if "Text" in sub:
                            results.append(sub["Text"])

        if results:
            return " ".join(results[:3])

        return f"No direct results found for '{query}'. Try refining the query."

    except Exception as e:
        return f"Web search error: {str(e)}"
