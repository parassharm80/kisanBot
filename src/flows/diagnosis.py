from genkit import flow
from genkit.flow import run
from PIL import Image
from genkit.models import gemini_pro_vision

@flow()
def diagnose_disease(image: Image.Image, instructions: str) -> str:
    """
    Analyzes an image of a plant using a multimodal model and provides a diagnosis
    and remedy based on user instructions (e.g., from voice input).
    """
    print("Analyzing plant image...")
    
    # Use the gemini_pro_vision model for image analysis
    response = gemini_pro_vision.generate(
        {
            "input": [
                {"text": f"Analyze this plant image based on the following instructions: {instructions}. Identify potential diseases or pests and suggest a remedy."},
                {"media": {"image": image, "content_type": "image/jpeg"}}
            ]
        }
    )
    
    return response.text()
