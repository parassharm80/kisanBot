from ..whatsapp.client import AsyncWhatsAppClient

whatsapp_client = AsyncWhatsAppClient(
    phone_number_id='779353605250568',
    bearer_token='EAAJQPoXkZCoMBPAoFIRk7kFZBHZBq6ezlt0nyy5Aj4JxSIZATnbKv5ZBJZAFcPrOv43bfh4167SwZCXL3YWsWAlAK1X0g0F8UXdV55QnDwZCBp4nXZCjFjwMw6Sw9BXwXhAjkZAaEEWWmL3fILMiaMGHT2bRqZBZBmHCHWisi55bTgFRFXFXYbCkrrKcwHZBo2Ypem7ycODZCk8Ww7UxUGbDi4kCh4RT76yZC5kZBgkufx9JoVR3pa3l68aBY7pLZCmQ2kAZDZD',
    reuse_client=True
)

#publisher
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# Replace with the actual path to your service account key file
SERVICE_ACCOUNT_KEY_FILE = "/Users/parassharma/Downloads/serene-flare-466616-m5-ced346076763.json"

# projects/serene-flare-466616-m5/subscriptions/bot_messages-sub
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)

project_id = "serene-flare-466616-m5"
topic_id = "bot_messages"
# --- For Publisher ---
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(project_id, topic_id)


