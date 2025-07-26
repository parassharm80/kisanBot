from ..whatsapp.client import AsyncWhatsAppClient
import os
from google import auth


whatsapp_client = AsyncWhatsAppClient(
    phone_number_id='779353605250568',
    bearer_token='EAAJQPoXkZCoMBPOiAbtkPfT0HW2E3UxHAYpZB47th3qLJXkbpQYEk3yoKCFwaqB3y8wwAZBelgFEZCUiZA0rPw6cRx60d6KD8egvWbbY1YJGpq4wQra7pjokoff6mtnJRhkGY7twKAFUcvwdeezoKEKeP4jVcvZAVxM557ZBTSmZBOJLbcEZAbEQ6Juc7I2POnq81ZA3A0Q88zZAgXUT69WEWU7Q67zjycv1487hjNrEZB8uzV4qzDHo85G55c9ciMXdGmEZD',
    reuse_client=True
)

#publisher
from google.cloud import pubsub_v1
from google.oauth2 import service_account

if os.environ.get("ENV") == "local":
    SERVICE_ACCOUNT_KEY_FILE = os.environ.get("SERVICE_ACCOUNT_KEY_FILE")
    API_KEY = os.environ.get("API_KEY")
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

