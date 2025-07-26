import src.utils.constants as constants
from typing import List, Dict, Any
from src.models.bot.message_context import BotMessageContext
import src.whatsapp.request_payload as wa_req_payload
from enum import Enum

class MessageCategory(Enum):
    BOT_TO_USER = "bot_to_botuser"
    BOT_TO_USER_RESPONSE = "bot_to_botuser_response"
    BOT_TO_EXPERT = "bot_to_botexpert"
    BOT_TO_EXPERT_RESPONSE = "bot_to_botexpert_response"
    BOT_TO_EXPERT_VERIFICATION = "bot_to_botexpert_verification"
    USER_TO_BOT = "botuser_to_bot"
    EXPERT_TO_BOT = "botexpert_to_bot",
    READ_RECEIPT = "read_receipt"

def has_audio_additional_info(
    bot_message: BotMessageContext
):
    return (
        bot_message.message_context.additional_info is not None and
        constants.DATA in bot_message.message_context.additional_info and
        constants.MIME_TYPE in bot_message.message_context.additional_info and
        "audio" in bot_message.message_context.additional_info.get(constants.MIME_TYPE)
    )

def has_interactive_list_additional_info(
    bot_message: BotMessageContext
):
    return (
        bot_message.message_context.additional_info is not None and
        constants.DESCRIPTION in bot_message.message_context.additional_info and
        constants.ROW_TEXTS in bot_message.message_context.additional_info
    )

def has_interactive_button_additional_info(
    bot_message: BotMessageContext
):
    return (
        bot_message.message_context.additional_info is not None and
        "button_titles" in bot_message.message_context.additional_info
    )

def has_template_additional_info(
    bot_message: BotMessageContext
):
    return (    
        bot_message.message_context.additional_info is not None and
        constants.TEMPLATE_NAME in bot_message.message_context.additional_info and
        constants.TEMPLATE_LANGUAGE in bot_message.message_context.additional_info and
        constants.TEMPLATE_PARAMETERS in bot_message.message_context.additional_info
    )

def has_text(
    bot_message: BotMessageContext
):
    return (
        bot_message.message_context.message_source_text is not None
    )

def get_last_active_duration_seconds(timestamp: str):
    from datetime import datetime
    
    # Convert Unix timestamp string to a datetime object
    last_active_time = datetime.fromtimestamp(int(timestamp))
    
    # Calculate the duration since last active
    return (datetime.now() - last_active_time).total_seconds()

def get_expert_bot_messages(bot_messages: List[BotMessageContext]):
    # expert_user_types = bot_config["expert"]
    expert_messages = [
        bot_message for bot_message in bot_messages
        if bot_message.user is not None and bot_message.user.user_type in expert_user_types.values()
    ]
    return expert_messages

def get_user_bot_messages(bot_messages: List[BotMessageContext]):
    # regular_user_type = bot_config["regular"]["user_type"]
    user_messages = [
        bot_message for bot_message in bot_messages 
        if bot_message.user is not None and bot_message.user.user_type == regular_user_type
    ]
    return user_messages

def get_read_receipt_bot_messages(bot_messages: List[BotMessageContext]):
    read_receipt_messages = [
        bot_message for bot_message in bot_messages
        if bot_message.message_category == MessageCategory.READ_RECEIPT.value
    ]
    return read_receipt_messages
    
def prepare_requests(
    bot_message: BotMessageContext
) -> List[Dict[str, Any]]:
    wa_requests = []
    if has_interactive_button_additional_info(bot_message):
        wa_interactive_button_message = wa_req_payload.get_whatsapp_interactive_button_request_from_bot_message(bot_message)
        wa_requests.append(wa_interactive_button_message)
    elif has_interactive_list_additional_info(bot_message):
        wa_interactive_list_message = wa_req_payload.get_whatsapp_interactive_list_request_from_bot_message(bot_message)
        wa_requests.append(wa_interactive_list_message)
    elif has_text(bot_message):
        wa_text_message = wa_req_payload.get_whatsapp_text_request_from_bot_message(bot_message)
        wa_requests.append(wa_text_message)
    if has_template_additional_info(bot_message):
        wa_template_message = wa_req_payload.get_whatsapp_template_request_from_bot_message(bot_message)
        # print("Whatsapp template message", json.dumps(wa_template_message))
        wa_requests.append(wa_template_message)
    if has_audio_additional_info(bot_message):
        wa_audio_message = wa_req_payload.get_whatsapp_audio_request_from_bot_message(bot_message)
        wa_requests.append(wa_audio_message)
    return wa_requests