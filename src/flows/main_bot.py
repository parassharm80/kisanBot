from genkit import flow
from genkit.flow import run
from PIL import Image
import re

# Import the specialized flows
from .diagnosis import diagnose_disease
from .market import market_analysis
from .schemes import government_schemes

@flow()
def kisan_bot(query: str, image: Image.Image = None) -> str:
    """The main orchestrator flow for the KisanBot."""
    print(f"KisanBot received query: '{query}'")
    
    # 1. Disease Diagnosis (if an image is provided)
    if image:
        return run(diagnose_disease, image, query)
    
    # 2. Market Analysis (if query contains "price", "market", etc.)
    # A more robust implementation would use an LLM to extract entities (crop, location).
    if re.search(r'\b(price|market|rate)\b', query, re.IGNORECASE):
        # Mock entity extraction
        crop = "wheat" 
        location = "delhi"
        return run(market_analysis, crop, location)
        
    # 3. Government Schemes (if query contains "scheme", "subsidy", etc.)
    if re.search(r'\b(scheme|subsidy|government|apply)\b', query, re.IGNORECASE):
        return run(government_schemes, query)
        
    # 4. Default case (if no specific flow is triggered)
    print("No specific flow triggered. Sending to a general model (not implemented).")
    return "I can help with plant diseases (send a photo), market prices, and government schemes. How can I assist you today?"
