SCHEMA = {
    "type": "function",
    "function": {
        "name": "word_count",
        "description": "Counts the number of words and characters in a given text.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to analyze"
                }
            },
            "required": ["text"]
        }
    }
}


def run(text: str) -> str:
    """Execute the word count tool."""
    words = len(text.split())
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))
    return (
        f"Words: {words} | "
        f"Characters (with spaces): {chars} | "
        f"Characters (no spaces): {chars_no_space}"
    )
