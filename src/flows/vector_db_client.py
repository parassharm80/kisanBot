import numpy as np
from typing import List, Dict, Tuple, Optional
from google.cloud import aiplatform
import faiss
import json
import os
from .firestore_client import FirestoreClient
from .vertex_ai_emb_gen import get_embedding_generator

class VectorDBClient:
    def __init__(self, project_id: str = None, region: str = "us-central1"):
        """Initialize Vector DB client with enhanced Vertex AI embedding generator"""
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = region
        
        # Initialize enhanced embedding generator (uses your vertex_ai_emb_gen.py)
        self.embedding_generator = get_embedding_generator(project_id, region)
        
        # Get model info from embedding generator
        model_info = self.embedding_generator.get_model_info()
        self.dimension = model_info['dimensionality']  # 3072 for gemini-embedding-001
        
        print(f"🔍 Vector DB using: {model_info['model_name']} with {self.dimension} dimensions")
        
        # Initialize FAISS for local vector search
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for similarity
        self.document_store = []  # Store document metadata
        
        # Firestore client for persistence
        self.firestore_client = FirestoreClient(project_id)
    
    async def generate_embedding(self, text: str, source: str = "text") -> List[float]:
        """
        Generate embedding for given text using enhanced preprocessing
        
        Args:
            text: Input text
            source: Source type ('text', 'speech', 'ocr') for appropriate preprocessing
        """
        try:
            # Check cache first
            cached = await self.firestore_client.get_cached_embedding(text)
            if cached:
                return cached
            
            # Generate new embedding using your enhanced generator
            embedding_vector = self.embedding_generator.embed_text(text, source)
            
            # Cache the embedding
            await self.firestore_client.cache_embedding(text, embedding_vector, source)
            
            return embedding_vector
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.dimension
    
    def generate_embeddings_batch(self, texts: List[str], source: str = "text") -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            return self.embedding_generator.embed_batch(texts, source)
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return [[0.0] * self.dimension] * len(texts)
    
    async def add_document(self, doc_id: str, text: str, metadata: Dict, source: str = "text") -> None:
        """
        Add document to vector index with source-aware preprocessing
        
        Args:
            doc_id: Unique document identifier
            text: Document text
            metadata: Additional document metadata
            source: Source type for preprocessing ('text', 'speech', 'ocr')
        """
        try:
            # Generate embedding with appropriate preprocessing
            embedding = await self.generate_embedding(text, source)
            
            # Add to FAISS index
            embedding_array = np.array([embedding]).astype('float32')
            self.index.add(embedding_array)
            
            # Store metadata with preprocessing info
            doc_data = {
                'id': doc_id,
                'text': text,
                'metadata': metadata,
                'source': source,
                'preprocessed_text': self.embedding_generator.preprocess(text, source),
                'index_position': len(self.document_store)
            }
            self.document_store.append(doc_data)
            
            print(f"📄 Added document {doc_id} to vector index (source: {source})")
            
        except Exception as e:
            print(f"Error adding document to vector index: {e}")
    
    async def search_similar(self, query: str, top_k: int = 5, threshold: float = 0.7, source: str = "text") -> List[Dict]:
        """
        Search for similar documents using vector similarity with smart preprocessing
        
        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            source: Query source type for preprocessing
        """
        try:
            # Generate query embedding with appropriate preprocessing
            query_embedding = await self.generate_embedding(query, source)
            query_array = np.array([query_embedding]).astype('float32')
            
            # Search in FAISS index
            scores, indices = self.index.search(query_array, min(top_k, len(self.document_store)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and score >= threshold:  # Valid index and above threshold
                    doc_data = self.document_store[idx].copy()
                    doc_data['similarity_score'] = float(score)
                    results.append(doc_data)
            
            return sorted(results, key=lambda x: x['similarity_score'], reverse=True)
            
        except Exception as e:
            print(f"Error searching vector index: {e}")
            return []
    
    async def build_agriculture_knowledge_base(self) -> None:
        """Build vector index from agricultural knowledge with diverse sources"""
        
        # Enhanced agricultural knowledge base with source attribution
        knowledge_base = [
            {
                'id': 'disease_001',
                'text': 'Leaf blight in rice crops shows brown spots on leaves with yellow halos. Treatment includes copper fungicides and proper drainage.',
                'category': 'disease',
                'crop': 'rice',
                'symptoms': ['brown spots', 'yellow halos', 'leaf damage'],
                'source': 'text'
            },
            {
                'id': 'disease_002', 
                'text': 'Powdery mildew appears as white powdery coating on leaves. Remove affected parts and apply sulfur-based fungicides.',
                'category': 'disease',
                'crop': 'general',
                'symptoms': ['white powder', 'leaf coating', 'mildew'],
                'source': 'text'
            },
            {
                'id': 'disease_003',
                'text': 'Tomato early blight causes dark brown spots with concentric rings on older leaves. Use fungicides and improve air circulation.',
                'category': 'disease',
                'crop': 'tomato',
                'symptoms': ['dark spots', 'concentric rings', 'older leaves'],
                'source': 'text'
            },
            {
                'id': 'market_001',
                'text': 'Best time to sell wheat is during harvest season March-April when demand is high and prices peak.',
                'category': 'market',
                'crop': 'wheat',
                'season': 'harvest',
                'source': 'text'
            },
            {
                'id': 'market_002',
                'text': 'Rice prices typically rise during monsoon delays. Store properly in moisture-free conditions for better rates.',
                'category': 'market',
                'crop': 'rice',
                'season': 'monsoon',
                'source': 'text'
            },
            {
                'id': 'scheme_001',
                'text': 'PM-KISAN scheme provides direct income support of Rs 6000 per year to farmer families. Apply online with Aadhaar.',
                'category': 'scheme',
                'benefits': 'income support',
                'eligibility': 'farmer families',
                'source': 'text'
            },
            {
                'id': 'scheme_002',
                'text': 'Pradhan Mantri Fasal Bima Yojana offers crop insurance at subsidized rates. Premium is only 2% for Kharif crops.',
                'category': 'scheme',
                'benefits': 'crop insurance',
                'eligibility': 'all farmers',
                'source': 'text'
            },
            {
                'id': 'weather_001',
                'text': 'During monsoon season, ensure proper drainage for rice crops to prevent root rot and fungal diseases.',
                'category': 'weather',
                'season': 'monsoon',
                'crop': 'rice',
                'source': 'text'
            },
            {
                'id': 'fertilizer_001',
                'text': 'Apply nitrogen fertilizer in split doses for wheat - 1/3 at sowing, 1/3 at first irrigation, 1/3 at second irrigation.',
                'category': 'fertilizer',
                'crop': 'wheat',
                'stage': 'multiple',
                'source': 'text'
            },
            {
                'id': 'pest_001',
                'text': 'Aphids on cotton can be controlled using neem oil spray or releasing ladybird beetles as biological control.',
                'category': 'pest',
                'crop': 'cotton',
                'control': 'biological',
                'source': 'text'
            }
        ]
        
        # Add documents to vector index
        for item in knowledge_base:
            source_type = item.pop('source', 'text')
            await self.add_document(
                doc_id=item['id'],
                text=item['text'],
                metadata={k: v for k, v in item.items() if k not in ['id', 'text']},
                source=source_type
            )
        
        print(f"🌾 Built agricultural knowledge base with {len(knowledge_base)} documents")
    
    async def add_speech_knowledge(self, doc_id: str, speech_text: str, metadata: Dict) -> None:
        """Add knowledge from speech input (like farmer interviews)"""
        await self.add_document(doc_id, speech_text, metadata, source="speech")
    
    async def add_ocr_knowledge(self, doc_id: str, ocr_text: str, metadata: Dict) -> None:
        """Add knowledge from OCR text (like scanned documents)"""
        await self.add_document(doc_id, ocr_text, metadata, source="ocr")
    
    async def search_diseases(self, symptoms: str, crop: str = None, source: str = "text") -> List[Dict]:
        """Search for diseases based on symptoms with smart preprocessing"""
        query = f"disease symptoms {symptoms}"
        if crop:
            query += f" in {crop} crop"
        
        results = await self.search_similar(query, top_k=3, source=source)
        return [r for r in results if r['metadata'].get('category') == 'disease']
    
    async def search_market_info(self, crop: str, query_type: str = "price", source: str = "text") -> List[Dict]:
        """Search for market information with preprocessing"""
        query = f"{crop} {query_type} market information selling"
        results = await self.search_similar(query, top_k=3, source=source)
        return [r for r in results if r['metadata'].get('category') == 'market']
    
    async def search_schemes(self, query: str, benefits: str = None, source: str = "text") -> List[Dict]:
        """Search for government schemes with preprocessing"""
        search_query = f"government scheme {query}"
        if benefits:
            search_query += f" {benefits}"
        
        results = await self.search_similar(search_query, top_k=5, source=source)
        return [r for r in results if r['metadata'].get('category') == 'scheme']
    
    def save_index(self, filename: str = "agriculture_index.faiss") -> None:
        """Save FAISS index to disk"""
        try:
            faiss.write_index(self.index, filename)
            
            # Save document store with enhanced metadata
            metadata = {
                'documents': self.document_store,
                'model_info': self.embedding_generator.get_model_info(),
                'version': '2.0'
            }
            
            with open(f"{filename}.metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"💾 Saved enhanced vector index to {filename}")
        except Exception as e:
            print(f"Error saving index: {e}")
    
    async def load_index(self, filename: str = "agriculture_index.faiss") -> None:
        """Load FAISS index from disk"""
        try:
            if os.path.exists(filename):
                self.index = faiss.read_index(filename)
                
                # Load document store
                metadata_file = f"{filename}.metadata.json"
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    self.document_store = metadata.get('documents', [])
                    
                    # Check compatibility
                    saved_model_info = metadata.get('model_info', {})
                    current_model_info = self.embedding_generator.get_model_info()
                    
                    if saved_model_info.get('model_name') != current_model_info.get('model_name'):
                        print(f"⚠️  Model mismatch: saved={saved_model_info.get('model_name')}, current={current_model_info.get('model_name')}")
                        print("   Rebuilding knowledge base...")
                        await self.build_agriculture_knowledge_base()
                        return
                
                print(f"📂 Loaded enhanced vector index from {filename}")
            else:
                print(f"Index file {filename} not found. Building new index...")
                await self.build_agriculture_knowledge_base()
        except Exception as e:
            print(f"Error loading index: {e}")
            print("Building new knowledge base...")
            await self.build_agriculture_knowledge_base()
