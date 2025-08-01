import base64
import xml.etree.ElementTree as ET
import google.generativeai as genai
from google.cloud import speech
from google.oauth2 import service_account
from src.chat_app.dependency_setup import speech_model
genai.configure(api_key='AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc')
import os
from google import auth

stt_client = None
language_dict = {
    "en-IN": "en",
    "hi-IN": "hi",
    "kn-IN": "te",
}
async def async_transcribe_ogg_bytes_stt(audio_bytes: bytes, language_code: str) -> str:
    """
    Asynchronously transcribes audio bytes in Ogg format to text.

    Args:
        audio_bytes: The raw bytes of the Ogg audio file.
        language_code: The language of the speech in the audio.
                       Examples: "en-US" for English, "hi-IN" for Hindi.

    Returns:
        The transcribed text.
    """
    print(f"Starting transcription for language: {language_code}...")
    
    # Create an asynchronous client
    global stt_client
    if not stt_client:
        print("Initializing Speech-to-Text client...")

        API_KEY = os.environ.get("API_KEY", "")
        credentials, project_id = "", ""
        if os.environ.get("ENV") == "local":
            SERVICE_ACCOUNT_KEY_FILE = os.environ.get("SERVICE_ACCOUNT_KEY_FILE")
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)

            project_id = os.environ.get("PROJECT_ID")

        else:
            credentials, project_id = auth.default()
        # global stt_client
        stt_client = speech.SpeechAsyncClient(credentials=credentials)

    # The audio data is passed directly to the API
    audio = speech.RecognitionAudio(content=audio_bytes)

    # Configure the request for Ogg format with Opus encoding
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=48000,  # Ogg/Opus typically uses 48000Hz
        language_code=language_code,
    )

    try:
        # Await the recognize method
        response = await stt_client.recognize(config=config, audio=audio)
    except Exception as e:
        print(f"An error occurred during transcription for {language_code}: {e}")
        return ""

    if not response.results:
        print(f"No speech detected for language: {language_code}.")
        return ""

    # Concatenate the results to form the final transcript
    transcript = "".join(result.alternatives[0].transcript for result in response.results)
    print(f"Finished transcription for language: {language_code}.")
    return transcript

async def async_transcribe_ogg_bytes_gemini(audio_bytes: bytes, language_code: str) -> str:

    def parse_transcripts_xml(xml_string: str) -> tuple[str | None, str | None]:
        try:
            root = ET.fromstring(xml_string.strip())

            # Find transcript_en and transcript_src anywhere in the tree
            text_en_element = root.find(".//transcript_en")
            text_src_element = root.find(".//transcript_src")

            text_en = text_en_element.text if text_en_element is not None else None
            text_src = text_src_element.text if text_src_element is not None else None

            return text_en, text_src
        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return None, None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None, None
    # Base64 encode the audio bytes
    encoded_audio_data = base64.b64encode(audio_bytes).decode('utf-8')
    
    prompt = f"""
    <instructions>
    You are a transciber. Transcribe the audio in ogg format to user language code {language_code} text and English text. 
    Follow below xml tagging for response. All tags as it is:
    <OUTPUT_STRUCTURE>
    <transcript_en>Response in English</transcript_en>
    <transcript_src>Response in {language_code}</transcript_src>
    </OUTPUT_STRUCTURE>.
    </instructions>"""

    # Prepare the content for the Gemini model
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "audio/ogg; codecs=opus",
                        "data": encoded_audio_data
                    }
                }
            ]
        }
    ]

    # Send the request to the Gemini model asynchronously
    response = await speech_model.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents
    )
    print(response.text)
    text_en, text_src = parse_transcripts_xml(response.text)

    return text_en, text_src