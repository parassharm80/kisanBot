from src.models.bot.user import User
from src.chat_app.dependency_setup import db
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference

user_collection = db.collection('users')
async def store_user_data(user: User):
    user_id = user.user_id
    doc_ref = user_collection.document(user_id)
    await doc_ref.set(user.model_dump())

async def get_user_data(user_id: str) -> User:
    doc_ref = user_collection.document(user_id)
    doc = await doc_ref.get()
    if doc.exists:
        doc_dict = doc.to_dict()
        print(f"Retrieved user data for {user_id}: {doc_dict}")
        return User.model_validate(doc_dict)
    return None