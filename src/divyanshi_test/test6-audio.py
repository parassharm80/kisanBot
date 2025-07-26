from google import genai
import os # Import the os module for file path operations
import base64 # Import the base64 module for encoding binary data

# Configure the API client
# In a real application, you would typically load your API key from environment variables
# or a secure configuration management system, not hardcode it.
# For demonstration purposes, I'll keep it as an empty string, assuming the environment
# will provide it if running in a Canvas-like setup.
client = genai.Client(api_key="AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc") # Leave empty for Canvas environment to provide

# Define the path to your audio file
# IMPORTANT: Replace '/Users/divyanshigulati/Hack/audio.ogg' with the actual path
# to your audio file on your system.
audio_file_path = '/Users/divyanshigulati/Hack/audio.ogg'

# Check if the file exists before attempting to read it
if not os.path.exists(audio_file_path):
    print(f"Error: Audio file not found at '{audio_file_path}'")
    print("Please update 'audio_file_path' to the correct location of your audio file.")
else:
    try:
        # Read the audio file as bytes
        # 'rb' mode opens the file in binary read mode
        with open(audio_file_path, 'rb') as f:
            audio_bytes = f.read()

        # Base64 encode the audio bytes
        # The Gemini API expects binary data in inlineData.data to be base64 encoded.
        encoded_audio_data = base64.b64encode(audio_bytes).decode('utf-8')

        # Create the prompt for the model
        prompt = 'Generate a transcript of the speech.'

        # Prepare the content for the Gemini model, including the base64 encoded audio data
        # This is how you provide byte stream data directly to the API
        contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    },
                    {
                        "inlineData": {
                            "mimeType": "audio/ogg", # Specify the correct MIME type for your audio file
                                                      # Common types: "audio/ogg", "audio/wav", "audio/mpeg" (for MP3)
                            "data": encoded_audio_data # Use the base64 encoded string here
                        }
                    }
                ]
            }
        ]

        # Send the request to the Gemini model
        # Using gemini-2.5-flash as requested, or adjust if a different model is preferred
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )

        # Print the transcribed text
        print("Transcription:")
        print(response.text)

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure your audio file is valid and the MIME type is correct.")
        print("Also, verify that the 'audio_file_path' variable points to a readable file.")

