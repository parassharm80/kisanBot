from genkit import flow
from src.tools.market_tools import get_market_prices

@flow()
def market_analysis(crop: str, location: str) -> str:
    """
    Flow to provide advice on selling a crop by fetching and analyzing market prices.
    """
    print(f"Running market analysis for {crop} in {location}...")
    price_info = get_market_prices(crop=crop, location=location)
    
    # In a real app, you could add more complex analysis here using an LLM.
    return f"{price_info}. Based on current trends, it appears to be a good time to sell."
