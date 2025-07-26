import asyncio
from src.services.text_to_speech import async_text_to_speech
from src.services.speech_to_text import async_transcribe_ogg_bytes_gemini
from src.services.image_to_text import async_generate_text_from_image
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

async def generate_context(
    message: BotMessageContext,
): 
    user_lang_related_questions = ['a','b','c']
    interactive_list_additional_info = {
        constants.DESCRIPTION: 'description',
        constants.ROW_TEXTS: user_lang_related_questions
    }
    source_text = 'जय हिंद'
    english_text = 'kaka in english'
    if message.message_context.message_type == MessageTypes.REGULAR_IMAGE.value:
        source_text = message.message_context.message_source_text
        english_text = message.message_context.message_english_text
    elif message.message_context.message_type == MessageTypes.REGULAR_AUDIO.value:
        source_text = message.message_context.message_source_text
        english_text = message.message_context.message_english_text
    translated_audio_message = await async_text_to_speech(source_text, message.user.user_language)
    media_info = {
        constants.DATA: translated_audio_message,
        constants.MIME_TYPE: "audio/ogg",
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
            message_source_text=source_text,
            message_english_text=english_text,
            additional_info={
                **media_info,
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
    user_requests_no_tag = wa_utils.prepare_requests(user_message_copy)
    text_tag_message = user_requests[0]
    audio_no_tag_message = user_requests_no_tag[1]
    response_text, message_id_text = await send_requests([text_tag_message])
    response_audio, message_id_audio = await send_requests([audio_no_tag_message])
    responses = response_text
    message_ids = message_id_text

async def handle_user_message(message: BotMessageContext):
    print("Handling user message:", message)
    message.user.user_language = 'hi-IN'
    if message.message_context.message_type == MessageTypes.REGULAR_IMAGE.value:
        print("Handling image message")
        media_id = message.message_context.media_info.media_id
        _, image_message, err = await whatsapp_client.adownload_media(media_id)
        source_text = message.message_context.message_source_text
        text_en, text_src = await async_generate_text_from_image(image_message.data, message.user.user_language, source_text)
        message.message_context.message_source_text = text_src
        message.message_context.message_english_text = text_en
        print(f"Extracted text from image: {text_en, text_src}")
        if image_message.data is None:
            print(f"Error downloading media with ID {media_id}: {err}")
    elif (message.message_context.message_type == MessageTypes.REGULAR_AUDIO.value):
        media_id = message.message_context.media_info.media_id
        _, audio_message, err = await whatsapp_client.adownload_media(media_id)
        if audio_message.data is None:
            print(f"Error downloading media with ID {media_id}: {err}")
        else:
            print(f"Downloaded audio media with ID {media_id}")
        text_en, text_src = await async_transcribe_ogg_bytes_gemini(audio_message.data, message.user.user_language)
        print(f"Transcribed audio to text: {text_en, text_src}")
        message.message_context.message_source_text = text_src
        message.message_context.message_english_text = text_en
    user_message_context = await generate_context(message)
    await send(user_message_context)

