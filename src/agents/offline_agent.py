import os
import re
import PyPDF2
import requests
import faiss
import numpy as np

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


def main():
    """Main function to run the RAG pipeline."""
    initialize_vertex_ai()

    pdf_url = "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2021/nov/doc2021112361.pdf"
    pdf_path = "pm_kisan.pdf"

    # 1. Ingest and process the document
    download_pdf(pdf_url, pdf_path)
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text_into_chunks(text)

    # 2. Create the vector index
    embeddings = get_embeddings(chunks)
    index = create_faiss_index(embeddings)

    # 3. Initialize the RAG pipeline
    rag_pipeline = RagPipeline(index, chunks)

    # 4. Ask questions
    question_1 = "What is the PM-KISAN scheme?"
    answer_1 = rag_pipeline.answer_question(question_1)
    print(f"\n💡 Answer 1:\n{answer_1}")

    question_2 = "What is the total financial outlay for the scheme?"
    answer_2 = rag_pipeline.answer_question(question_2)
    print(f"\n💡 Answer 2:\n{answer_2}")


if __name__ == "__main__":
    main()





# import os
# import re
# import json
# import requests
# import numpy as np

# # Import the necessary classes from the Vertex AI SDK
# from google.cloud import aiplatform
# from google.cloud import storage
# from vertexai.generative_models import GenerativeModel
# from vertexai.language_models import TextEmbeddingModel

# # --- Configuration ---
# PROJECT_ID = "serene-flare-466616-m5"
# LOCATION = "us-central1"
# BUCKET_NAME = "serene-flare-466616-m5-vector-embeddings"
# BUCKET_URI = f"gs://{BUCKET_NAME}"

# # Model Configuration
# GENERATION_MODEL_ID = "gemini-2.5-flash"
# EMBEDDING_MODEL_ID = "gemini-embedding-001"
# EMBEDDING_DIMENSION = 3072

# def initialize_vertex_ai():
#     """Initializes the Vertex AI SDK."""
#     print("🌍 Initializing Vertex AI...")
#     aiplatform.init(project=PROJECT_ID, location=LOCATION, staging_bucket=BUCKET_URI)
#     print("✅ Vertex AI Initialized.")


# def download_pdf(url, save_path):
#     """Downloads a PDF from a URL."""
#     print(f"📄 Downloading PDF from {url}...")
#     try:
#         response = requests.get(url, timeout=30)
#         response.raise_for_status()
#         with open(save_path, "wb") as f:
#             f.write(response.content)
#         print("✅ PDF Downloaded.")
#     except requests.exceptions.RequestException as e:
#         print(f"❌ Error downloading PDF: {e}")
#         raise


# def extract_text_from_pdf(pdf_path):
#     """Extracts text from a PDF file."""
#     print("📖 Extracting text from PDF...")
#     text = ""
#     try:
#         with open(pdf_path, "rb") as f:
#             # Note: PyPDF2 is used here, but other libraries like pdfplumber might offer better text extraction.
#             from PyPDF2 import PdfReader
#             reader = PdfReader(f)
#             for page in reader.pages:
#                 page_text = page.extract_text()
#                 if page_text:
#                     text += re.sub(r'\s+', ' ', page_text).strip() + "\n"
#         print("✅ Text Extracted.")
#         return text
#     except Exception as e:
#         print(f"❌ Error extracting text: {e}")
#         raise


# def split_text_into_chunks(text, chunk_size=500, chunk_overlap=100):
#     """Splits text into overlapping chunks of words."""
#     print("Splitting text into chunks...")
#     words = re.split(r'\s+', text)
#     chunks = []
#     for i in range(0, len(words), chunk_size - chunk_overlap):
#         chunks.append(" ".join(words[i: i + chunk_size]))
#     print(f"✅ Text split into {len(chunks)} chunks.")
#     return chunks


# class RagPipeline:
#     """A RAG pipeline using a deployed Vertex AI Vector Search endpoint."""

#     def __init__(self, endpoint, chunks_dict):
#         """
#         Initializes the pipeline.
#         Args:
#             endpoint: A deployed Vertex AI MatchingEngineIndexEndpoint object.
#             chunks_dict: A dictionary mapping custom string IDs to text chunks.
#         """
#         self.index_endpoint = endpoint
#         self.chunks = chunks_dict  # Store the dictionary
#         self.model = GenerativeModel(GENERATION_MODEL_ID)
#         self.embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_ID)

#     def answer_question(self, query, top_k=3):
#         """Answers a question based on the indexed document."""
#         print(f"\n🔍 Searching for answer to: '{query}'")

#         # Get embedding for the query
#         query_embedding = self.embedding_model.get_embeddings([query])[0].values

#         # Search the Vector Search index endpoint
#         response = self.index_endpoint.find_neighbors(
#             queries=[query_embedding],
#             num_neighbors=top_k,
#             deployed_index_id="deploy_kisan_1753377086327"
#         )

#         # Retrieve context from chunks using the IDs returned by Vector Search
#         context = ""
#         if response and response[0]:
#             # CORRECT: No int() conversion. Look up string IDs in the dictionary.
#             retrieved_ids = [neighbor.id for neighbor in response[0]]
#             context = "\n---\n".join([self.chunks[retrieved_id] for retrieved_id in retrieved_ids])
#             print(f"✅ Found {len(retrieved_ids)} relevant chunks.")
#         else:
#             print("❌ No relevant chunks found in the document.")
#             return "The answer could not be found in the provided document."

#         prompt = f"""
#         You are a helpful assistant. Answer the user's query based ONLY on the following context.
#         If the context does not contain the answer, state that the answer is not found in the document.

#         Context:
#         {context}

#         Query: {query}

#         Answer:
#         """

#         print("✍️ Generating answer...")
#         generation_response = self.model.generate_content(prompt)
#         return generation_response.text


# def query_existing_index():
#     """
#     Connects to an existing, deployed Vector Search endpoint and runs queries.
#     """
#     initialize_vertex_ai()

#     # CORRECT: Use the long numerical ID for the endpoint.
#     ENDPOINT_ID = "8844614470341754880"

#     print("\n--- Starting Querying ---")
#     try:
#         rag_endpoint = aiplatform.MatchingEngineIndexEndpoint(ENDPOINT_ID)
#         print(f"✅ Successfully connected to endpoint: {rag_endpoint.display_name}")
#     except Exception as e:
#         print(f"❌ Failed to connect to endpoint ID {ENDPOINT_ID}. Error: {e}")
#         return

#     # The RagPipeline needs the original chunks to provide context.
#     # In a real app, you'd fetch these from a database or cloud storage.
#     # For this example, we re-process the PDF to get them.
#     print("Re-processing PDF to get text chunks for context...")
#     pdf_url = "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2021/nov/doc2021112361.pdf"
#     pdf_path = "pm_kisan.pdf"
#     if not os.path.exists(pdf_path):
#         download_pdf(pdf_url, pdf_path)
#     text = extract_text_from_pdf(pdf_path)
#     chunks_list = split_text_into_chunks(text)

#     # CORRECT: Create a dictionary mapping custom IDs to chunks.
#     # This must use the same ID format you used when uploading the embeddings.
#     chunks_dict = {f"agri_fertilizer_{i:03d}": chunk for i, chunk in enumerate(chunks_list)}

#     # Initialize the RAG pipeline with the live endpoint and the chunks dictionary
#     rag_pipeline = RagPipeline(rag_endpoint, chunks_dict)

#     # Ask questions
#     question_1 = "What is the PM-KISAN scheme?"
#     answer_1 = rag_pipeline.answer_question(question_1)
#     print(f"\n💡 Answer 1:\n{answer_1}")

#     question_2 = "What is the total financial outlay for the scheme?"
#     answer_2 = rag_pipeline.answer_question(question_2)
#     print(f"\n💡 Answer 2:\n{answer_2}")


# if __name__ == "__main__":
#     query_existing_index()