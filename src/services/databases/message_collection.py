from src.models.bot.message_context import BotMessageContext
from src.models.bot.user import User
from src.chat_app.dependency_setup import db
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference

user_collection = db.collection('users')
async def store_message_data(message: BotMessageContext):
    pass

async def get_message_data(message_id: str):
    pass