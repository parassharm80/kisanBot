from ..whatsapp.client import AsyncWhatsAppClient

whatsapp_client = AsyncWhatsAppClient(
    phone_number_id='779353605250568',
    bearer_token='EAAJQPoXkZCoMBPInf5JugXSAHKpHZCmZAXpEkAtT4JGEQEc2xUHPLD9v3lG7Aze9XZBmlJ5I1imDhXr9iV4tPYfLPonFS0yvpZBgatBh2AH7Ro8re2DkQvbn57aZBP1BhjRzoi78qHPtVYmSS1ZAo0xP43fPdykfSGnHcO7l5tVrJnsAi1ZBEN0IHXZAI0U5sPL3dN1wzaoTLyVLo4IFMEP6BvCJuo1b8mdmFPdFb9okuebc3hrinpAdPgBAoggZDZD',
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


