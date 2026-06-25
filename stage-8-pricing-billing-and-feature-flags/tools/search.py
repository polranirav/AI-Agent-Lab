# Simulated web search — returns fake but realistic results for learning
SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for information on a topic. "
            "Returns a list of relevant result summaries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max number of results to return (1-5)",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    }
}

_FAKE_RESULTS = {
    "ai agents": [
        "AI agents are systems that can perceive their environment, reason about it, and take actions.",
        "Modern AI agents combine LLMs with tool use, memory, and planning capabilities.",
        "Multi-agent systems coordinate multiple specialized agents for complex tasks.",
    ],
    "python programming": [
        "Python is a high-level, interpreted programming language known for readability.",
        "Python 3.12 introduced significant performance improvements over prior versions.",
        "Python's ecosystem includes over 400,000 packages on PyPI.",
    ],
    "content creation": [
        "Content creators spend an average of 6-8 hours repurposing a single video.",
        "Multi-platform content requires adapting tone, format, and length per channel.",
        "AI tools are reducing content repurposing time by 60-80% for early adopters.",
    ],
}

def run(query: str, max_results: int = 3) -> str:
    """Execute the web search tool."""
    key = query.lower()
    for k, results in _FAKE_RESULTS.items():
        if k in key:
            top = results[:max_results]
            return "\n".join(f"- {r}" for r in top)
    return f"No results found for '{query}'. Try a broader query."