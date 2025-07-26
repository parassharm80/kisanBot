import hashlib
import logging
import json
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from src.whatsapp.validate_message import validate_whatsapp_message
from src.whatsapp.convert_message import convert_whatsapp_to_bot_message
from src.chat_app.dependency_setup import publisher, topic_path, update_whatsapp
from src.services.databases.user_collection import get_user_data


CHAT_API_NAME = 'chat_api'
chat_apis_router = APIRouter()
_logger = logging.getLogger(CHAT_API_NAME)


@chat_apis_router.post("/receive")
async def receive(request: Request):
    """
    Handle incoming WhatsApp messages.
    """
    body = await request.json()
    # print("Received the request: ", json.dumps(body))
    print(f"Received the request: {json.dumps(body)}")

    _, message_type = validate_whatsapp_message(body)
    if message_type == "status":
        return JSONResponse(
            content='Done',
            status_code=200
        )
    bot_message  = convert_whatsapp_to_bot_message(body, message_type)
    user_id=hashlib.md5(bot_message.user.phone_number_id.encode()).hexdigest()
    bot_message.user = await get_user_data(user_id)
    if bot_message.user is None:
        return JSONResponse(
            content='Done',
            status_code=200
        )
    data = bot_message.model_dump_json()
    data = data.encode("utf-8")
    future = publisher.publish(topic_path, data)
    print(f"Published message ID (Service Account): {future.result()}")
    print(f"Message type: {message_type}")
    print(f"bot_message: {bot_message.model_dump_json(indent=2)}")
    return JSONResponse(
        content='Done',
        status_code=200
    )
    
@chat_apis_router.post("/update_whatsapp_token")
async def update_token(request: Request):
    """
    Update the WhatsApp bearer token.
    """
    body = await request.json()
    token = body.get("token")
    # print("Received the request: ", json.dumps(body))
    print(f"Received the request: {json.dumps(body)}")
    await update_whatsapp(token)
    return JSONResponse(
        content='Done',
        status_code=200
    )

