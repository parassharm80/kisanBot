from google.cloud import firestore
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

class FirestoreClient:
    def __init__(self, project_id: str = None, credentials=None):
        """Initialize Firestore client"""
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        if credentials:
            self.db = firestore.Client(project=self.project_id, credentials=credentials)
        else:
            self.db = firestore.Client(project=self.project_id)

    # User Session Management
    async def save_user_session(self, user_id: str, session_data: Dict[str, Any]) -> None:
        """Save or update user session data"""
        session_data['last_updated'] = datetime.utcnow()
        self.db.collection('user_sessions').document(user_id).set(session_data, merge=True)

    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user session data"""
        doc = self.db.collection('user_sessions').document(user_id).get()
        return doc.to_dict() if doc.exists else None

    # Agricultural Knowledge Base
    async def store_disease_info(self, disease_id: str, disease_data: Dict[str, Any]) -> None:
        """Store disease information with embeddings"""
        disease_data['created_at'] = datetime.utcnow()
        self.db.collection('diseases').document(disease_id).set(disease_data)

    async def query_diseases_by_symptoms(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """Query diseases by symptoms"""
        results = []
        for symptom in symptoms:
            query = self.db.collection('diseases').where('symptoms', 'array_contains', symptom).limit(5)
            docs = query.stream()
            results.extend([doc.to_dict() for doc in docs])
        return results

    # Market Data Storage
    async def store_market_price(self, crop: str, location: str, price_data: Dict[str, Any]) -> None:
        """Store current market prices"""
        doc_id = f"{crop}_{location}_{datetime.now().strftime('%Y%m%d')}"
        price_data['timestamp'] = datetime.utcnow()
        self.db.collection('market_prices').document(doc_id).set(price_data)

    async def get_latest_price(self, crop: str, location: str) -> Optional[Dict[str, Any]]:
        """Get latest price for crop in location"""
        query = (self.db.collection('market_prices')
                .where('crop', '==', crop)
                .where('location', '==', location)
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
                .limit(1))

        docs = list(query.stream())
        return docs[0].to_dict() if docs else None

    # Government Schemes
    async def store_scheme(self, scheme_id: str, scheme_data: Dict[str, Any]) -> None:
        """Store government scheme information"""
        scheme_data['created_at'] = datetime.utcnow()
        self.db.collection('schemes').document(scheme_id).set(scheme_data)

    async def search_schemes(self, keywords: List[str], state: str = None) -> List[Dict[str, Any]]:
        """Search schemes by keywords and state"""
        query = self.db.collection('schemes')

        if state:
            query = query.where('applicable_states', 'array_contains', state)

        # Simple keyword matching (in production, use vector search)
        results = []
        docs = query.stream()
        for doc in docs:
            data = doc.to_dict()
            title = data.get('title', '').lower()
            description = data.get('description', '').lower()

            if any(keyword.lower() in title or keyword.lower() in description for keyword in keywords):
                results.append(data)

        return results

    # Embedding Cache
    async def cache_embedding(self, text: str, embedding: List[float], source: str = "text") -> None:
        """Cache computed embeddings to avoid recomputation"""
        cache_data = {
            'text': text,
            'embedding': embedding,
            'source': source,
            'cached_at': datetime.utcnow()
        }
        # Use hash of text as document ID for quick lookup
        doc_id = str(hash(text))
        self.db.collection('embedding_cache').document(doc_id).set(cache_data)

    async def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve cached embedding for text"""
        doc_id = str(hash(text))
        doc = self.db.collection('embedding_cache').document(doc_id).get()
        if doc.exists:
            return doc.to_dict().get('embedding')
        return None