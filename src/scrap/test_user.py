
import hashlib
import asyncio
from src.models.bot.user import User
from src.services.databases.user_collection import store_user_data, get_user_data

async def main():
    phone_number_id = '919780540036'
    user_id=hashlib.md5(phone_number_id.encode()).hexdigest()
    user_language = 'en-IN'
    user_type = 'Kisan'
    user = User(
        user_id=user_id,
        phone_number_id=phone_number_id,
        user_language=user_language,
        user_type=user_type
    )
    if await get_user_data(user_id) is None:
        await store_user_data(user)
        print(f"User {user_id} created with phone number {phone_number_id} and language {user_language}.")
    else:
        user = await get_user_data(user_id)
        print(f"User {user_id} already exists with phone number {user.phone_number_id} and language {user.user_language}.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")