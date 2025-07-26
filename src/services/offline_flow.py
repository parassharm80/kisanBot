import base64
import xml.etree.ElementTree as ET
from src.chat_app.dependency_setup import offline_model

def generate_prompt(language_code: str, src_text: str = None) -> str:
    instructions = f"""
    <instruction>
    You are an AI assistant designed to help users with their queries in the {language_code} language.
    1. Translate the user query {src_text} from {language_code} to English for your understanding if needed.
    2. After translation reply to query in en and user language {language_code} as well in not more than 30 words.
    3. Keep the reply concise and relevant to the query.
    """
    output_structure = f"""
    Follow below xml tagging for response. All tags as it is:
    <OUTPUT_STRUCTURE>
    <ans_en>Reply in English</ans_en>
    <ans_src>Reply in {language_code}</ans_src>
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
            root = ET.fromstring(xml_string.strip())

            # Find description_en and description_src anywhere in the tree
            text_en_element = root.find(".//ans_en")
            text_src_element = root.find(".//ans_src")

            text_en = text_en_element.text if text_en_element is not None else None
            text_src = text_src_element.text if text_src_element is not None else None

            return text_en, text_src
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return None, None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None, None
    prompt = generate_prompt(language_code, src_text)
    print(f"Generated prompt: {prompt}")

    response = await offline_model.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    print(response.text)
    text_en, text_src = parse_xml(response.text)
    return text_en, text_src