from ...models.bot.message_context import (
    BotMessageContext,
    MessageContext,
    ReplyContext,
    MediaContext,
    MessageTypes
)
from ...models.bot.user import User
from ...utils import constants
from ...utils import wa_utils as wa_utils
from ...chat_app.dependency_setup import whatsapp_client
import asyncio

async def generate_context(
    message: BotMessageContext,
): 
    user_lang_related_questions = ['a','b','c']
    interactive_list_additional_info = {
            constants.DESCRIPTION: 'description',
            constants.ROW_TEXTS: user_lang_related_questions
        }
    user_message = BotMessageContext(
        channel_type=message.channel_type,
        message_category='BOT_TO_USER_RESPONSE',
        user=User(
            user_id='sexy_user_id',
            user_language='hi',
            user_type='Kisan',
            phone_number_id=message.user.phone_number_id,
            last_conversations=message.user.last_conversations
        ),
        message_context=MessageContext(
            message_type=MessageTypes.INTERACTIVE_LIST.value,
            message_source_text='jai hind',
            message_english_text='kaka in english',
            additional_info={
                **interactive_list_additional_info
            }
        ),
        reply_context=ReplyContext(
            reply_id=message.message_context.message_id,
            reply_type=message.message_context.message_type,
            reply_english_text=message.message_context.message_english_text,
            reply_source_text=message.message_context.message_source_text,
            media_info=message.message_context.media_info
        ),
        incoming_timestamp=message.incoming_timestamp,
    )
    return user_message

async def send(user_message_context: BotMessageContext):
    async def send_requests(requests):
        tasks = []
        for request in requests:
            message_type = request["type"]
            tasks.append(whatsapp_client.asend_batch_messages([request], message_type))
        results = await asyncio.gather(*tasks)
        responses = [response for result in results for response in result]
        message_ids = [response.messages[0].id if response.messages else None for response in responses]
        return responses, message_ids
    user_requests = wa_utils.prepare_requests(user_message_context)
    user_message_copy = user_message_context.__deepcopy__()
    user_message_copy.reply_context = None
    # user_requests_no_tag = wa_utils.prepare_requests(user_message_copy)
    text_tag_message = user_requests[0]
    # audio_no_tag_message = user_requests_no_tag[1]
    response_text, message_id_text = await send_requests([text_tag_message])
    # response_audio, message_id_audio = await send_requests([audio_no_tag_message])
    responses = response_text
    message_ids = message_id_text

async def handle_user_message(message: BotMessageContext):
    print("Handling user message:", message)
    user_message_context = await generate_context(message)
    await send(user_message_context)

