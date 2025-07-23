import logging
import json
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from ..whatsapp.validate_message import validate_whatsapp_message
from ..whatsapp.convert_message import convert_whatsapp_to_bot_message
from ..chat_app.dependency_setup import publisher, topic_path


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

