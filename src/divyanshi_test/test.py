## AIzaSyDmc7RxbeLOpTe299AlzZo-CxYF-KxyCbg
import requests
import json
import os

# --- IMPORTANT: Replace with your actual Gemini API Key ---
# It's recommended to load this from an environment variable for security.
# For demonstration, we'll keep it here, but be mindful in production.
GEMINI_API_KEY = "AIzaSyDmc7RxbeLOpTe299AlzZo-CxYF-KxyCbg" # <--- REPLACE THIS WITH YOUR KEY!

def call_gemini_api(prompt_text):
    """
    Sends a text prompt to the Gemini 2.0 Flash model and prints the response.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Error: GEMINI_API_KEY is not set or is the placeholder. Please set it.")
        return

    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt_text 
                    }
                ]
            }
        ]
    }

    print(f"\nSending request to Gemini API with prompt: '{prompt_text}'...")
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        json_response = response.json()
        
        if 'candidates' in json_response and json_response['candidates']:
            for candidate in json_response['candidates']:
                if candidate.get('content') and candidate['content'].get('parts'):
                    for part in candidate['content']['parts']:
                        if part.get('text'):
                            print("\n--- Gemini's Response ---")
                            print(part['text'])
                        else:
                            print("Gemini response part has no 'text' field.")
                else:
                    print("Gemini response candidate has no 'content' or 'parts'.")
        else:
            print("Gemini did not return any 'candidates' for this request.")
            print(f"Full API response: {json.dumps(json_response, indent=2)}")

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
        print(f"Response content: {response.text}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"An unexpected error occurred: {err}")
    except json.JSONDecodeError as errd:
        print(f"JSON Decode Error: {errd}")
        print(f"Raw response text: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred during response processing: {e}")


if __name__ == "__main__":
    # Define prompts in both English and Hindi
    prompts = {
        "english": {
            "capital_query": "What is the capital of India? Answer briefly.",
            "greeting_query": "Tell me some ways to say hello."
        },
        "hindi": {
            "capital_query": "भारत की राजधानी क्या है? संक्षेप में उत्तर दें।",
            "greeting_query": "नमस्ते कहने के कुछ तरीके बताएं।"
        }
    }

    print("Choose a language for the prompts:")
    print("1. English")
    print("2. Hindi")

    while True:
        lang_choice = input("Enter your choice (1 or 2): ").strip()
        if lang_choice == '1':
            selected_language = "english"
            break
        elif lang_choice == '2':
            selected_language = "hindi"
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

    print(f"\nSelected language: {selected_language.capitalize()}")

    # Call API with the selected language's prompts
    print("\n--- Query 1: Capital of India ---")
    call_gemini_api(prompts[selected_language]["capital_query"])

    print("\n" + "="*50 + "\n")

    print("--- Query 2: Ways to say hello ---")
    call_gemini_api(prompts[selected_language]["greeting_query"])

    # You can also allow the user to input their own prompt in the chosen language
    print("\n" + "="*50 + "\n")
    print(f"Enter your own prompt in {selected_language.capitalize()} (type 'exit' to quit):")
    while True:
        user_input = input(f"Your prompt ({selected_language.capitalize()}): ").strip()
        if user_input.lower() == 'exit':
            break
        if user_input:
            call_gemini_api(user_input)
        else:
            print("Prompt cannot be empty. Please enter something.")

