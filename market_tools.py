import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from bs4 import BeautifulSoup
from ..flows.firestore_client import FirestoreClient

class MarketDataFetcher:
    def __init__(self):
        """Initialize market data fetcher"""
        self.firestore_client = FirestoreClient()
        self.api_cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    async def get_market_prices(self, crop: str, location: str) -> str:
        """Get current market prices for crop in location"""
        try:
            # Check cache first
            cached_price = await self.firestore_client.get_latest_price(crop, location)
            if cached_price and self._is_cache_valid(cached_price.get('timestamp')):
                return self._format_price_response(cached_price, crop, location)
            
            # Fetch fresh data
            price_data = await self._fetch_current_prices(crop, location)
            if price_data:
                # Cache the result
                await self.firestore_client.store_market_price(crop, location, price_data)
                return self._format_price_response(price_data, crop, location)
            
            return f"Sorry, I couldn't find current market prices for {crop} in {location}. Try checking local mandis or agricultural websites."
            
        except Exception as e:
            print(f"Error fetching market prices: {e}")
            return "I'm having trouble accessing market data right now. Please try again later."
    
    def _is_cache_valid(self, timestamp) -> bool:
        """Check if cached data is still valid"""
        if not timestamp:
            return False
        
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return datetime.utcnow() - timestamp < self.api_cache_duration
    
    async def _fetch_current_prices(self, crop: str, location: str) -> Optional[Dict[str, Any]]:
        """Fetch current prices from multiple sources"""
        # Try multiple data sources
        sources = [
            self._fetch_from_agmarknet,
            self._fetch_from_apmc_portal,
            self._fetch_from_commodity_api,
            self._fetch_mock_data  # Fallback for testing
        ]
        
        for source in sources:
            try:
                data = await source(crop, location)
                if data:
                    return data
            except Exception as e:
                print(f"Error with source {source.__name__}: {e}")
                continue
        
        return None
    
    async def _fetch_from_agmarknet(self, crop: str, location: str) -> Optional[Dict[str, Any]]:
        """Fetch data from AgMarkNet (Government portal)"""
        try:
            # AgMarkNet API endpoint (hypothetical - replace with actual)
            base_url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"
            
            # This would need proper API integration with government portal
            # For now, return None to try next source
            return None
            
        except Exception as e:
            print(f"AgMarkNet fetch error: {e}")
            return None
    
    async def _fetch_from_apmc_portal(self, crop: str, location: str) -> Optional[Dict[str, Any]]:
        """Fetch from state APMC portals"""
        try:
            # Map location to state APMC portal
            state_portals = {
                'delhi': 'https://delhiapmc.nic.in',
                'maharashtra': 'https://mahaapmc.gov.in',
                'punjab': 'https://punjabapmc.com',
                # Add more state portals
            }
            
            state = self._get_state_from_location(location)
            if state not in state_portals:
                return None
            
            # This would require web scraping or API integration
            # Implementing basic structure for now
            return None
            
        except Exception as e:
            print(f"APMC portal fetch error: {e}")
            return None
    
    async def _fetch_from_commodity_api(self, crop: str, location: str) -> Optional[Dict[str, Any]]:
        """Fetch from commodity price APIs"""
        try:
            # Example: CommodityAPI.com (replace with actual service)
            api_key = os.getenv('COMMODITY_API_KEY')
            if not api_key:
                return None
            
            base_url = "https://api.commodityapi.com/v1/rates"
            params = {
                'access_key': api_key,
                'symbols': self._get_commodity_symbol(crop),
                'base': 'INR'
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    rates = data.get('rates', {})
                    symbol = self._get_commodity_symbol(crop)
                    if symbol in rates:
                        return {
                            'source': 'CommodityAPI',
                            'price_per_kg': rates[symbol],
                            'currency': 'INR',
                            'market': 'National Average',
                            'grade': 'FAQ (Fair Average Quality)',
                            'last_updated': datetime.utcnow().isoformat()
                        }
            
            return None
            
        except Exception as e:
            print(f"Commodity API fetch error: {e}")
            return None
    
    async def _fetch_mock_data(self, crop: str, location: str) -> Dict[str, Any]:
        """Generate mock market data for testing"""
        # Mock prices for common crops (per kg in INR)
        mock_prices = {
            'wheat': {'min': 20, 'max': 25, 'avg': 22.5},
            'rice': {'min': 18, 'max': 30, 'avg': 24},
            'maize': {'min': 15, 'max': 20, 'avg': 17.5},
            'soybean': {'min': 35, 'max': 45, 'avg': 40},
            'cotton': {'min': 5500, 'max': 6200, 'avg': 5850},  # per quintal
            'sugarcane': {'min': 280, 'max': 350, 'avg': 315},  # per quintal
            'onion': {'min': 12, 'max': 25, 'avg': 18.5},
            'potato': {'min': 8, 'max': 15, 'avg': 11.5},
            'tomato': {'min': 15, 'max': 40, 'avg': 27.5}
        }
        
        crop_lower = crop.lower()
        if crop_lower in mock_prices:
            price_info = mock_prices[crop_lower]
            return {
                'source': 'Mock Data',
                'price_min': price_info['min'],
                'price_max': price_info['max'], 
                'price_avg': price_info['avg'],
                'currency': 'INR',
                'unit': 'per quintal' if crop_lower in ['cotton', 'sugarcane'] else 'per kg',
                'market': f"{location.title()} Mandi",
                'grade': 'FAQ (Fair Average Quality)',
                'trend': 'stable',
                'last_updated': datetime.utcnow().isoformat(),
                'note': 'This is sample data for demonstration'
            }
        
        return {
            'source': 'Mock Data',
            'message': f"Price data for {crop} not available in our database",
            'suggestion': f"Please check local mandis in {location} for current {crop} prices"
        }
    
    def _get_state_from_location(self, location: str) -> str:
        """Map location to state"""
        location_state_map = {
            'delhi': 'delhi',
            'mumbai': 'maharashtra',
            'pune': 'maharashtra',
            'ludhiana': 'punjab',
            'chandigarh': 'punjab',
            'jaipur': 'rajasthan',
            'ahmedabad': 'gujarat',
            'bangalore': 'karnataka',
            'hyderabad': 'telangana',
            'chennai': 'tamil nadu'
        }
        return location_state_map.get(location.lower(), 'unknown')
    
    def _get_commodity_symbol(self, crop: str) -> str:
        """Get commodity trading symbol for crop"""
        symbols = {
            'wheat': 'WHEAT',
            'rice': 'RICE',
            'maize': 'CORN',
            'soybean': 'SOYBEAN',
            'cotton': 'COTTON',
            'sugar': 'SUGAR',
            'coffee': 'COFFEE'
        }
        return symbols.get(crop.lower(), crop.upper())
    
    def _format_price_response(self, price_data: Dict, crop: str, location: str) -> str:
        """Format price data into readable response"""
        if 'message' in price_data:
            return price_data['message']
        
        response = f"🌾 **Market Prices for {crop.title()} in {location.title()}**\n\n"
        
        if 'price_avg' in price_data:
            unit = price_data.get('unit', 'per kg')
            response += f"💰 Average Price: ₹{price_data['price_avg']} {unit}\n"
            
            if 'price_min' in price_data and 'price_max' in price_data:
                response += f"📊 Price Range: ₹{price_data['price_min']} - ₹{price_data['price_max']} {unit}\n"
        
        elif 'price_per_kg' in price_data:
            response += f"💰 Current Price: ₹{price_data['price_per_kg']} per kg\n"
        
        if 'market' in price_data:
            response += f"🏪 Market: {price_data['market']}\n"
        
        if 'grade' in price_data:
            response += f"📋 Grade: {price_data['grade']}\n"
        
        if 'trend' in price_data:
            trend_emoji = "📈" if price_data['trend'] == 'rising' else "📉" if price_data['trend'] == 'falling' else "➡️"
            response += f"{trend_emoji} Trend: {price_data['trend'].title()}\n"
        
        if 'last_updated' in price_data:
            response += f"🕐 Last Updated: {price_data['last_updated'][:10]}\n"
        
        if 'note' in price_data:
            response += f"\n📝 Note: {price_data['note']}\n"
        
        response += f"\n💡 **Tip**: Best selling time is usually early morning at the mandi for better prices!"
        
        return response

# Convenience function for backward compatibility
async def get_market_prices(crop: str, location: str) -> str:
    """Get market prices - main function called by flows"""
    fetcher = MarketDataFetcher()
    return await fetcher.get_market_prices(crop, location)
