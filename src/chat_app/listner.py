# listener.py

from google.cloud import pubsub_v1
from google.oauth2 import service_account
from src.models.bot.message_context import BotMessageContext
import json
import asyncio
from src.chat_app.dependency_setup import SERVICE_ACCOUNT_KEY_FILE
from src.services.user_flow.message_handle import handle_user_message
import traceback
import os
from google import auth


# This will hold the main event loop from the FastAPI app
main_loop = None
consumer = None

API_KEY = os.environ.get("API_KEY", "")
if os.environ.get("ENV") == "local":
    SERVICE_ACCOUNT_KEY_FILE = os.environ.get("SERVICE_ACCOUNT_KEY_FILE")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)

    project_id = os.environ.get("PROJECT_ID")

else:
    credentials, project_id = auth.default()
topic_id = "bot_messages"

subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
subscription_id = "bot_messages-sub"
subscription_path = subscriber.subscription_path(project_id, subscription_id)


async def _async_process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """
    ✨ FIX: This is the original async logic, now in its own function.
    It will be scheduled to run on the main event loop.
    """
    try:
        print(f"Received message ID: {message.message_id}")
        data = message.data.decode('utf-8')
        print(f"Data: {data}")
        
        json_message = json.loads(data)
        user_message = BotMessageContext.model_validate(json_message)

        # This await now happens correctly on the main event loop
        await handle_user_message(user_message)

        message.ack()
        print(f"Acknowledged message ID: {message.message_id}")

    except Exception as e:
        print(f"Error processing message {message.message_id}: {e}")
        traceback.print_exc()
        message.nack()


def pubsub_callback(message: pubsub_v1.subscriber.message.Message) -> None:
    """
    ✨ FIX: A standard synchronous callback.
    It safely schedules the async processing on the main event loop.
    """
    if not main_loop:
        print("ERROR: Main event loop is not set. Cannot process message.")
        # Nacking is a good default action if the app is not ready
        message.nack()
        return

    # Schedule the coroutine to be executed on the main event loop
    asyncio.run_coroutine_threadsafe(_async_process_message(message), main_loop)


async def listen_for_messages():
    """
    Starts the Pub/Sub subscriber. This function itself remains async.
    """
    print(f"Listening for messages on {subscription_path}...")
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=pubsub_callback,  # ✨ FIX: Pass the new synchronous callback
    )

    global consumer
    consumer = streaming_pull_future
    try:
        await streaming_pull_future
    except asyncio.CancelledError:
        print("Subscriber task cancelled.")
        streaming_pull_future.cancel()


async def cancel():
    if consumer:
        consumer.cancel()
        # The result() call on a cancelled future raises CancelledError,
        # so we wrap it in a try/except block.
        try:
            consumer.result()
        except asyncio.CancelledError:
            pass # Cancellation is expected
    subscriber.close()