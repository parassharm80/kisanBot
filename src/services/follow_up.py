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
def generate_prompt(language_code: str, user_query: str = None, answer: str = None) -> str:
    instructions = f"""
    <instructions>
    Given the user query and answer in English, user query <query>{user_query}</query> and answer <answer>{answer}</answer>, your role is to. Generate 3 follow-up questions in user language code <lang>{language_code}</lang> that they can ask. Length of each question should be less than 20 words and should be **COMPLETE** and **SELF-CONTAINED**.
    </instructions>
    """
    output_structure = f"""
    Follow below xml tagging for response. All tags as it is:
    <OUTPUT_STRUCTURE>
    <follow_up_questions>
        <q1>Follow-up question 1 in {language_code}</q1>
        <q2>Follow-up question 2 in {language_code}</q2>
        <q3>Follow-up question 3 in {language_code}</q3>
    </follow_up_questions>
    </OUTPUT_STRUCTURE>
    <instruction>
    """
    return "\n".join([instructions, output_structure])

async def async_generate_related(
    user_query: str,
    answer: str,
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

            # Extract follow-up questions
            questions = []
            follow_up = root.find("follow_up_questions")
            if follow_up is not None:
                for q in follow_up:
                    if q.text:
                        questions.append(q.text.strip())

            return questions

        except ET.ParseError as e:
            print("XML Parse Error:", e)
            return None

    prompt = generate_prompt(language_code, user_query, answer)
    print(f"Generated prompt: {prompt}")

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
    questions = parse_xml(response.text)
    # if category == "unknown":
    #     text_en = idk['en']
    #     text_src = idk[language_code]
    return questions
