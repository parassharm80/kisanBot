from src.whatsapp.client import AsyncWhatsAppClient
import os
from google import auth
from dotenv import load_dotenv
from google.cloud import firestore

# load environment variables from .env file
current_dir = os.path.dirname(os.path.abspath(__file__))
environment_path = os.path.join(current_dir, 'keys.env')
environment_path = os.path.normpath(environment_path)
print(f"Loading environment variables from: {environment_path}")
if os.path.exists(environment_path):
    load_dotenv(environment_path)
else:
    print(f"Warning: Environment file not found at {environment_path}")

_whatsapp_client = None
def get_whatsapp_client():
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = AsyncWhatsAppClient(
            phone_number_id='779353605250568',
            bearer_token=os.environ.get("WHATSAPP_AUTH_TOKEN"),
            reuse_client=True
        )
    print(f"Current token {_whatsapp_client._bearer_token}")
    return _whatsapp_client

async def update_whatsapp(token: str):
    """
    Update the WhatsApp bearer token and reinitialize the client.
    """
    global _whatsapp_client  # Clear the existing client
    print(f"Updating WhatsApp bearer token to: {token}")
    os.environ["WHATSAPP_AUTH_TOKEN"] = token

    # Close old client if it exists
    if _whatsapp_client is not None:
        print("Closing existing WhatsApp client...")
        await _whatsapp_client._close()
        del _whatsapp_client
        
    _whatsapp_client = None  # Reset the client to None
    # Create new client
    _whatsapp_client = AsyncWhatsAppClient(
        phone_number_id='779353605250568',
        bearer_token=token,
        reuse_client=True
    )
    
#publisher
from google.cloud import pubsub_v1
from google.oauth2 import service_account

API_KEY = os.environ.get("API_KEY", "")
if os.environ.get("ENV") == "local":
    SERVICE_ACCOUNT_KEY_FILE = os.environ.get("SERVICE_ACCOUNT_KEY_FILE")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)
    db = firestore.AsyncClient.from_service_account_json(SERVICE_ACCOUNT_KEY_FILE)

    project_id = os.environ.get("PROJECT_ID")

else:
    credentials, project_id = auth.default()
    db = firestore.AsyncClient()


# projects/serene-flare-466616-m5/subscriptions/bot_messages-sub

topic_id = "bot_messages"
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(project_id, topic_id)

from google import genai
# orchestrator model
orch_model = genai.Client(api_key=API_KEY)

# speech to text gemini client
speech_model = genai.Client(api_key=API_KEY)

# image model
image_model = genai.Client(api_key=API_KEY)

# online model
online_model = genai.Client(api_key=API_KEY)

# offline model
offline_model = genai.Client(api_key=API_KEY)

# Document db firestore
message_collection = db.collection('messages')

