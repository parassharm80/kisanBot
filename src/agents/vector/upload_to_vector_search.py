import json
import os
import sys
from google.cloud import aiplatform
from google.auth import load_credentials_from_file

from src.chat_app.dependency_setup import SERVICE_ACCOUNT_KEY_FILE, project_id

def upload_embeddings():
    # Configuration
    project_id = project_id
    region = "us-central1"
    index_id = "1593590371856678912"
    credentials_path = SERVICE_ACCOUNT_KEY_FILE

    # Load credentials
    print("🔐 Loading credentials...")
    credentials, _ = load_credentials_from_file(credentials_path)

    # Initialize Vertex AI
    aiplatform.init(project=project_id, location=region, credentials=credentials)

    # Load embeddings data
    print("📄 Loading embeddings data...")
    with open('vector_upload_dot_product.jsonl', 'r') as f:
        lines = f.readlines()

    # Prepare datapoints in the format expected by the API
    datapoints = []
    for line in lines:
        if line.strip():
            data = json.loads(line)
            # Create datapoint in the format expected by the API
            datapoint = {
                "datapoint_id": data['id'],
                "feature_vector": data['embedding']
            }
            datapoints.append(datapoint)

    print(f"📤 Uploading {len(datapoints)} datapoints to Vector Search index...")

    # Get the index
    index_name = f"projects/{project_id}/locations/{region}/indexes/{index_id}"
    index = aiplatform.MatchingEngineIndex(index_name)

    print(f"📋 Found index: {index.display_name}")

    # Upload datapoints
    print("🔄 Starting upload operation...")
    operation = index.upsert_datapoints(datapoints=datapoints)

    print(f"⏳ Upload operation started: {operation.operation.name}")
    print("   Waiting for completion...")

    # Wait for completion
    result = operation.result(timeout=1800)  # 30 minutes timeout

    print("✅ Upload completed successfully!")
    print(f"🎉 Your Vector Search index now contains {len(datapoints)} agricultural documents!")

    return True

if __name__ == "__main__":
    try:
        success = upload_embeddings()
        if success:
            print("\n🌾 Agricultural knowledge base is now ready for searching!")
            sys.exit(0)
        else:
            print("\n❌ Upload failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 