from google import genai
from google.genai import types

# Configure the client
client = genai.Client(api_key="AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc")

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Who won the euro 2024?",
    config=config,
)

# Print the grounded response
print(response.text)