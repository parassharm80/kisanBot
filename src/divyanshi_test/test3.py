from PIL import Image
from google import genai

client = genai.Client(api_key="AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc")

image = Image.open("/Users/divyanshigulati/Hack//crop1.jpg")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, "Whether this image is of crop or not? If yes, then what is the crop? Crop is good or bad? What is the reason for that? Give output in para in less than 30 words."],
)
print(response.text)