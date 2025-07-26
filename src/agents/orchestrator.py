import google.generativeai as genai
import os
import asyncio

from src.agents.offline_agent import generation_offline
from src.agents.online_agent import generation_online
from src.chat_app.dependency_setup import orch_model


# Topics that should be handled by the offline RAG system.
OFFLINE_TOPICS = [
    "Nitrogen fertilizer",
]

# A mapping to direct the classified topic to an async function.
# Note that we are storing the function objects themselves.
FUNCTION_MAP = {
    "Offline": generation_offline,
    "Online": generation_online,
}


async def agent_orchestrator(query: str):
    """
    Asynchronously classifies the query and routes it to the appropriate generation function.
    """
    print(f"\nProcessing query: '{query}'")

    classification_prompt = f"""
    You are a topic router. Your job is to classify the user's query.

    These are the topics that must be handled by an internal, offline knowledge base:
    {', '.join(OFFLINE_TOPICS)}

    If the user's query clearly falls into one of those categories, respond with only the word "Offline".
    For any other query that requires general knowledge or current events, respond with only the word "Online".

    User Query: "{query}"
    Classification:
    """

    try:
        # Use the async version of the generate_content method
        response = await orch_model.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=classification_prompt)

        classified_topic = response.text.strip()
        print(f"🧠 Classification result: {classified_topic}")

        # Step 2: Route to the correct async function based on classification
        target_function = FUNCTION_MAP.get(classified_topic)

        # Step 3: Execute the async function or return "I don't know"
        if target_function:
            # Await the selected asynchronous function
            return await target_function(query)
        else:
            print("🤔 Classification unclear.")
            return "I don't know how to answer that question."

    except Exception as e:
        print(f"An error occurred: {e}")
        return "I'm sorry, I encountered an error and cannot process your request."


# --- Example Usage with asyncio ---
async def main():
    """Main async function to run the examples."""
    # Query that should go to the offline RAG system
    offline_query = "nitrogen fertilizer doses?"
    offline_response = await agent_orchestrator(offline_query)
    print(f"✅ Final Answer: {offline_response}")

    print("-" * 30)

    # Query that should go to the online Gemini function
    online_query = "What is the current weather in Bengaluru?"
    online_response = await agent_orchestrator(online_query)
    print(f"✅ Final Answer: {online_response}")

if __name__ == "__main__":
    # Run the main async function using asyncio.run()
    asyncio.run(main())