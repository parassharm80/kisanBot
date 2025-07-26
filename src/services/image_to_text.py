import base64
import xml.etree.ElementTree as ET
from src.chat_app.dependency_setup import image_model

def generate_prompt(language_code: str, src_text: str = None) -> str:
    common_instructions = """
    <instruction>
    1. Check if the given image is of a crop.
    """.strip()

    non_crop_instruction = f"""
    3. If it is not a crop, simply respond with: "This is not a crop image."
    4. Output the result in English and the given source language code {language_code}.
    """.strip()

    output_structure = f"""
    Follow below xml tagging for response. All tags as it is:
    <OUTPUT_STRUCTURE>
    <description_en>Response in English</description_en>
    <description_src>Response in {language_code}</description_src>
    </OUTPUT_STRUCTURE>
    </instruction>
    """.strip()

    if src_text is None:
        crop_instructions = f"""
        2. If it is:
        - Describe the image.
        - Determine the state of the crop (e.g., healthy, diseased, dry, etc.).
        - Keep the description within 30 words.
        """.strip()
    else:
        crop_instructions = f"""
        2. If it is:
        - Describe the image and determine the crop state.
        - Use the following user input in {language_code}: "{src_text}"
        - Generate a suitable answer considering the image and input context.
        """.strip()

    prompt = "\n".join([common_instructions, crop_instructions, non_crop_instruction, output_structure])
    return prompt

async def async_generate_text_from_image(
    image_bytes: bytes,
    language_code: str,
    src_text = None
) -> str:
    """
    Generates text based on an image and a prompt using Gemini.

    Args:
        image_bytes: The image data in bytes (e.g., from reading a file).
        prompt: The text prompt to guide the model's generation.
        vision_model: The initialized Gemini vision model client.

    Returns:
        The generated text from the model as a string.
    """
    def parse_xml(xml_string):
        try:
            root = ET.fromstring(xml_string.strip())

            # Find description_en and description_src anywhere in the tree
            text_en_element = root.find(".//description_en")
            text_src_element = root.find(".//description_src")

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
    # Base64 encode the image bytes
    encoded_image_data = base64.b64encode(image_bytes).decode('utf-8')

    # Prepare the content for the Gemini model
    # The structure is a list containing the prompt and the inline image data.
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image_data
                    }
                }
            ]
        }
    ]

    # Send the request to the Gemini model asynchronously
    response = await image_model.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents
    )

    print(f"response text: {response.text}")
    text_en, text_src = parse_xml(response.text)
    return text_en, text_src