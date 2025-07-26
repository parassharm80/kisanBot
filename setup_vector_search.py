#!/usr/bin/env python3
"""
Setup script for configuring and populating Vertex AI Vector Search
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the project root to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

async def setup_vector_search():
    """Setup and populate Vector Search with agricultural knowledge"""
    
    print("🚀 Vertex AI Vector Search Setup\n")
    
    # Use hardcoded values from your file or environment variables
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'serene-flare-466616-m5')
    endpoint_id = os.getenv('VECTOR_SEARCH_ENDPOINT_ID', '8844614470341754880')
    deployed_index_id = os.getenv('VECTOR_SEARCH_DEPLOYED_INDEX_ID', 'deploy_kisan_1753377086327')
    
    print("📋 Configuration Check:")
    print(f"   Project ID: {project_id}")
    print(f"   Endpoint ID: {endpoint_id}")
    print(f"   Deployed Index ID: {deployed_index_id}")
    
    try:
        # Import with proper path handling
        from src.flows.vertex_ai_vector_search import VertexAIVectorSearch
        
        # Initialize Vector Search client with your configuration
        vector_search = VertexAIVectorSearch(
            project_id=project_id,
            index_endpoint_id=endpoint_id,
            deployed_index_id=deployed_index_id,
            similarity_metric="DOT_PRODUCT"
        )
        
        # Test connection
        print("\n🔌 Testing Vector Search Connection...")
        success = await vector_search.initialize_endpoint()
        
        if not success:
            print("\n❌ Vector Search connection failed.")
            print("\n🔧 Troubleshooting Steps:")
            print("1. Verify your Vector Search endpoint exists in Google Cloud Console")
            print("2. Check that your service account has proper permissions:")
            print("   - aiplatform.endpoints.predict")
            print("   - aiplatform.indexEndpoints.queryVectors") 
            print("3. Ensure the endpoint is in the correct region (us-central1)")
            print("4. Make sure you have proper authentication set up")
            return False
        
        # Get current status
        status = vector_search.get_status()
        print("\n📊 Vector Search Status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Ask if user wants to populate knowledge base
        if input("\n🌾 Populate AND upload Vector Search knowledge base? (y/n): ").lower().startswith('y'):
            print("\n📚 Populating and uploading to Vector Search...")
            
            # Option to specify custom bucket
            custom_bucket = input("📦 Enter Cloud Storage bucket name (or press Enter for auto-generated): ").strip()
            bucket_name = custom_bucket if custom_bucket else None
            
            success = await vector_search.populate_and_upload_knowledge(bucket_name)
            
            if success:
                print("✅ Knowledge base populated and uploaded successfully!")
                print("🎉 Your Vector Search index should now be ready!")
            else:
                print("❌ Failed to populate or upload knowledge base")
                print("💡 Try the manual upload process or check your Google Cloud permissions")
        
        # Test search functionality (if index is already populated)
        if input("\n🔍 Test search functionality? (y/n): ").lower().startswith('y'):
            print("\n🧪 Testing Search Functionality...")
            
            test_queries = [
                ("wheat disease brown spots", "disease"),
                ("rice market price selling time", "market"), 
                ("government crop insurance scheme", "scheme")
            ]
            
            for query, category in test_queries:
                print(f"\n🔎 Searching: '{query}'")
                try:
                    results = await vector_search.search_similar_vectors(query, top_k=2)
                    
                    if results:
                        for i, result in enumerate(results, 1):
                            print(f"   {i}. {result['text'][:80]}...")
                            print(f"      Similarity: {result.get('similarity_score', 0):.4f}")
                            print(f"      Category: {result['metadata'].get('category', 'unknown')}")
                    else:
                        print("   No results found (index may be empty)")
                except Exception as e:
                    print(f"   Search failed: {e}")
        
        print(f"\n🎉 Vector Search setup complete!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Make sure you're running this script from the kisanBot directory")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

async def list_vector_search_resources():
    """List available Vector Search resources in the project"""
    
    print("📋 Listing Vector Search Resources...\n")
    
    try:
        from google.cloud import aiplatform
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'serene-flare-466616-m5')
        region = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        
        aiplatform.init(project=project_id, location=region)
        
        # List Index Endpoints
        print("🔗 Index Endpoints:")
        try:
            endpoints = aiplatform.MatchingEngineIndexEndpoint.list()
            for endpoint in endpoints:
                print(f"   📍 {endpoint.display_name}")
                print(f"      ID: {endpoint.name.split('/')[-1]}")
                print(f"      Region: {endpoint.name.split('/')[3]}")
                
                # List deployed indexes
                if hasattr(endpoint, 'deployed_indexes') and endpoint.deployed_indexes:
                    print(f"      Deployed Indexes:")
                    for idx in endpoint.deployed_indexes:
                        print(f"        - {idx.id}")
                print()
        except Exception as e:
            print(f"   Error listing endpoints: {e}")
        
        # List Indexes
        print("📚 Vector Indexes:")
        try:
            indexes = aiplatform.MatchingEngineIndex.list()
            for index in indexes:
                print(f"   📖 {index.display_name}")
                print(f"      ID: {index.name.split('/')[-1]}")
                print(f"      Dimensions: {getattr(index, 'config', {}).get('dimensions', 'unknown')}")
                print()
        except Exception as e:
            print(f"   Error listing indexes: {e}")
            
    except Exception as e:
        print(f"❌ Error accessing Vector Search resources: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure you have proper Google Cloud authentication")
        print("2. Verify your service account has Vector Search permissions")
        print("3. Check that Vector Search API is enabled in your project")

def generate_env_template():
    """Generate .env file template with user's Vector Search resources"""
    
    print("📝 Generating .env template...\n")
    
    # Use current hardcoded values as defaults
    project_id = input("Enter your Google Cloud Project ID [serene-flare-466616-m5]: ").strip() or "serene-flare-466616-m5"
    region = input("Enter your region [us-central1]: ").strip() or "us-central1"
    endpoint_id = input("Enter your Vector Search Endpoint ID [8844614470341754880]: ").strip() or "8844614470341754880"
    deployed_index_id = input("Enter your Deployed Index ID [deploy_kisan_1753377086327]: ").strip() or "deploy_kisan_1753377086327"
    
    env_content = f"""# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT={project_id}
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account.json

# Vertex AI Vector Search Configuration
VECTOR_SEARCH_ENDPOINT_ID={endpoint_id}
VECTOR_SEARCH_DEPLOYED_INDEX_ID={deployed_index_id}
VECTOR_SEARCH_SIMILARITY_METRIC=DOT_PRODUCT

# WhatsApp Business API (configure when ready)
WHATSAPP_VERIFY_TOKEN=your-verify-token
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id

# Optional APIs
COMMODITY_API_KEY=your-commodity-api-key

# Application Settings
DEBUG=true
PORT=8000
ENVIRONMENT=development
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created!")
    print("🔧 Next steps:")
    print("1. Add your service account JSON file path")
    print("2. Run: python setup_vector_search.py")

async def test_embedding_generation():
    """Test just the embedding generation without Vector Search"""
    
    print("🧪 Testing Embedding Generation Only\n")
    
    try:
        from src.flows.vertex_ai_emb_gen import VertexAIEmbeddingGenerator
        
        # Initialize embedding generator
        generator = VertexAIEmbeddingGenerator(
            project_id="serene-flare-466616-m5"
        )
        
        # Test different input types
        test_texts = {
            "text": "Rice plants with brown spots on leaves",
            "speech": "uh rice plants with... you know, brown spots on leaves",
            "ocr": "R1ce p1ants w1th br0wn sp0ts 0n le4ves"
        }
        
        print("📝 Testing Different Input Sources:")
        
        for source, text in test_texts.items():
            print(f"\n{source.upper()} INPUT:")
            print(f"Raw: {text}")
            
            # Clean text
            clean_text = generator.preprocess(text, source)
            print(f"Cleaned: {clean_text}")
            
            # Generate embedding
            embedding = generator.embed_text(text, source)
            print(f"Embedding: {len(embedding)} dimensions")
            print(f"First 5 values: {embedding[:5]}")
        
        print("\n✅ Embedding generation working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False

async def main():
    """Main setup function"""
    
    choice = input("""
🚀 Vector Search Setup Options:

1. Setup and populate Vector Search
2. List Vector Search resources  
3. Generate new .env template
4. Test embedding generation only

Choose option (1-4): """).strip()
    
    if choice == "1":
        await setup_vector_search()
    elif choice == "2":
        await list_vector_search_resources()
    elif choice == "3":
        generate_env_template()
    elif choice == "4":
        await test_embedding_generation()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main()) 