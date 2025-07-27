import asyncio
from src.services.translator import async_translate
from src.services.text_to_speech import async_text_to_speech
from src.services.speech_to_text import async_transcribe_ogg_bytes_gemini
from src.services.image_to_text import async_generate_text_from_image
from src.services.online_flow import async_generate_online
from src.services.follow_up import async_generate_related
from src.services.offline_flow import async_generate_offline
from src.models.bot.message_context import (
    BotMessageContext,
    MessageContext,
    ReplyContext,
    MediaContext,
    MessageTypes
)
from src.models.bot.user import User
from src.utils import constants
from src.utils import wa_utils as wa_utils
from src.chat_app.dependency_setup import get_whatsapp_client
from src.services.databases.message_collection import store_message_data

language_dict = {
    "en-IN": "en",
    "hi-IN": "hi",
    "kn-IN": "te",
}
descriptions = {
    "en-IN": "Related questions",
    "hi-IN": "संबंधित प्रश्न",
    "kn-IN": "ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಗಳು",
}
async def generate_context(
    message: BotMessageContext,
): 
    user_lang_related_questions = ['a','b','c']
    interactive_list_additional_info = {
        constants.DESCRIPTION: 'description',
        constants.ROW_TEXTS: user_lang_related_questions
    }
    source_text = None
    english_text = None
    category = None
    desc = 'description'
    questions = user_lang_related_questions
    if message.message_context.message_type == MessageTypes.REGULAR_IMAGE.value:
        media_id = message.message_context.media_info.media_id
        _, image_message, err = await get_whatsapp_client().adownload_media(media_id)
        source_text = message.message_context.message_source_text
        text_en, text_src = await async_generate_text_from_image(image_message.data, language_dict[message.user.user_language], source_text)
        questions = await async_generate_related(
            "User gave an image input and below is the response. Use only the response text to generate related questions.",
            text_en,
            message.user.user_language
        )
        desc = descriptions[message.user.user_language]
        source_text = text_src
        english_text = text_en
    if message.message_context.message_type == MessageTypes.REGULAR_TEXT.value or message.message_context.message_type == MessageTypes.INTERACTIVE_LIST.value:
        eng_query = await async_translate(
            message.message_context.message_source_text,
            message.user.user_language
        )
        message.message_context.message_english_text = eng_query
        text_en, text_src = await async_generate_online(
            message.message_context.message_source_text,
            language_dict[message.user.user_language]
        )
        questions = await async_generate_related(
            message.message_context.message_english_text,
            text_en,
            message.user.user_language
        )
        print(f"Generated online response: {text_en}, {text_src}, {questions}")
        desc = descriptions[message.user.user_language]
        source_text = text_src
        english_text = text_en
    elif message.message_context.message_type == MessageTypes.REGULAR_AUDIO.value:
        media_id = message.message_context.media_info.media_id
        _, audio_message, err = await get_whatsapp_client().adownload_media(media_id)
        if audio_message.data is None:
            print(f"Error downloading media with ID {media_id}: {err}")
        else:
            print(f"Downloaded audio media with ID {media_id}")
        text_en, text_src = await async_transcribe_ogg_bytes_gemini(audio_message.data, language_dict[message.user.user_language])
        message.message_context.message_source_text = text_src
        message.message_context.message_english_text = text_en
        text_en, text_src = await async_generate_online(
            message.message_context.message_english_text,
            language_dict[message.user.user_language]
        )
        questions = await async_generate_related(
            message.message_context.message_english_text,
            text_en,
            message.user.user_language
        )
        desc = descriptions[message.user.user_language]
        source_text = text_src
        english_text = text_en
    interactive_list_additional_info = {
        constants.DESCRIPTION: desc,
        constants.ROW_TEXTS: questions
    }
    translated_audio_message = await async_text_to_speech(source_text, message.user.user_language)
    media_info = {
        constants.DATA: translated_audio_message,
        constants.MIME_TYPE: "audio/ogg",
    }
    user_message = BotMessageContext(
        channel_type=message.channel_type,
        message_category='BOT_TO_USER_RESPONSE',
        user=User(
            user_id=message.user.user_id,
            user_language=message.user.user_language,
            user_type=message.user.user_type,
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

async def send(user_message_context: BotMessageContext) -> BotMessageContext:
    async def send_requests(requests):
        tasks = []
        for request in requests:
            message_type = request["type"]
            tasks.append(get_whatsapp_client().asend_batch_messages([request], message_type))
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
    user_message_context.message_context.message_id = message_id_text[0]
    response_audio, message_id_audio = await send_requests([audio_no_tag_message])
    responses = response_text
    message_ids = message_id_text
    return user_message_context

async def handle_user_message(message: BotMessageContext):
    print("Handling user message:", message)
    # message.user.user_language = 'hi-IN
    user_message_context = await generate_context(message)
    user_message_context = await send(user_message_context)
    await store_message_data(user_message_context)
    print(f"User message sent with ID: {user_message_context.message_context.message_id}")

