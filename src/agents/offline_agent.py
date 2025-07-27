import os
import re
import PyPDF2
import requests
import faiss
import numpy as np
import asyncio


# CORRECT: Import the necessary classes from the Vertex AI SDK
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel

# --- Configuration ---
# IMPORTANT: Replace with your actual Project ID
PROJECT_ID = "serene-flare-466616-m5"
LOCATION = "us-central1"
# Use a specific model for generation
GENERATION_MODEL_ID = "gemini-2.5-flash"
# Use the recommended model for embeddings
EMBEDDING_MODEL_ID = "gemini-embedding-001"


def initialize_vertex_ai():
    """Initializes the Vertex AI SDK."""
    print("🌍 Initializing Vertex AI...")
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    print("✅ Vertex AI Initialized.")


def download_pdf(url, save_path):
    """Downloads a PDF from a URL."""
    print(f"📄 Downloading PDF from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print("✅ PDF Downloaded.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading PDF: {e}")
        raise


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    print("📖 Extracting text from PDF...")
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        print("✅ Text Extracted.")
        return text
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        raise


def split_text_into_chunks(text, chunk_size=1000, chunk_overlap=200):
    """Splits text into overlapping chunks."""
    print("Splitting text into chunks...")
    # Use a more robust splitter
    words = re.split(r'\s+', text)
    chunks = []
    for i in range(0, len(words), chunk_size - chunk_overlap):
        chunks.append(" ".join(words[i: i + chunk_size]))
    print(f"✅ Text split into {len(chunks)} chunks.")
    return chunks


def get_embeddings(texts):
    """Generates embeddings for a list of texts using Vertex AI."""
    print(f"🧠 Generating embeddings with '{EMBEDDING_MODEL_ID}'...")
    # CORRECT: Use TextEmbeddingModel for this task
    model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_ID)
    try:
        embeddings = model.get_embeddings(texts)
        # Extract the numerical vectors from the response
        vectors = [e.values for e in embeddings]
        print("✅ Embeddings generated.")
        return vectors
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        raise


def create_faiss_index(embeddings):
    """Creates a FAISS index for a list of embeddings."""
    print("🤖 Creating FAISS vector index...")
    # The output dimension of text-embedding-004 is 768
    dimension = 3072
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    print(f"✅ FAISS index created with {index.ntotal} vectors of dimension {dimension}.")
    return index


class RagPipeline:
    """A retrieval-augmented generation (RAG) pipeline."""

    def __init__(self, index, chunks):
        self.index = index
        self.chunks = chunks
        self.model = GenerativeModel(GENERATION_MODEL_ID)
        self.embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_ID)

    def answer_question(self, query, top_k=3):
        """Answers a question based on the indexed document."""
        print(f"\n🔍 Searching for answer to: '{query}'")
        # Get embedding for the query
        query_embedding = self.embedding_model.get_embeddings([query])[0].values

        # Search the FAISS index
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32), top_k
        )

        # Retrieve context from chunks
        context = "\n---\n".join([self.chunks[i] for i in indices[0]])

        prompt = f"""
        You are a helpful assistant. Answer the user's query based ONLY on the following context.
        If the context does not contain the answer, state that the answer is not found in the document.

        Context:
        {context}

        Query: {query}

        Answer:
        """

        print("✍️ Generating answer...")
        response = self.model.generate_content(prompt)
        return response.text


# ...existing code...

def run_rag_pipeline(pdf_url: str, questions: list, pdf_path: str = "pm_kisan.pdf") -> dict:
    """
    Runs the RAG pipeline for a given PDF and list of questions.
    Returns a dictionary mapping each question to its answer.
    """
    initialize_vertex_ai()

    # 1. Ingest and process the document
    download_pdf(pdf_url, pdf_path)
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text_into_chunks(text)

    # 2. Create the vector index
    embeddings = get_embeddings(chunks)
    index = create_faiss_index(embeddings)

    # 3. Initialize the RAG pipeline
    rag_pipeline = RagPipeline(index, chunks)

    # 4. Ask questions and collect answers
    answers = {}
    for question in questions:
        answer = rag_pipeline.answer_question(question)
        answers[question] = answer

    return answers



async def generation_offline(query: str) -> str:
    """
    Async wrapper for offline RAG generation.
    Downloads and processes the default PDF, then answers the query.
    """
    pdf_url = "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2021/nov/doc2021112361.pdf"
    questions = [query]
    loop = asyncio.get_event_loop()
    # Run the sync RAG pipeline in a thread to avoid blocking
    answers = await loop.run_in_executor(None, run_rag_pipeline, pdf_url, questions)
    return answers[query]