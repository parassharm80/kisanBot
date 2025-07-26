from ..whatsapp.client import AsyncWhatsAppClient
import os
from google import auth
from dotenv import load_dotenv

# load environment variables from .env file
current_dir = os.path.dirname(os.path.abspath(__file__))
environment_path = os.path.join(current_dir, '..', 'keys.env')
environment_path = os.path.normpath(environment_path)
print(f"Loading environment variables from: {environment_path}")
if os.path.exists(environment_path):
    load_dotenv(environment_path)
else:
    print(f"Warning: Environment file not found at {environment_path}")
    
whatsapp_client = AsyncWhatsAppClient(
    phone_number_id='779353605250568',
    bearer_token=os.environ.get("WHATSAPP_AUTH_TOKEN"),
    reuse_client=True
)

#publisher
from google.cloud import pubsub_v1
from google.oauth2 import service_account

API_KEY = os.environ.get("API_KEY", "")
if os.environ.get("ENV") == "local":
    SERVICE_ACCOUNT_KEY_FILE = os.environ.get("SERVICE_ACCOUNT_KEY_FILE")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)

    project_id = os.environ.get("PROJECT_ID")

else:
    credentials, project_id = auth.default()


# Replace with the actual path to your service account key file

# projects/serene-flare-466616-m5/subscriptions/bot_messages-sub

topic_id = "bot_messages"
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(project_id, topic_id)

# speech to text gemini client
import google.generativeai as genai
genai.configure(api_key=API_KEY)
speech_model = genai.GenerativeModel('gemini-2.5-flash')

# image model
image_model = genai.GenerativeModel('gemini-2.5-flash')

# orchestrator model
orch_model = genai.GenerativeModel('gemini-2.5-flash')

# online model
online_model = genai.GenerativeModel('gemini-2.5-flash')

# offline model
offline_model = genai.GenerativeModel('gemini-2.5-flash')

# Document db firestore
from google.cloud import firestore
db = firestore.AsyncClient.from_service_account_json(SERVICE_ACCOUNT_KEY_FILE)
message_collection = db.collection('messages')

