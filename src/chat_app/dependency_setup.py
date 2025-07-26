from ..whatsapp.client import AsyncWhatsAppClient

whatsapp_client = AsyncWhatsAppClient(
    phone_number_id='779353605250568',
    bearer_token='EAAJQPoXkZCoMBPGayRx7xVTsmMTJ7bRrgb3390s9LfzC3uwM90mNJ9rr6IoZBJIoz0bOCwI3FuoSfcjDnH5cDMN44ZBsWbKtifdR196lwqK9UqJFR9BE73ECSPb33DptN9IKDYyXPVqySaMiOuZBaZBdSyRpUeNJfWRjoyZCbkmfuDlMoIqp0OZAkEKDguPphebmnCPeHnQcQg0ZBZAah5AY7xLET1OZA4MDhMAdGZB0lyIZCNlZC67fi4CVOAt9YwgqnngZDZD',
    reuse_client=True
)

#publisher
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# Replace with the actual path to your service account key file
SERVICE_ACCOUNT_KEY_FILE = r"C:\Users\t-sharmara\kisanbot\serene-flare-466616-m5-bcb6c678bd2b.json"
API_KEY = 'AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc'


# projects/serene-flare-466616-m5/subscriptions/bot_messages-sub
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)

project_id = "serene-flare-466616-m5"
topic_id = "bot_messages"
# --- For Publisher ---
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

