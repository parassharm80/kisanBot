from google.cloud import pubsub_v1
from google.oauth2 import service_account
import time
import os
from google import auth

API_KEY = os.environ.get("API_KEY", "")
if os.environ.get("ENV") == "local":
    SERVICE_ACCOUNT_KEY_FILE = os.environ.get("SERVICE_ACCOUNT_KEY_FILE")
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)

    project_id = os.environ.get("PROJECT_ID")

else:
    credentials, project_id = auth.default()
topic_id = "bot_messages"
# topic_path = publisher.topic_path(project_id, topic_id)
# # --- For Publisher ---
# publisher = pubsub_v1.PublisherClient(credentials=credentials)
# topic_path = publisher.topic_path(project_id, topic_id)

# data = "Hello from service account!"
# data = data.encode("utf-8")
# future = publisher.publish(topic_path, data)
# print(f"Published message ID (Service Account): {future.result()}")


# # --- For Subscriber ---
# subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

# subscription_id = "bot_messages-sub"
# subscription_path = subscriber.subscription_path(project_id, subscription_id)

# def callback(message):
#     print(f"Received message (Service Account): {message.data.decode('utf-8')}")
#     message.ack()

# print(f"Listening for messages on {subscription_path} using service account...")
# streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
# try:
#     streaming_pull_future.result()
# except KeyboardInterrupt:
#     streaming_pull_future.cancel()
#     streaming_pull_future.result()
#     subscriber.close()



subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

subscription_id = "bot_messages-sub"
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    print(f"Received message (Service Account): {message.data.decode('utf-8')}")
    # Your processing logic that might take up to 2 minutes goes here
    # time.sleep(120)
    message.ack()
    print(f"Message processed and acknowledged.{message.data.decode('utf-8')}")

# Set the flow control to manage the ack deadline
# We want the client to keep messages leased for up to 120 seconds.
flow_control = pubsub_v1.types.FlowControl(
    max_duration_per_lease_extension=120,
)

print(f"Listening for messages on {subscription_path} with a 2-minute ack deadline extension...")

# Pass the flow_control settings to the subscribe method
streaming_pull_future = subscriber.subscribe(
    subscription_path, 
    callback=callback, 
    # flow_control=flow_control
)

try:
    # result() will block indefinitely, waiting for messages.
    streaming_pull_future.result()
except KeyboardInterrupt:
    streaming_pull_future.cancel()  # Stop consuming messages
    streaming_pull_future.result()  # Wait for the cancellation to complete
    subscriber.close()
