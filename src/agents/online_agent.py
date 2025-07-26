import asyncio

# Add these imports
from google import genai
from google.genai import types

# You should load the API key from an environment variable in production!
GEMINI_API_KEY = "AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc"  # Replace with your actual key or use os.environ.get("GEMINI_API_KEY")

async def generation_online(query: str) -> str:
    """
    Asynchronously calls Gemini with web search capabilities for the given query.
    """
    print("➡️ Routing to: ASYNC ONLINE (Web Search)")

    # Run the blocking Gemini call in a thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    response_text = await loop.run_in_executor(None, _gemini_web_search, query)
    return response_text

def _gemini_web_search(query: str) -> str:
    """
    Synchronous helper to call Gemini API with Google Search grounding.
    """
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(tools=[grounding_tool])

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=config,
        )
        return f"🌐 [ONLINE Gemini]: {response.text.strip()}"
    except Exception as e:
        return f"❌ Gemini API error: {e}"