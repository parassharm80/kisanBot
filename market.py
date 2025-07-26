from genkit import flow
from ..tools.market_tools import get_market_prices

@flow()
async def market_analysis(crop: str, location: str) -> str:
    """
    Flow to provide advice on selling a crop by fetching and analyzing market prices.
    """
    print(f"Running market analysis for {crop} in {location}...")
    
    # Get comprehensive market data
    price_info = await get_market_prices(crop=crop, location=location)
    
    # Add market intelligence and recommendations
    recommendations = _generate_market_recommendations(crop, location)
    
    return f"{price_info}\n\n{recommendations}"

def _generate_market_recommendations(crop: str, location: str) -> str:
    """Generate market recommendations based on crop and location"""
    recommendations = "📈 **Market Recommendations:**\n\n"
    
    # General recommendations based on crop type
    crop_specific = {
        'wheat': [
            "Best to sell during April-May after harvest",
            "Check MSP (Minimum Support Price) rates",
            "Consider storage if prices are below MSP"
        ],
        'rice': [
            "October-November is peak selling season",
            "Check government procurement centers",
            "Quality matters - clean and dry rice gets better prices"
        ],
        'cotton': [
            "Sell early in the season for better prices",
            "Check CCI (Cotton Corporation of India) rates",
            "Grade your cotton properly"
        ],
        'sugarcane': [
            "Coordinate with nearby sugar mills",
            "Check FRP (Fair and Remunerative Price)",
            "Timely delivery reduces weight loss"
        ]
    }
    
    crop_lower = crop.lower()
    if crop_lower in crop_specific:
        for rec in crop_specific[crop_lower]:
            recommendations += f"• {rec}\n"
    else:
        recommendations += "• Sell early morning for best prices\n"
        recommendations += "• Check multiple mandis for better rates\n"
        recommendations += "• Ensure proper grading and packaging\n"
    
    recommendations += "\n💡 **General Tips:**\n"
    recommendations += "• Avoid selling immediately after widespread harvest\n"
    recommendations += "• Keep track of weather forecasts affecting supply\n"
    recommendations += "• Join farmer groups for better negotiating power\n"
    recommendations += "• Use digital platforms for price discovery"
    
    return recommendations
