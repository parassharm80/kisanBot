from genkit import flow
from genkit.flow import run
from PIL import Image
import re
import asyncio

# Import the specialized flows
from .diagnosis import diagnose_disease
from .market import market_analysis
from .schemes import government_schemes
from .vector_db_client import VectorDBClient

# Initialize vector client
vector_client = VectorDBClient()

@flow()
async def kisan_bot(query: str, image: Image.Image = None, user_context: dict = None) -> str:
    """The main orchestrator flow for the KisanBot."""
    print(f"KisanBot received query: '{query}'")
    
    # Initialize vector search if not already done
    if not hasattr(vector_client, 'index') or len(vector_client.document_store) == 0:
        await vector_client.load_index()
    
    # Extract user context
    user_location = None
    user_crops = []
    if user_context:
        user_location = user_context.get('location')
        user_crops = user_context.get('crops', [])
    
    # 1. Disease Diagnosis (if an image is provided)
    if image:
        return await run(diagnose_disease, image, query)
    
    # 2. Market Analysis (if query contains market-related keywords)
    if re.search(r'\b(price|market|rate|sell|selling|mandi|cost)\b', query, re.IGNORECASE):
        # Extract crop and location from query
        crop, location = _extract_market_entities(query, user_context)
        if crop and location:
            return await market_analysis(crop, location)
        else:
            # Use vector search to find market information
            market_results = await vector_client.search_market_info(crop or "general", "price")
            if market_results:
                return f"Here's market information I found:\n\n{market_results[0]['text']}\n\nPlease specify the crop and your location for detailed prices."
            else:
                return "I can help with market prices! Please tell me which crop you want to sell and your location. For example: 'What is the wheat price in Delhi?'"
        
    # 3. Government Schemes (if query contains scheme-related keywords)
    if re.search(r'\b(scheme|subsidy|government|apply|loan|credit|support|benefit|yojana)\b', query, re.IGNORECASE):
        state = _extract_state_from_query(query, user_context)
        return await government_schemes(query, state)
        
    # 4. General agricultural queries - use vector search
    search_results = await vector_client.search_similar(query, top_k=3, threshold=0.6)
    if search_results:
        best_match = search_results[0]
        response = f"Based on your query, here's what I found:\n\n{best_match['text']}"
        
        # Add related information if available
        if len(search_results) > 1:
            response += f"\n\n**Related Information:**\n{search_results[1]['text'][:200]}..."
        
        response += "\n\nWould you like more specific information about this topic?"
        return response
    
    # 5. Default case (if no specific flow is triggered)
    return _get_default_response(query)

def _extract_market_entities(query: str, user_context: dict = None) -> tuple:
    """Extract crop and location from market query"""
    # Common crops
    crops = ['wheat', 'rice', 'maize', 'corn', 'soybean', 'cotton', 'sugarcane', 
             'onion', 'potato', 'tomato', 'chili', 'turmeric', 'groundnut', 'mustard']
    
    # Common locations
    locations = ['delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad',
                'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur']
    
    query_lower = query.lower()
    
    # Find crop
    found_crop = None
    for crop in crops:
        if crop in query_lower:
            found_crop = crop
            break
    
    # Find location
    found_location = None
    for location in locations:
        if location in query_lower:
            found_location = location
            break
    
    # Use user context if available
    if not found_crop and user_context and user_context.get('crops'):
        found_crop = user_context['crops'][0]  # Use first crop from user profile
    
    if not found_location and user_context and user_context.get('location'):
        found_location = user_context['location']
    
    # Default fallbacks
    if not found_crop:
        found_crop = "wheat"  # Default crop
    if not found_location:
        found_location = "delhi"  # Default location
    
    return found_crop, found_location

def _extract_state_from_query(query: str, user_context: dict = None) -> str:
    """Extract state from query for scheme search"""
    states = ['punjab', 'haryana', 'uttar pradesh', 'maharashtra', 'karnataka', 
              'andhra pradesh', 'telangana', 'tamil nadu', 'kerala', 'gujarat',
              'rajasthan', 'madhya pradesh', 'bihar', 'west bengal', 'odisha']
    
    query_lower = query.lower()
    
    for state in states:
        if state in query_lower:
            return state
    
    # Check user context
    if user_context and user_context.get('state'):
        return user_context['state']
    
    return None

def _get_default_response(query: str) -> str:
    """Generate default response with helpful suggestions"""
    response = "I'm here to help with your agricultural needs! 🌾\n\n"
    response += "I can assist you with:\n"
    response += "• 🏥 **Plant Disease Diagnosis** - Send a photo of your plant\n"
    response += "• 💰 **Market Prices** - Ask about crop prices in your area\n"
    response += "• 🏛️ **Government Schemes** - Find subsidies and support programs\n"
    response += "• 🌱 **General Farming Advice** - Ask any agriculture-related question\n\n"
    
    response += "**Examples:**\n"
    response += "• \"What is the wheat price in Delhi?\"\n"
    response += "• \"Show me crop insurance schemes\"\n"
    response += "• \"How to control pest in tomato?\"\n"
    response += "• Send a photo with \"What's wrong with my plant?\"\n\n"
    
    response += "How can I help you today?"
    
    return response

# Backward compatibility wrapper
def kisan_bot_sync(query: str, image: Image.Image = None) -> str:
    """Synchronous wrapper for the main bot function"""
    return asyncio.run(kisan_bot(query, image))
