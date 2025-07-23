import uuid
import logging
import src.whatsapp.requests as wa_requests
from ..whatsapp.requests import media_request as wa_media
from ..models.bot.message_context import BotMessageContext
from ..whatsapp.message_context import WhatsappMessageReplyContext
from enum import Enum


class WhatsAppMessageTypes(Enum):
    TEXT = "text"
    REACTION = "reaction"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"
    AUDIO = "audio"
    READ = "read"


logger = logging.getLogger(__name__)
def get_whatsapp_text_request_from_bot_message(
    bot_message: BotMessageContext
):
    message_text = bot_message.message_context.message_source_text
    phone_number_id = bot_message.user.phone_number_id
    messaging_product = "whatsapp"
    context = None
    if bot_message.reply_context is not None:
        reply_id = bot_message.reply_context.reply_id
        context = WhatsappMessageReplyContext(
            message_id=reply_id
        )
    text_message = wa_requests.WhatsAppMessage(
            messaging_product=messaging_product,
            to=phone_number_id,
            type=WhatsAppMessageTypes.TEXT.value,
            text=wa_requests.Text(body=message_text),
            context=context
        )
    return text_message.model_dump()

def get_whatsapp_audio_request_from_bot_message(
    bot_message: BotMessageContext,
):
            
    audio_data = bot_message.message_context.additional_info["data"]
    mime_type = bot_message.message_context.additional_info.get("mime_type", None)
    phone_number_id = bot_message.user.phone_number_id
    messaging_product = "whatsapp"
    context = None
    if bot_message.reply_context is not None:
        reply_id = bot_message.reply_context.reply_id
        context = WhatsappMessageReplyContext(
            message_id=reply_id
        )
    try:
        audio = None
        if mime_type == wa_media.FileMediaType.AUDIO_OGG.value:
            audio = audio_data
            mime_type = wa_media.FileMediaType.AUDIO_OGG.value
        audio_message = wa_requests.WhatsAppMediaMessage(
            messaging_product=messaging_product,
            to=phone_number_id,
            type=WhatsAppMessageTypes.AUDIO.value,
            media=wa_requests.MediaData(
                data=audio,
                mime_type=mime_type
            ),
            context=context
        )
        return audio_message.model_dump()
    except ValueError as e:
        logger.error(f"Audio conversion error: {e}")
        print(f"Audio conversion error: {e}")
        return None

def get_whatsapp_interactive_button_request_from_bot_message(
    bot_message: BotMessageContext
):
    def get_button(title):
        poll_id = str(uuid.uuid4())
        return wa_requests.InteractiveActionButton(
            reply=wa_requests.InteractiveReply(
                id=poll_id,
                title=title
            )
        )
    context = None
    if bot_message.reply_context is not None:
        reply_id = bot_message.reply_context.reply_id
        context = WhatsappMessageReplyContext(
            message_id=reply_id
        )
    button_titles = bot_message.message_context.additional_info["button_titles"]
    buttons = [get_button(title) for title in button_titles]
    message_text = bot_message.message_context.message_source_text
    phone_number_id = bot_message.user.phone_number_id
    interactive_message = wa_requests.WhatsAppInteractiveMessage(
        messaging_product="whatsapp",
        to=phone_number_id,
        type=WhatsAppMessageTypes.INTERACTIVE.value,
        interactive=wa_requests.Interactive(
            body=wa_requests.InteractiveBody(
                text=message_text
            ),
            action=wa_requests.InteractiveAction(
                buttons=buttons
            )
        ),
        context=context
    )
    return interactive_message.model_dump()

def get_whatsapp_interactive_list_request_from_bot_message(
    bot_message: BotMessageContext
):
    def get_section_row(description):
        return wa_requests.InteractiveSectionRow(
            id=str(uuid.uuid4()),
            title=" ",
            description=description
        )
    def get_section(row_texts):
        rows = [get_section_row(row_text) for row_text in row_texts]
        return wa_requests.InteractiveActionSection(
            title="Default Section",
            rows=rows
        )
    description = bot_message.message_context.additional_info["description"]
    row_texts = bot_message.message_context.additional_info["row_texts"]
    message_text = bot_message.message_context.message_source_text
    phone_number_id = bot_message.user.phone_number_id
    context = None
    if bot_message.reply_context is not None:
        reply_id = bot_message.reply_context.reply_id
        context = WhatsappMessageReplyContext(
            message_id=reply_id
        )
    interactive_message = wa_requests.WhatsAppInteractiveMessage(
        messaging_product="whatsapp",
        to=phone_number_id,
        type=WhatsAppMessageTypes.INTERACTIVE.value,
        interactive=wa_requests.Interactive(
            type=wa_requests.InteractiveMessageTypes.LIST.value,
            body=wa_requests.InteractiveBody(
                text=message_text
            ),
            action=wa_requests.InteractiveAction(
                button=description,
                sections=[
                    get_section(row_texts),
                ]
            )
        ),
        context=context
    )
    return interactive_message.model_dump()

def get_whatsapp_template_request_from_bot_message(
    bot_message: BotMessageContext
):
    template_parameters = bot_message.message_context.additional_info["template_parameters"]
    template_name = bot_message.message_context.additional_info["template_name"]
    template_language = bot_message.message_context.additional_info["template_language"]
    phone_number_id = bot_message.user.phone_number_id
    parameters = [
        wa_requests.TemplateParameter(
            type="text",
            text=parameter
        ) for parameter in template_parameters
    ]
    component = wa_requests.TemplateComponent(
        type="body",
        parameters=parameters
    )
    template = wa_requests.Template(
        name =template_name,
        language=wa_requests.TemplateLanguage(
            code=template_language,
        ),
        components=[component]
    )
    template_message = wa_requests.WhatsAppTemplateMessage(
        messaging_product="whatsapp",
        to=phone_number_id,
        type=WhatsAppMessageTypes.TEMPLATE.value,
        template=template
    )
    return template_message.model_dump()

def get_whatsapp_reaction_request(
    phone_number_id,
    message_id,
    reaction
):
    reaction_message = wa_requests.WhatsAppMessage(
        messaging_product="whatsapp",
        to=phone_number_id,
        type=WhatsAppMessageTypes.REACTION.value,
        reaction=wa_requests.Reaction(
            message_id=message_id,
            emoji=reaction
        )
    )
    return reaction_message.model_dump()

def get_whatsapp_read_reciept(message_id):
    read_receipt = wa_requests.WhatsAppReadMessage(
        messaging_product="whatsapp",
        status="read",
        message_id=message_id
    )
    return read_receipt.model_dump()