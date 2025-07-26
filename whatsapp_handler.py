from flask import Flask, request, jsonify
import requests
import json
import os
import asyncio
from typing import Dict, Any, Optional
from google.cloud import speech
from google.cloud import storage
from PIL import Image
import io
import base64
from .main_bot import kisan_bot
from .firestore_client import FirestoreClient
from .vector_db_client import VectorDBClient

class WhatsAppHandler:
    def __init__(self):
        """Initialize WhatsApp handler with Google Cloud services"""
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        
        # Initialize Google Cloud clients
        self.speech_client = speech.SpeechClient()
        self.storage_client = storage.Client()
        self.firestore_client = FirestoreClient()
        self.vector_client = VectorDBClient()
        
        # Load vector index
        asyncio.create_task(self.vector_client.load_index())
    
    def verify_webhook(self, request) -> Dict[str, Any]:
        """Verify WhatsApp webhook"""
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == self.verify_token:
                print("Webhook verified successfully!")
                return {'challenge': challenge}, 200
            else:
                return {'error': 'Forbidden'}, 403
        
        return {'error': 'Bad Request'}, 400
    
    async def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming WhatsApp messages"""
        try:
            # Extract message data
            if 'entry' not in data:
                return {'status': 'no_entry'}, 200
            
            for entry in data['entry']:
                if 'changes' not in entry:
                    continue
                
                for change in entry['changes']:
                    if change.get('field') != 'messages':
                        continue
                    
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    
                    for message in messages:
                        await self.handle_message(message, value.get('contacts', []))
            
            return {'status': 'success'}, 200
            
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return {'error': str(e)}, 500
    
    async def handle_message(self, message: Dict[str, Any], contacts: list) -> None:
        """Handle individual WhatsApp message"""
        try:
            user_id = message.get('from')
            message_type = message.get('type')
            
            # Get user context
            user_session = await self.firestore_client.get_user_session(user_id)
            if not user_session:
                user_session = {
                    'user_id': user_id,
                    'message_count': 0,
                    'preferred_language': 'en',
                    'location': None,
                    'crops': []
                }
            
            user_session['message_count'] += 1
            
            # Process different message types
            response_text = ""
            
            if message_type == 'text':
                text_content = message.get('text', {}).get('body', '')
                response_text = await self.process_text_message(text_content, user_session)
                
            elif message_type == 'image':
                response_text = await self.process_image_message(message, user_session)
                
            elif message_type == 'audio' or message_type == 'voice':
                response_text = await self.process_audio_message(message, user_session)
                
            else:
                response_text = "I can help with text messages, images of plants, and voice messages. How can I assist you today?"
            
            # Save updated session
            await self.firestore_client.save_user_session(user_id, user_session)
            
            # Send response
            await self.send_message(user_id, response_text)
            
        except Exception as e:
            print(f"Error handling message: {e}")
            await self.send_message(user_id, "Sorry, I encountered an error. Please try again.")
    
    async def process_text_message(self, text: str, user_session: Dict) -> str:
        """Process text messages using the main bot flow with smart preprocessing"""
        try:
            # Use enhanced vector search for context with text preprocessing
            search_results = await self.vector_client.search_similar(text, top_k=3, source="text")
            
            # Add search context to session
            user_session['last_search_results'] = search_results
            
            # Call main bot flow with user context
            response = await kisan_bot(text, user_context=user_session)
            
            # If no specific flow triggered, use vector search results
            if "How can I assist you today?" in response and search_results:
                best_match = search_results[0]
                clean_text = self.vector_client.embedding_generator.preprocess(text, "text")
                response = f"Based on your query: '{clean_text}'\n\nHere's what I found:\n\n{best_match['text']}\n\nWould you like more specific information?"
            
            return response
            
        except Exception as e:
            print(f"Error processing text: {e}")
            return "I'm having trouble understanding your message. Could you please rephrase it?"
    
    async def process_image_message(self, message: Dict, user_session: Dict) -> str:
        """Process image messages for disease diagnosis"""
        try:
            # Download image from WhatsApp
            image_id = message.get('image', {}).get('id')
            if not image_id:
                return "I couldn't access the image. Please try sending it again."
            
            image_data = await self.download_media(image_id)
            if not image_data:
                return "Failed to download the image. Please try again."
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Get any accompanying text
            caption = message.get('image', {}).get('caption', '')
            if not caption:
                caption = "Please analyze this plant image for diseases or issues"
            
            # Use diagnosis flow
            from .diagnosis import diagnose_disease
            response = diagnose_disease(image, caption)
            
            # Save image analysis to session
            user_session['last_image_analysis'] = {
                'caption': caption,
                'response': response
            }
            
            return response
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return "I had trouble analyzing the image. Please make sure it's a clear photo of a plant and try again."
    
    async def process_audio_message(self, message: Dict, user_session: Dict) -> str:
        """Process audio messages using Speech-to-Text"""
        try:
            # Download audio from WhatsApp
            audio_id = message.get('audio', {}).get('id') or message.get('voice', {}).get('id')
            if not audio_id:
                return "I couldn't access the audio. Please try sending it again."
            
            audio_data = await self.download_media(audio_id)
            if not audio_data:
                return "Failed to download the audio. Please try again."
            
            # Convert audio to text using Speech-to-Text
            text = await self.speech_to_text(audio_data)
            if not text:
                return "I couldn't understand the audio. Could you please speak clearly and try again?"
            
            # Process speech with enhanced preprocessing
            try:
                # Use enhanced vector search for speech input
                search_results = await self.vector_client.search_similar(text, top_k=3, source="speech")
                
                # Add search context to session
                user_session['last_search_results'] = search_results
                user_session['last_speech_input'] = text
                
                # Call main bot flow with speech-preprocessed text
                clean_text = self.vector_client.embedding_generator.preprocess(text, "speech")
                response = await kisan_bot(clean_text, user_context=user_session)
                
                # If no specific flow triggered, use vector search results
                if "How can I assist you today?" in response and search_results:
                    best_match = search_results[0]
                    response = f"Here's what I found related to your question:\n\n{best_match['text']}\n\nWould you like more specific information?"
                
                # Add transcription info
                response = f"🎤 I heard: \"{clean_text}\"\n\n{response}"
                
                return response
                
            except Exception as e:
                print(f"Error processing speech: {e}")
                # Fallback to regular text processing
                response = await self.process_text_message(text, user_session)
                response = f"🎤 I heard: \"{text}\"\n\n{response}"
                return response
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return "I had trouble processing the audio message. Please try again or send a text message."
    
    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Download media from WhatsApp"""
        try:
            # Get media URL
            url = f"https://graph.facebook.com/v17.0/{media_id}"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return None
            
            media_url = response.json().get('url')
            if not media_url:
                return None
            
            # Download actual media
            media_response = requests.get(media_url, headers=headers)
            if media_response.status_code == 200:
                return media_response.content
            
            return None
            
        except Exception as e:
            print(f"Error downloading media: {e}")
            return None
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Convert audio to text using Google Speech-to-Text"""
        try:
            # Configure speech recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=16000,
                language_code="en-IN",  # Indian English
                alternative_language_codes=["hi-IN"],  # Hindi fallback
                enable_automatic_punctuation=True,
            )
            
            audio = speech.RecognitionAudio(content=audio_data)
            
            # Perform speech recognition
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                return transcript.strip()
            
            return None
            
        except Exception as e:
            print(f"Error in speech-to-text: {e}")
            return None
    
    async def send_message(self, user_id: str, message: str) -> bool:
        """Send message back to WhatsApp user"""
        try:
            url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': user_id,
                'text': {'body': message}
            }
            
            response = requests.post(url, headers=headers, json=data)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

# Flask app for webhook
app = Flask(__name__)
whatsapp_handler = WhatsAppHandler()

@app.route('/webhook', methods=['GET'])
def verify():
    """Verify webhook endpoint"""
    result, status_code = whatsapp_handler.verify_webhook(request)
    return jsonify(result), status_code

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle incoming messages"""
    data = request.get_json()
    result, status_code = await whatsapp_handler.process_webhook(data)
    return jsonify(result), status_code

if __name__ == '__main__':
    app.run(debug=True, port=8000) 