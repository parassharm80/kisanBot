from ..whatsapp.client import AsyncWhatsAppClient

whatsapp_client = AsyncWhatsAppClient(
    phone_number_id='779353605250568',
    bearer_token='EAAJQPoXkZCoMBPHQk9jaM4g8Y9tSXbDueXcgjHlXctNOs7wQaV1XV2hWIqPnLHVxQ3AEtpaAs1PFaRbk6NboEl5ZAIZBvvw1aGmEAZCYNw2jsFhk74rmT3HsCKh5WSgiZAyTqjz80lzeZAiziHpyZAmFNPAZAkhHFR4DQvl33GNXANQgWwTCmHKAZCGZBrKRmRMiXqokgM6IeMR8ACqSbYt97QTOVPRsE2CnmTaxpBpidkTebcX7jSCatcXxx34wZDZD',
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


