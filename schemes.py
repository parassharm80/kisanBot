from genkit import flow
from ..tools.scheme_tools import search_government_schemes

@flow()
async def government_schemes(query: str, state: str = None) -> str:
    """
    Flow to help farmers find relevant government schemes and subsidies.
    """
    print(f"Searching government schemes for query: '{query}'")
    
    # Search for relevant schemes
    schemes_response = await search_government_schemes(query, state)
    
    # Add application guidance
    guidance = _get_application_guidance()
    
    return f"{schemes_response}\n\n{guidance}"

def _get_application_guidance() -> str:
    """Provide general guidance for scheme applications"""
    guidance = "🚀 **How to Apply for Schemes:**\n\n"
    guidance += "**Step 1: Documentation**\n"
    guidance += "• Keep Aadhaar card ready and linked to bank account\n"
    guidance += "• Collect land ownership documents\n"
    guidance += "• Take passport-size photographs\n"
    guidance += "• Get income/caste certificates if required\n\n"
    
    guidance += "**Step 2: Application Process**\n"
    guidance += "• Visit nearest Common Service Center (CSC)\n"
    guidance += "• Use official government portals\n"
    guidance += "• Visit Krishi Vigyan Kendra for assistance\n"
    guidance += "• Contact local agriculture officer\n\n"
    
    guidance += "**Step 3: Follow-up**\n"
    guidance += "• Save application receipt/reference number\n"
    guidance += "• Track application status online\n"
    guidance += "• Contact helpline if delayed\n"
    guidance += "• Keep documents safe for verification\n\n"
    
    guidance += "📞 **Helplines:**\n"
    guidance += "• PM-KISAN: 155261 / 1800115526\n"
    guidance += "• Agriculture: 1551\n"
    guidance += "• CSC: 1800 121 3468"
    
    return guidance
