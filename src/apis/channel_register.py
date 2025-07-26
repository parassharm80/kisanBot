import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src.models.response import ResponseModel

REGISTER_API_NAME = 'register_api'

register_apis_router = APIRouter()
_logger = logging.getLogger(REGISTER_API_NAME)

@register_apis_router.get("/receive")
async def register(request: Request):
    """
    Route to handle the registration process.
    """
    # print("Received the request: ", request.query_params._dict)
    _logger.debug(msg=f"Received the request: \n{request.query_params._dict}")
    response = get_response(request.query_params._dict)
    print("Response: ", response.message)
    return JSONResponse(content=int(response.message), status_code=200)
    # return JSONResponse(content={"message": "received"}, status_code=200)

def is_invalid(
    value: str
):
    return value in (None, '', 'null')
def get_response(
    params: dict,
    verification_token = '12345'
) -> ResponseModel:
        
    REQUESST_MODE = "hub.mode"
    REQUEST_TOKEN = "hub.verify_token"
    REQUEST_CHALLENGE = "hub.challenge"

    MODE_TYPE = "subscribe"
    mode = params.get(REQUESST_MODE)
    token = params.get(REQUEST_TOKEN)
    challenge = params.get(REQUEST_CHALLENGE)

    
    if (is_invalid(mode) or
        is_invalid(token) or
        is_invalid(challenge)
    ):
        return ResponseModel(
            message="Invalid request to register whatsapp",
            status_code=400
        )

    if mode != MODE_TYPE:
        return ResponseModel(
            message="Invalid mode type",
            status_code=400
        )

    if token != verification_token:
        return ResponseModel(
            message="Invalid verification token",
            status_code=400
        )

    return ResponseModel(
        message=challenge,
        status_code=200
    )
