import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from bs4 import BeautifulSoup
from ..flows.firestore_client import FirestoreClient
from ..flows.vector_db_client import VectorDBClient

class SchemeDataManager:
    def __init__(self):
        """Initialize scheme data manager"""
        self.firestore_client = FirestoreClient()
        self.vector_client = VectorDBClient()
        
    async def search_government_schemes(self, query: str, state: str = None, category: str = None) -> str:
        """Search for relevant government schemes"""
        try:
            # Use vector search for semantic matching
            vector_results = self.vector_client.search_schemes(query)
            
            # Also search in Firestore
            keywords = self._extract_keywords(query)
            firestore_results = await self.firestore_client.search_schemes(keywords, state)
            
            # Combine and deduplicate results
            all_schemes = self._combine_results(vector_results, firestore_results)
            
            if not all_schemes:
                # If no results, try to fetch from online sources
                online_schemes = await self._fetch_online_schemes(query, state)
                if online_schemes:
                    all_schemes = online_schemes
            
            if all_schemes:
                return self._format_scheme_response(all_schemes, query)
            else:
                return self._no_schemes_found_response(query, state)
                
        except Exception as e:
            print(f"Error searching schemes: {e}")
            return "I'm having trouble accessing scheme information right now. Please try again later."
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from user query"""
        # Common scheme-related keywords
        scheme_keywords = [
            'subsidy', 'loan', 'credit', 'insurance', 'support', 'assistance',
            'benefit', 'welfare', 'development', 'agriculture', 'farmer',
            'crop', 'irrigation', 'fertilizer', 'seed', 'machinery', 'equipment'
        ]
        
        # Economic keywords
        economic_keywords = [
            'income', 'money', 'financial', 'economic', 'poverty', 'relief'
        ]
        
        # Technology keywords  
        tech_keywords = [
            'technology', 'modern', 'digital', 'online', 'training', 'skill'
        ]
        
        all_keywords = scheme_keywords + economic_keywords + tech_keywords
        
        # Extract keywords present in query
        query_lower = query.lower()
        found_keywords = [kw for kw in all_keywords if kw in query_lower]
        
        # Add specific words from query
        query_words = [word.strip('.,!?') for word in query_lower.split() if len(word) > 3]
        found_keywords.extend(query_words)
        
        return list(set(found_keywords))  # Remove duplicates
    
    def _combine_results(self, vector_results: List[Dict], firestore_results: List[Dict]) -> List[Dict]:
        """Combine and deduplicate results from different sources"""
        combined = []
        seen_ids = set()
        
        # Add vector search results
        for result in vector_results:
            scheme_id = result.get('id') or result.get('metadata', {}).get('id')
            if scheme_id and scheme_id not in seen_ids:
                combined.append({
                    'id': scheme_id,
                    'title': result.get('metadata', {}).get('title', 'Unknown Scheme'),
                    'description': result.get('text', ''),
                    'source': 'vector_search',
                    'similarity_score': result.get('similarity_score', 0),
                    **result.get('metadata', {})
                })
                seen_ids.add(scheme_id)
        
        # Add Firestore results
        for result in firestore_results:
            scheme_id = result.get('id')
            if scheme_id and scheme_id not in seen_ids:
                combined.append({
                    **result,
                    'source': 'firestore',
                    'similarity_score': 0.8  # Default score for Firestore matches
                })
                seen_ids.add(scheme_id)
        
        # Sort by similarity score
        return sorted(combined, key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    async def _fetch_online_schemes(self, query: str, state: str = None) -> List[Dict]:
        """Fetch schemes from online government portals"""
        try:
            schemes = []
            
            # Try different government portals
            portals = [
                self._fetch_from_pmkisan,
                self._fetch_from_agri_portal,
                self._fetch_from_state_portals,
                self._get_popular_schemes  # Fallback
            ]
            
            for portal in portals:
                try:
                    portal_schemes = await portal(query, state)
                    if portal_schemes:
                        schemes.extend(portal_schemes)
                except Exception as e:
                    print(f"Error with portal {portal.__name__}: {e}")
                    continue
            
            return schemes[:5]  # Return top 5 schemes
            
        except Exception as e:
            print(f"Error fetching online schemes: {e}")
            return []
    
    async def _fetch_from_pmkisan(self, query: str, state: str = None) -> List[Dict]:
        """Fetch from PM-KISAN portal"""
        # This would integrate with actual PM-KISAN API
        # For now, return mock data if relevant
        if any(keyword in query.lower() for keyword in ['income', 'support', 'money', 'kisan']):
            return [{
                'id': 'pm_kisan_001',
                'title': 'PM-KISAN Samman Nidhi',
                'description': 'Direct income support of ₹6000 per year to eligible farmer families',
                'benefits': '₹2000 every 4 months (₹6000 annually)',
                'eligibility': 'Small and marginal farmer families',
                'application': 'Online at pmkisan.gov.in',
                'documents': ['Aadhaar', 'Bank account', 'Land records'],
                'source': 'PM-KISAN Portal'
            }]
        return []
    
    async def _fetch_from_agri_portal(self, query: str, state: str = None) -> List[Dict]:
        """Fetch from agriculture.gov.in"""
        # Mock implementation - would integrate with actual API
        return []
    
    async def _fetch_from_state_portals(self, query: str, state: str = None) -> List[Dict]:
        """Fetch from state government portals"""
        # Mock implementation for state-specific schemes
        if state:
            state_schemes = {
                'punjab': [
                    {
                        'id': 'punjab_001',
                        'title': 'Punjab Crop Diversification Scheme',
                        'description': 'Financial support for farmers to diversify from paddy to other crops',
                        'state': 'Punjab'
                    }
                ],
                'maharashtra': [
                    {
                        'id': 'maha_001', 
                        'title': 'Maharashtra Crop Insurance Scheme',
                        'description': 'Comprehensive crop insurance for weather-related losses',
                        'state': 'Maharashtra'
                    }
                ]
            }
            return state_schemes.get(state.lower(), [])
        return []
    
    async def _get_popular_schemes(self, query: str = None, state: str = None) -> List[Dict]:
        """Get popular/common agricultural schemes"""
        popular_schemes = [
            {
                'id': 'pmfby_001',
                'title': 'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
                'description': 'Crop insurance scheme providing financial support to farmers in case of crop failure',
                'benefits': 'Insurance coverage for crop losses due to natural calamities',
                'premium': 'Only 2% for Kharif, 1.5% for Rabi crops',
                'application': 'Through banks, CSCs, or online portal',
                'category': 'insurance'
            },
            {
                'id': 'pmkcc_001', 
                'title': 'PM Kisan Credit Card (KCC)',
                'description': 'Credit facility for farmers to meet agricultural and allied activities',
                'benefits': 'Easy access to credit at subsidized interest rates',
                'features': ['Flexible repayment', 'No collateral for loans up to ₹1.6 lakh'],
                'application': 'Any bank branch',
                'category': 'credit'
            },
            {
                'id': 'soil_health_001',
                'title': 'Soil Health Card Scheme', 
                'description': 'Provides soil health cards to farmers with nutrient status and recommendations',
                'benefits': 'Free soil testing and fertilizer recommendations',
                'application': 'Krishi Vigyan Kendras or agriculture departments',
                'category': 'technology'
            },
            {
                'id': 'organic_001',
                'title': 'Paramparagat Krishi Vikas Yojana (PKVY)',
                'description': 'Promotes organic farming through financial assistance and certification',
                'benefits': '₹50,000 per hectare over 3 years for organic farming',
                'application': 'Through state agriculture departments',
                'category': 'organic'
            }
        ]
        
        # Filter based on query keywords if provided
        if query:
            query_lower = query.lower()
            filtered = []
            for scheme in popular_schemes:
                if any(keyword in query_lower for keyword in 
                      [scheme['category'], scheme['title'].lower(), scheme['description'].lower()]):
                    filtered.append(scheme)
            return filtered if filtered else popular_schemes[:3]
        
        return popular_schemes
    
    def _format_scheme_response(self, schemes: List[Dict], query: str) -> str:
        """Format scheme search results into readable response"""
        if not schemes:
            return self._no_schemes_found_response(query)
        
        response = f"🏛️ **Government Schemes Related to: {query}**\n\n"
        
        for i, scheme in enumerate(schemes[:3], 1):  # Show top 3 schemes
            response += f"**{i}. {scheme.get('title', 'Unknown Scheme')}**\n"
            response += f"📋 {scheme.get('description', 'No description available')}\n"
            
            if 'benefits' in scheme:
                response += f"💰 Benefits: {scheme['benefits']}\n"
            
            if 'eligibility' in scheme:
                response += f"✅ Eligibility: {scheme['eligibility']}\n"
            
            if 'application' in scheme:
                response += f"📝 Apply: {scheme['application']}\n"
            
            if 'documents' in scheme:
                docs = ', '.join(scheme['documents']) if isinstance(scheme['documents'], list) else scheme['documents']
                response += f"📄 Documents: {docs}\n"
            
            if 'state' in scheme:
                response += f"📍 State: {scheme['state']}\n"
            
            response += "\n" + "─" * 40 + "\n\n"
        
        response += "💡 **Tips:**\n"
        response += "• Keep Aadhaar and bank account linked\n"
        response += "• Maintain proper land records\n" 
        response += "• Apply before deadlines\n"
        response += "• Visit nearest CSC or Krishi Vigyan Kendra for help\n\n"
        response += "🔗 For more schemes, visit: https://pmkisan.gov.in or your state agriculture portal"
        
        return response
    
    def _no_schemes_found_response(self, query: str, state: str = None) -> str:
        """Response when no schemes are found"""
        response = f"🔍 No specific schemes found for '{query}'"
        if state:
            response += f" in {state}"
        response += ".\n\n"
        
        response += "📋 **Popular Agricultural Schemes:**\n"
        response += "• PM-KISAN Samman Nidhi (Income Support)\n"
        response += "• PM Fasal Bima Yojana (Crop Insurance)\n"
        response += "• PM Kisan Credit Card (Agricultural Credit)\n"
        response += "• Soil Health Card Scheme\n"
        response += "• Organic Farming Support\n\n"
        
        response += "💬 Try asking about:\n"
        response += "• 'Income support schemes'\n"
        response += "• 'Crop insurance schemes'\n"
        response += "• 'Agricultural loan schemes'\n"
        response += "• 'Fertilizer subsidy'\n"
        response += "• 'Irrigation schemes'\n\n"
        
        response += "🏛️ Visit your nearest CSC or agriculture office for personalized assistance!"
        
        return response

# Convenience function for backward compatibility
async def search_government_schemes(query: str, state: str = None) -> str:
    """Search government schemes - main function called by flows"""
    manager = SchemeDataManager()
    return await manager.search_government_schemes(query, state)
