import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from google.cloud import aiplatform
from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint
from google.auth import load_credentials_from_file
from .vertex_ai_emb_gen import get_embedding_generator
from .firestore_client import FirestoreClient
import numpy as np
from google.cloud import storage
import time

class VertexAIVectorSearch:
    """
    Production-ready Vector Search using Google Cloud Vertex AI Vector Search
    (formerly Vertex AI Matching Engine)
    """
    
    def __init__(self, 
                 project_id: str = "serene-flare-466616-m5",
                 region: str = "us-central1",
                 index_endpoint_id: str = "8844614470341754880",
                 deployed_index_id: str = "deploy_kisan_1753377086327",
                 similarity_metric: str = "DOT_PRODUCT",
                 credentials_path: str = "/Users/mahima.dubey/Downloads/serene-flare-466616-m5-6ecc2e02985d.json"):
        """
        Initialize Vertex AI Vector Search client
        
        Args:
            project_id: Google Cloud Project ID
            region: Google Cloud region
            index_endpoint_id: Your Vector Search endpoint ID
            deployed_index_id: Your deployed index ID
            similarity_metric: DOT_PRODUCT, COSINE_DISTANCE, or SQUARED_L2_DISTANCE
            credentials_path: Path to Google Cloud service account JSON file
        """
        
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.region = region
        self.index_endpoint_id = index_endpoint_id or os.getenv('VECTOR_SEARCH_ENDPOINT_ID')
        self.deployed_index_id = deployed_index_id or os.getenv('VECTOR_SEARCH_DEPLOYED_INDEX_ID')
        self.similarity_metric = similarity_metric.upper()
        self.credentials_path = credentials_path
        
        # Set up credentials from the provided path
        credentials = None
        if os.path.exists(self.credentials_path):
            credentials, _ = load_credentials_from_file(self.credentials_path)
            print(f"🔐 Loaded credentials from: {self.credentials_path}")
        else:
            print(f"⚠️  Credentials file not found: {self.credentials_path}")
            print("   Falling back to environment credentials")
        
        # Initialize Vertex AI with credentials
        if credentials:
            aiplatform.init(project=self.project_id, location=self.region, credentials=credentials)
        else:
            aiplatform.init(project=self.project_id, location=self.region)
        
        # Initialize embedding generator (your enhanced one)
        self.embedding_generator = get_embedding_generator(project_id, region)
        
        # Get model info
        model_info = self.embedding_generator.get_model_info()
        self.dimension = model_info['dimensionality']  # 3072 for gemini-embedding-001
        
        # Initialize Firestore for metadata storage
        if credentials:
            self.firestore_client = FirestoreClient(project_id, credentials=credentials)
        else:
            self.firestore_client = FirestoreClient(project_id)
        
        # Vector Search endpoint
        self.endpoint = None
        self.index = None
        
        print(f"🔍 Vertex AI Vector Search initialized:")
        print(f"   Project: {self.project_id}")
        print(f"   Region: {self.region}")
        print(f"   Endpoint ID: {self.index_endpoint_id}")
        print(f"   Index ID: {self.deployed_index_id}")
        print(f"   Similarity Metric: {self.similarity_metric}")
        print(f"   Embedding Model: {model_info['model_name']} ({self.dimension}D)")
        print(f"   Credentials: File-based ({self.credentials_path})")
        
        # Warn about dot product requirements
        if self.similarity_metric == "DOT_PRODUCT":
            print("⚠️  DOT_PRODUCT similarity requires normalized embeddings for optimal results")
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize embedding vector for dot product similarity
        
        For dot product similarity, normalized vectors give equivalent results to cosine similarity
        but with better performance characteristics.
        """
        if self.similarity_metric == "DOT_PRODUCT":
            # Convert to numpy array
            emb_array = np.array(embedding, dtype=np.float32)
            
            # L2 normalize (unit vector)
            norm = np.linalg.norm(emb_array)
            if norm > 0:
                emb_array = emb_array / norm
            
            return emb_array.tolist()
        
        return embedding
    
    def _convert_distance_to_similarity(self, distance: float) -> float:
        """
        Convert distance score to similarity score based on metric
        
        Args:
            distance: Distance returned by Vector Search
            
        Returns:
            Similarity score (higher = more similar)
        """
        if self.similarity_metric == "DOT_PRODUCT":
            # For normalized vectors with dot product, distance is actually negative dot product
            # So similarity = -distance (higher dot product = higher similarity)
            return -distance
        elif self.similarity_metric == "COSINE_DISTANCE":
            # Cosine distance = 1 - cosine similarity
            # So similarity = 1 - distance
            return 1.0 - distance
        elif self.similarity_metric == "SQUARED_L2_DISTANCE":
            # For L2 distance, convert to similarity (smaller distance = higher similarity)
            # Using exponential decay: similarity = exp(-distance)
            return np.exp(-distance)
        else:
            # Default: assume smaller distance = higher similarity
            return 1.0 / (1.0 + distance)
    
    async def initialize_endpoint(self):
        """Initialize the Vector Search endpoint and index"""
        try:
            if not self.index_endpoint_id:
                raise ValueError("VECTOR_SEARCH_ENDPOINT_ID not provided. Please set it in environment variables.")
            
            # Get the endpoint
            endpoint_name = f"projects/{self.project_id}/locations/{self.region}/indexEndpoints/{self.index_endpoint_id}"
            self.endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
            
            print(f"✅ Connected to Vector Search endpoint: {self.index_endpoint_id}")
            
            # List deployed indexes to verify
            deployed_indexes = self.endpoint.deployed_indexes
            print(f"📋 Deployed indexes: {[idx.id for idx in deployed_indexes]}")
            
            if self.deployed_index_id:
                # Verify the deployed index exists
                if any(idx.id == self.deployed_index_id for idx in deployed_indexes):
                    print(f"✅ Found deployed index: {self.deployed_index_id}")
                else:
                    print(f"⚠️  Deployed index '{self.deployed_index_id}' not found")
                    print(f"   Available indexes: {[idx.id for idx in deployed_indexes]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing endpoint: {e}")
            return False
    
    async def add_embeddings_batch(self, 
                                   documents: List[Dict[str, Any]], 
                                   source: str = "text") -> bool:
        """
        Add multiple documents to Vector Search index
        
        Args:
            documents: List of documents with 'id', 'text', and 'metadata'
            source: Source type for preprocessing
            
        Returns:
            Success status
        """
        try:
            if not self.endpoint:
                success = await self.initialize_endpoint()
                if not success:
                    return False
            
            # Prepare data for Vector Search
            embeddings = []
            doc_ids = []
            
            print(f"🔄 Generating embeddings for {len(documents)} documents...")
            print(f"   Similarity metric: {self.similarity_metric}")
            
            for doc in documents:
                doc_id = doc['id']
                text = doc['text']
                metadata = doc.get('metadata', {})
                
                # Generate embedding using your enhanced generator
                raw_embedding = self.embedding_generator.embed_text(text, source)
                
                # Normalize if using dot product similarity
                normalized_embedding = self._normalize_embedding(raw_embedding)
                
                embeddings.append(normalized_embedding)
                doc_ids.append(doc_id)
                
                # Store metadata in Firestore for retrieval
                doc_metadata = {
                    'id': doc_id,
                    'text': text,
                    'metadata': metadata,
                    'source': source,
                    'preprocessed_text': self.embedding_generator.preprocess(text, source),
                    'embedding_dimension': len(normalized_embedding),
                    'normalized': self.similarity_metric == "DOT_PRODUCT"
                }
                
                # Store in Firestore collection 'vector_documents'
                self.firestore_client.db.collection('vector_documents').document(doc_id).set(doc_metadata)
            
            # Convert to numpy array format expected by Vector Search
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            print(f"📤 Prepared {len(embeddings)} embeddings for Vector Search...")
            print(f"   Embeddings shape: {embeddings_array.shape}")
            print(f"   Normalized: {self.similarity_metric == 'DOT_PRODUCT'}")
            print(f"   Metadata stored in Firestore")
            
            # For production deployment, you would typically:
            # 1. Save embeddings to Cloud Storage in JSONL format
            # 2. Use the Vector Search batch import API
            # 3. Monitor the import job status
            
            # Example format for batch upload:
            upload_format = []
            for i, (doc_id, embedding) in enumerate(zip(doc_ids, embeddings)):
                upload_format.append({
                    "id": doc_id,
                    "embedding": embedding
                })
            
            # Save to file for manual upload (production approach)
            with open(f"vector_upload_{self.similarity_metric.lower()}.jsonl", "w") as f:
                for item in upload_format:
                    f.write(json.dumps(item) + "\n")
            
            print(f"💾 Saved embeddings to vector_upload_{self.similarity_metric.lower()}.jsonl")
            print(f"🔧 For production: Upload this file to Cloud Storage and use Vector Search batch import")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding embeddings: {e}")
            return False
    
    async def search_similar_vectors(self, 
                                     query: str, 
                                     top_k: int = 5,
                                     source: str = "text") -> List[Dict[str, Any]]:
        """
        Search for similar vectors using Vertex AI Vector Search
        
        Args:
            query: Search query
            top_k: Number of results to return
            source: Query source type
            
        Returns:
            List of similar documents with metadata
        """
        try:
            if not self.endpoint:
                success = await self.initialize_endpoint()
                if not success:
                    return []
            
            # Generate query embedding
            raw_query_embedding = self.embedding_generator.embed_text(query, source)
            
            # Normalize for consistency with stored embeddings
            query_embedding = self._normalize_embedding(raw_query_embedding)
            
            print(f"🔍 Searching for: '{query}' (source: {source})")
            print(f"   Similarity metric: {self.similarity_metric}")
            print(f"   Query embedding normalized: {self.similarity_metric == 'DOT_PRODUCT'}")
            
            # Perform vector search
            if self.deployed_index_id:
                response = self.endpoint.find_neighbors(
                    deployed_index_id=self.deployed_index_id,
                    queries=[query_embedding],
                    num_neighbors=top_k
                )
                
                results = []
                
                # Process search results
                for neighbor_list in response:
                    for neighbor in neighbor_list:
                        doc_id = neighbor.id
                        distance = neighbor.distance
                        
                        # Convert distance to similarity based on metric
                        similarity_score = self._convert_distance_to_similarity(distance)
                        
                        # Retrieve metadata from Firestore
                        doc_ref = self.firestore_client.db.collection('vector_documents').document(doc_id)
                        doc_data = doc_ref.get()
                        
                        if doc_data.exists:
                            result_data = doc_data.to_dict()
                            result_data['similarity_score'] = similarity_score
                            result_data['raw_distance'] = distance
                            result_data['similarity_metric'] = self.similarity_metric
                            results.append(result_data)
                
                # Sort by similarity score (higher = more similar)
                results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
                
                print(f"✅ Found {len(results)} similar documents")
                if results:
                    print(f"   Best match similarity: {results[0]['similarity_score']:.4f}")
                
                return results
            else:
                print("❌ No deployed index ID configured")
                return []
            
        except Exception as e:
            print(f"❌ Error searching vectors: {e}")
            return []
    
    async def populate_agriculture_knowledge(self) -> bool:
        """Populate Vector Search with agricultural knowledge base"""
        
        # Enhanced agricultural knowledge base
        knowledge_documents = [
            {
                'id': 'agri_disease_001',
                'text': 'Leaf blight in rice crops shows brown spots on leaves with yellow halos. Treatment includes copper fungicides and proper drainage.',
                'metadata': {
                    'category': 'disease',
                    'crop': 'rice',
                    'symptoms': ['brown spots', 'yellow halos', 'leaf damage'],
                    'treatment': ['copper fungicides', 'drainage']
                }
            },
            {
                'id': 'agri_disease_002',
                'text': 'Powdery mildew appears as white powdery coating on leaves. Remove affected parts and apply sulfur-based fungicides.',
                'metadata': {
                    'category': 'disease',
                    'crop': 'general',
                    'symptoms': ['white powder', 'leaf coating'],
                    'treatment': ['sulfur fungicides', 'remove affected parts']
                }
            },
            {
                'id': 'agri_disease_003',
                'text': 'Tomato early blight causes dark brown spots with concentric rings on older leaves. Use fungicides and improve air circulation.',
                'metadata': {
                    'category': 'disease',
                    'crop': 'tomato',
                    'symptoms': ['dark spots', 'concentric rings'],
                    'treatment': ['fungicides', 'air circulation']
                }
            },
            {
                'id': 'agri_market_001',
                'text': 'Best time to sell wheat is during harvest season March-April when demand is high and prices peak.',
                'metadata': {
                    'category': 'market',
                    'crop': 'wheat',
                    'season': 'harvest',
                    'months': ['March', 'April']
                }
            },
            {
                'id': 'agri_market_002',
                'text': 'Rice prices typically rise during monsoon delays. Store properly in moisture-free conditions for better rates.',
                'metadata': {
                    'category': 'market',
                    'crop': 'rice',
                    'season': 'monsoon',
                    'storage': 'moisture-free'
                }
            },
            {
                'id': 'agri_scheme_001',
                'text': 'PM-KISAN scheme provides direct income support of Rs 6000 per year to farmer families. Apply online with Aadhaar.',
                'metadata': {
                    'category': 'scheme',
                    'name': 'PM-KISAN',
                    'benefits': 'income support',
                    'amount': '6000',
                    'application': 'online'
                }
            },
            {
                'id': 'agri_scheme_002',
                'text': 'Pradhan Mantri Fasal Bima Yojana offers crop insurance at subsidized rates. Premium is only 2% for Kharif crops.',
                'metadata': {
                    'category': 'scheme',
                    'name': 'PMFBY',
                    'benefits': 'crop insurance',
                    'premium': '2%',
                    'season': 'Kharif'
                }
            },
            {
                'id': 'agri_fertilizer_001',
                'text': 'Apply nitrogen fertilizer in split doses for wheat - 1/3 at sowing, 1/3 at first irrigation, 1/3 at second irrigation.',
                'metadata': {
                    'category': 'fertilizer',
                    'crop': 'wheat',
                    'type': 'nitrogen',
                    'application': 'split doses'
                }
            },
            {
                'id': 'agri_pest_001',
                'text': 'Aphids on cotton can be controlled using neem oil spray or releasing ladybird beetles as biological control.',
                'metadata': {
                    'category': 'pest',
                    'crop': 'cotton',
                    'pest': 'aphids',
                    'control': ['neem oil', 'biological control']
                }
            },
            {
                'id': 'agri_weather_001',
                'text': 'During monsoon season, ensure proper drainage for rice crops to prevent root rot and fungal diseases.',
                'metadata': {
                    'category': 'weather',
                    'season': 'monsoon',
                    'crop': 'rice',
                    'prevention': ['drainage', 'root rot', 'fungal diseases']
                }
            }
        ]
        
        print(f"🌾 Populating Vector Search with {len(knowledge_documents)} agricultural documents...")
        print(f"   Using {self.similarity_metric} similarity metric")
        
        success = await self.add_embeddings_batch(knowledge_documents, source="text")
        
        if success:
            print(f"✅ Agricultural knowledge base prepared successfully!")
            print(f"🔧 Next step: Upload the generated JSONL file to your Vector Search index")
        else:
            print(f"❌ Failed to prepare knowledge base")
        
        return success
    
    async def search_diseases(self, symptoms: str, crop: str = None, source: str = "text") -> List[Dict]:
        """Search for diseases based on symptoms"""
        query = f"disease symptoms {symptoms}"
        if crop:
            query += f" in {crop} crop"
        
        results = await self.search_similar_vectors(query, top_k=3, source=source)
        return [r for r in results if r['metadata'].get('category') == 'disease']
    
    async def search_market_info(self, crop: str, query_type: str = "price", source: str = "text") -> List[Dict]:
        """Search for market information"""
        query = f"{crop} {query_type} market information selling"
        results = await self.search_similar_vectors(query, top_k=3, source=source)
        return [r for r in results if r['metadata'].get('category') == 'market']
    
    async def search_schemes(self, query: str, benefits: str = None, source: str = "text") -> List[Dict]:
        """Search for government schemes"""
        search_query = f"government scheme {query}"
        if benefits:
            search_query += f" {benefits}"
        
        results = await self.search_similar_vectors(search_query, top_k=5, source=source)
        return [r for r in results if r['metadata'].get('category') == 'scheme']
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Vector Search status"""
        return {
            'project_id': self.project_id,
            'region': self.region,
            'endpoint_id': self.index_endpoint_id,
            'deployed_index_id': self.deployed_index_id,
            'similarity_metric': self.similarity_metric,
            'endpoint_connected': self.endpoint is not None,
            'embedding_model': self.embedding_generator.get_model_info(),
            'normalization_enabled': self.similarity_metric == "DOT_PRODUCT",
            'credentials_path': self.credentials_path,
            'credentials_type': 'file-based'
        } 

    async def upload_embeddings_to_index(self, jsonl_file_path: str, bucket_name: str = None) -> bool:
        """
        Upload embeddings from JSONL file to Vector Search index
        
        Args:
            jsonl_file_path: Path to the JSONL file with embeddings
            bucket_name: Cloud Storage bucket name (optional, will create temp bucket if not provided)
            
        Returns:
            Success status
        """
        try:
            # Initialize storage client
            storage_client = storage.Client(project=self.project_id)
            
            # Create or use existing bucket
            if not bucket_name:
                bucket_name = f"{self.project_id}-vector-embeddings"
            
            try:
                bucket = storage_client.create_bucket(bucket_name, location=self.region)
                print(f"📦 Created bucket: {bucket_name}")
            except Exception:
                bucket = storage_client.bucket(bucket_name)
                print(f"📦 Using existing bucket: {bucket_name}")
            
            # Upload JSONL file to Cloud Storage
            blob_name = f"embeddings/{os.path.basename(jsonl_file_path)}"
            blob = bucket.blob(blob_name)
            
            print(f"📤 Uploading {jsonl_file_path} to gs://{bucket_name}/{blob_name}...")
            blob.upload_from_filename(jsonl_file_path)
            
            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            print(f"✅ Uploaded to: {gcs_uri}")
            
            # Get the index for batch import
            index_name = f"projects/{self.project_id}/locations/{self.region}/indexes/{self.index_endpoint_id.replace('indexEndpoints/', 'indexes/')}"
            
            try:
                index = aiplatform.MatchingEngineIndex(index_name)
                print(f"📋 Found index: {index.name}")
            except Exception as e:
                print(f"❌ Could not find index: {e}")
                print(f"💡 You may need to manually import using gcloud:")
                print(f"   gcloud ai indexes update YOUR_INDEX_ID \\")
                print(f"     --region={self.region} \\")
                print(f"     --project={self.project_id} \\")
                print(f"     --upsert-datapoints-uri={gcs_uri}")
                return False
            
            # Start batch import operation
            print(f"🔄 Starting batch import to Vector Search index...")
            operation = index.upsert_datapoints(
                datapoints_source_uri=gcs_uri
            )
            
            print(f"⏳ Import operation started: {operation.operation.name}")
            print(f"   This may take several minutes to complete...")
            
            # Monitor the operation (optional - can run in background)
            if input("🤔 Wait for import to complete? (y/n): ").lower().startswith('y'):
                print("⏳ Waiting for import to complete...")
                result = operation.result(timeout=1800)  # 30 minutes timeout
                print(f"✅ Import completed successfully!")
                return True
            else:
                print(f"🔄 Import running in background. Check status in Google Cloud Console.")
                return True
                
        except Exception as e:
            print(f"❌ Error uploading embeddings: {e}")
            return False

    async def populate_and_upload_knowledge(self, bucket_name: str = None) -> bool:
        """
        Complete workflow: populate knowledge base and upload to Vector Search
        
        Args:
            bucket_name: Cloud Storage bucket name (optional)
            
        Returns:
            Success status
        """
        print("🌾 Starting complete Vector Search setup...")
        
        # Step 1: Populate knowledge base (creates JSONL file)
        success = await self.populate_agriculture_knowledge()
        if not success:
            return False
        
        # Step 2: Upload to Vector Search index
        jsonl_file = f"vector_upload_{self.similarity_metric.lower()}.jsonl"
        
        if os.path.exists(jsonl_file):
            print(f"\n📤 Uploading embeddings to Vector Search...")
            upload_success = await self.upload_embeddings_to_index(jsonl_file, bucket_name)
            
            if upload_success:
                print(f"\n🎉 Complete! Your Vector Search index should now have data.")
                print(f"   Try searching again in a few minutes.")
            else:
                print(f"\n⚠️  Upload failed. You may need to manually import the JSONL file.")
            
            return upload_success
        else:
            print(f"❌ JSONL file not found: {jsonl_file}")
            return False 