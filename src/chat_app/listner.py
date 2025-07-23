from google.cloud import pubsub_v1
from google.oauth2 import service_account
from src.models.bot.message_context import BotMessageContext
from src.models.bot.user import User
from ..services.user_flow.message_handle import handle_user_message
import json

# Replace with the actual path to your service account key file
SERVICE_ACCOUNT_KEY_FILE = "/Users/parassharma/Downloads/serene-flare-466616-m5-ced346076763.json"
consumer = None
# projects/serene-flare-466616-m5/subscriptions/bot_messages-sub
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)

project_id = "serene-flare-466616-m5"
topic_id = "bot_messages"


subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

subscription_id = "bot_messages-sub"
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    import asyncio
    print(f"Received message (Service Account): {message.data.decode('utf-8')}")
    json_message = json.loads(message.data.decode('utf-8'))
    user_message = BotMessageContext.model_validate(json_message)
    asyncio.run(handle_user_message(user_message))
    message.ack()

# # Set the flow control to manage the ack deadline
# # We want the client to keep messages leased for up to 120 seconds.
# flow_control = pubsub_v1.types.FlowControl(
#     max_duration_per_lease_extension=120,
# )

def listen_for_messages():
    print(f"Listening for messages on {subscription_path} with a 2-minute ack deadline extension...")

    # Pass the flow_control settings to the subscribe method
    streaming_pull_future = subscriber.subscribe(
        subscription_path, 
        callback=callback, 
    )

        # result() will block indefinitely, waiting for messages.
    global consumer
    consumer = streaming_pull_future


def cancel():
    consumer.cancel()  # Stop consuming messages
    consumer.result()  # Wait for the cancellation to complete
    subscriber.close()