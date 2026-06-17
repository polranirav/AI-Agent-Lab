# Simulated weather tool — no real API needed for learning
SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Gets the current weather for a given city. Returns temperature and conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'Toronto' or 'New York'"
                }
            },
            "required": ["city"]
        }
    }
}

# Simulated data — in production, this would call a real weather API
_FAKE_WEATHER = {
    "toronto":   {"temp_c": 22, "condition": "Partly cloudy"},
    "new york":  {"temp_c": 28, "condition": "Sunny"},
    "london":    {"temp_c": 15, "condition": "Overcast"},
    "tokyo":     {"temp_c": 30, "condition": "Humid and warm"},
}

def run(city: str) -> str:
    """Execute the weather tool."""
    data = _FAKE_WEATHER.get(city.lower())
    if not data:
        return f"No weather data available for '{city}'."
    return (
        f"{city.title()}: {data['temp_c']}°C, {data['condition']}"
    )