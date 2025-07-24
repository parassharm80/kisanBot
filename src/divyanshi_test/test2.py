from google import genai

# Initialize the client with your API key
client = genai.Client(api_key="AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)

print(response.text)