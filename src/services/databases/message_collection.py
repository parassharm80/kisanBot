from src.models.bot.message_context import BotMessageContext
from src.chat_app.dependency_setup import db
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference

message_collection = db.collection('messages')
async def store_message_data(message: BotMessageContext):
    message_id = message.message_context.message_id
    doc_ref = message_collection.document(message_id)
    await doc_ref.set(message.model_dump())

async def get_message_data(message_id: str):
    doc_ref = message_collection.document(message_id)
    doc = await doc_ref.get()
    if doc.exists:
        doc_dict = doc.to_dict()
        print(f"Retrieved message data for {message_id}: {doc_dict}")
        return BotMessageContext.model_validate(doc_dict)
    return None