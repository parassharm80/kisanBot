import asyncio
from google.cloud import texttospeech_v1
from google.oauth2 import service_account
from typing import Optional
from google.auth import default
from src.chat_app.dependency_setup import SERVICE_ACCOUNT_KEY_FILE

client = None
async def async_text_to_speech(
    text: str,
    language_code: str
) -> Optional[bytes]:
    from google.cloud import texttospeech_v1
    global client
    if not client:
        print("Initializing Text-to-Speech client...")
        if os.environ.get("ENV") == "local":
           SERVICE_ACCOUNT_KEY_FILE = os.environ.get("SERVICE_ACCOUNT_KEY_FILE")
           API_KEY = os.environ.get("API_KEY")
           credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)
        else:
          credentials, project_id = default()

        
        # global client
        client = texttospeech_v1.TextToSpeechAsyncClient(credentials=credentials)

    """
    Asynchronously synthesizes speech from text and returns it as bytes.

    This function uses Google Cloud's Text-to-Speech API to convert a given
    string of text into OGG Opus audio data.

    Args:
        client (texttospeech_v1.TextToSpeechAsyncClient): The authenticated async client.
        text (str): The text to be synthesized.
        language_code (str): The language of the text (e.g., "en-IN", "hi-IN").

    Returns:
        Optional[bytes]: The synthesized audio content as bytes, or None if an
                         error occurs.
    """
    try:
        # Set the text input to be synthesized
        synthesis_input = texttospeech_v1.SynthesisInput(text=text)

        # A mapping of language codes to recommended voice names.
        voice_map = {
            "en-IN": "en-IN-Wavenet-A",
            "hi-IN": "hi-IN-Neural2-A",
            "kn-IN": "kn-IN-Wavenet-A",  # Using a Wavenet voice for Kannada
        }

        voice_name = voice_map.get(language_code)
        if not voice_name:
            print(f"Warning: Language code '{language_code}' not in voice map.")
            print("Defaulting to 'en-IN'.")
            language_code = "en-IN"
            voice_name = voice_map[language_code]

        # Build the voice request, select a language code and a neural voice.
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=language_code, name=voice_name
        )

        # Select the audio file type.
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.OGG_OPUS,
            sample_rate_hertz=48000
        )

        print(f"Synthesizing speech for '{language_code}': '{text}'")

        # Perform the text-to-speech request
        response = await client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Return the audio content as bytes
        print(f"Successfully synthesized audio for '{language_code}'.")
        return response.audio_content

    except Exception as e:
        print(f"An error occurred during synthesis for '{language_code}': {e}")
        return None

# async def main():
#     """Main function to load credentials, create a client, and run async TTS tasks."""
    
#     # --- CREDENTIALS HANDLING ---
#     # IMPORTANT: Replace this with the actual path to your service account key file.
#     credentials_path = "/Users/parassharma/Downloads/serene-flare-466616-m5-ced346076763.json"
    
#     try:
#         credentials = service_account.Credentials.from_service_account_file(credentials_path)
#         client = texttospeech_v1.TextToSpeechAsyncClient(credentials=credentials)
#     except FileNotFoundError:
#         print(f"Error: Credentials file not found at '{credentials_path}'.")
#         print("Please update the 'credentials_path' variable with the correct path.")
#         return
#     except Exception as e:
#         print(f"An error occurred while loading credentials: {e}")
#         return

#     # A list of tuples, each containing the text and its language code.
#     synthesis_requests = [
#         ("Hello, this is a test in English.", "en-IN"),
#         ("नमस्ते, यह हिंदी में एक परीक्षण है।", "hi-IN"),
#         ("ನಮಸ್ಕಾರ, ಇದು ಕನ್ನಡದಲ್ಲಿ ಒಂದು ಪರೀಕ್ಷೆ.", "kn-IN"),
#     ]

#     # Create a list of asynchronous tasks, passing the client to each.
#     tasks = [
#         async_text_to_speech(client, text, lang) for text, lang in synthesis_requests
#     ]
    
#     # Run all tasks concurrently and gather the results
#     audio_results = await asyncio.gather(*tasks)

#     # Process the results
#     for i, audio_bytes in enumerate(audio_results):
#         lang = synthesis_requests[i][1]
#         if audio_bytes:
#             print(f"Received {len(audio_bytes)} bytes of audio for language '{lang}'.")
#             # For demonstration, let's save the English audio to a file.
#             if lang == "en-IN":
#                 with open("output_en_from_bytes.ogg", "wb") as f:
#                     f.write(audio_bytes)
#                     print("Saved the English audio to 'output_en_from_bytes.ogg'")
#         else:
#             print(f"Failed to receive audio bytes for language '{lang}'.")


# if __name__ == "__main__":
#     asyncio.run(main())
