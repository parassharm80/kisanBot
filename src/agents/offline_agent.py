import asyncio
from .vector.flows.vertex_ai_emb_gen import embed_text
from .vector.flows.vertex_ai_vector_search import VertexAIVectorSearch
import google.generativeai as genai

# Configure the generative model for answering questions based on context
# This can be configured globally or passed as a dependency
# For simplicity, we configure it here.
# Ensure your API key is set in your environment variables or configured elsewhere.
genai.configure(api_key='AIzaSyB3y8k32Rjw2A-EGRAWve3ZQxLTY9FwEHc')
rag_model = genai.GenerativeModel('gemini-2.5-flash')

async def generate_answer(query: str, context: str) -> str:
    """
    Generates an answer using a generative model based on the query and context.
    """
    prompt = f"""
    You are a helpful assistant. Answer the user's query based on the following context.
    If the context does not contain the answer, say that you don't know.

    Context:
    {context}

    Query: {query}

    Answer:
    """
    try:
        response = await rag_model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "I am sorry, but I encountered an error while generating the answer."

async def generation_offline(query: str) -> str:
    """
    Asynchronously queries a vector database using embeddings and generates an answer.
    """
    print("➡️ Routing to: ASYNC OFFLINE (RAG System)")

    try:
        # Initialize the vector search client. In a real application, this might be a singleton.
        vector_search_client = VertexAIVectorSearch()

        # 1. & 2. Embed the query and search for similar documents in the vector database
        # The search_similar_vectors method handles embedding the query.
        print(f"Searching for documents similar to: '{query}'")
        top_docs = await vector_search_client.search_similar_vectors(query, top_k=3)

        if not top_docs:
            return "📚 [OFFLINE RAG]: I could not find any relevant information in the internal documents."

        # 3. Concatenate retrieved context
        context = "\n".join([doc['text'] for doc in top_docs])
        print(f"Retrieved context: {context}")

        # 4. Generate answer using LLM with the retrieved context
        answer = await generate_answer(query, context)

        return f"📚 [OFFLINE RAG]: {answer}"

    except Exception as e:
        print(f"An error occurred in the offline generation flow: {e}")
        return "I am sorry, but I encountered an error and cannot process your request."