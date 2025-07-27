import base64
import xml.etree.ElementTree as ET
from src.chat_app.dependency_setup import offline_model
import google.generativeai as genai
from google.genai import types

lang = {
    "en-IN": "English",
    "hi-IN": "hindi",
    "kn-IN": "kanada",
}
def generate_prompt(language_code: str, src_text: str = None) -> str:
    instructions = f"""
    <instruction>
    You are a language translator. Translate the user query {src_text} from {lang[language_code]} to English for your understanding. Output english translated response only
    </instruction>
    """
    return instructions

async def async_translate(
    src_text: str,
    language_code: str
) -> str:
    prompt = generate_prompt(language_code, src_text)
    print(f"Generated prompt: {prompt}")
    # Define the grounding tool
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    # Configure generation settings
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature= 0.0
    )

    # Make the request
    response = await offline_model.aio.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=config,
    )
    return response.text
