import base64
import re
import xml.etree.ElementTree as ET
from src.chat_app.dependency_setup import offline_model
from google.generativeai.types import GenerationConfig
from google.genai import types

idk = {
    "en": "Sorry, I don't know",
    "hi": "मुझे खेद है, मुझे नहीं पता",
    "kn": "ಕ್ಷಮಿಸಿ, ನನಗೆ ಗೊತ್ತಿಲ್ಲ",
}
def generate_prompt(language_code: str, src_text: str = None) -> str:
    instructions = f"""
    You are Kisan Bot. Answer the following query <query>{src_text}</query> in user language code {language_code} and English. Use **farmer-friendly language**, keeping technical jargon to a minimum. Keep the length of each response under 30 words."""
    # instructions = f"""
    # You are Kisan Bot – an AI-powered personal farming assistant designed to support small-scale farmers in India, especially in rural areas.

    # Your role is to:
    # 1. Understand query given as english text.
    # 2. Identify the user’s intent
    # 3. Respond in user language code {language_code}. Translate the response to English using **farmer-friendly language**, keeping technical jargon to a minimum. Keep the length of each response under 30 words.

    # Always speak like a friendly local expert who deeply cares about the farmer’s success.

    # """
    output_structure = f"""
    Follow below xml tagging for response. All tags as it is:
    <OUTPUT_STRUCTURE>
    <ans_en>Response in English</ans_en>
    <ans_src>Response in {language_code}</ans_src>
    </OUTPUT_STRUCTURE>
    <instruction>
    """
    return "\n".join([instructions, output_structure])

async def async_generate_offline(
    src_text: str,
    language_code: str
) -> str:
    def parse_xml(xml_string):
        try:
            # Strip unwanted whitespace and parse
            xml_string = xml_string.strip()

            # If there's outer tag noise, extract <OUTPUT_STRUCTURE> content
            match = re.search(r"<OUTPUT_STRUCTURE>(.*?)</OUTPUT_STRUCTURE>", xml_string, re.DOTALL)
            if match:
                xml_string = "<OUTPUT_STRUCTURE>" + match.group(1).strip() + "</OUTPUT_STRUCTURE>"

            root = ET.fromstring(xml_string)

            # Extract values
            text_en = root.findtext("ans_en", default="").strip()
            text_src = root.findtext("ans_src", default="").strip()

            return text_en, text_src

        except ET.ParseError as e:
            print("XML Parse Error:", e)
            return None

    prompt = generate_prompt(language_code, src_text)
    # print(f"Generated prompt: {prompt}")

    # Configure generation settings
    config = types.GenerateContentConfig(
        temperature= 0.0
    )

    # Make the request
    response = await offline_model.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config
    )
    print(response.text)
    text_en, text_src = parse_xml(response.text)
    # if category == "unknown":
    #     text_en = idk['en']
    #     text_src = idk[language_code]
    return text_en, text_src
