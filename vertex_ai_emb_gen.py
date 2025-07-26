from __future__ import annotations

import re
import unicodedata
import os
from typing import List, Optional, Dict, Any
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
import vertexai

class VertexAIEmbeddingGenerator:
    """
    Enhanced Vertex AI embedding generator with preprocessing capabilities
    for different input sources (text, speech, OCR)
    """
    
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """Initialize the embedding generator"""
        print("Initializing Vertex AI embedding generation...")
        
        # Use provided project or fall back to environment variable or default
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT', 'serene-flare-466616-m5')
        self.location = location
        
        # Initialize Vertex AI
        vertexai.init(
            project=self.project_id,
            location=self.location
        )
        
        # Load the Gemini embedding model
        self.embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
        
        # Set embedding task and dimensionality
        self.TASK_TYPE = "RETRIEVAL_DOCUMENT"
        self.DIMENSIONALITY = 3072
        
        # Disfluency cleaning for speech input
        self.DISFLUENCIES = {"uh", "um", "you know", "like", "i mean", "so", "well", "actually"}
        
        print(f"✅ Embedding generator initialized with project: {self.project_id}")
    
    def fix_disfluencies(self, text: str) -> str:
        """Clean up speech disfluencies and normalize text"""
        text = text.lower()
        for d in self.DISFLUENCIES:
            text = re.sub(rf"\b{re.escape(d)}\b", "", text)
        text = text.replace("...", " ")
        text = re.sub(r"\s{2,}", " ", text).strip()
        if text and not text.endswith("."):
            text = text[0].upper() + text[1:] + "."
        return text

    def clean_ocr_artifacts(self, text: str) -> str:
        """Clean up OCR artifacts and normalize text"""
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"[^\x20-\x7E]", "", text)
        
        # Common OCR mistakes in agricultural context
        text = re.sub(r"\bch4nge\b", "change", text)
        text = re.sub(r"\bwor1d\b", "world", text)
        text = re.sub(r"\bcr0p\b", "crop", text)
        text = re.sub(r"\bf4rm\b", "farm", text)
        text = re.sub(r"\bp1ant\b", "plant", text)
        text = re.sub(r"\bs0il\b", "soil", text)
        
        return text.strip()

    def clean_general_text(self, text: str) -> str:
        """General text cleaning for typed input"""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove special characters but keep agricultural terms
        text = re.sub(r"[^\w\s\-\.,!?]", "", text)
        # Normalize case - keep first letter capitalized
        text = text.strip()
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        return text

    def preprocess(self, text: str, source: str = "text") -> str:
        """
        Unified preprocessing function for different input sources
        
        Args:
            text: Input text to preprocess
            source: Source type ('text', 'speech', 'ocr')
        
        Returns:
            Cleaned and preprocessed text
        """
        if not text or not text.strip():
            return ""
        
        if source == "speech":
            text = self.fix_disfluencies(text)
        elif source == "ocr":
            text = self.clean_ocr_artifacts(text)
        else:  # Default for typed text
            text = self.clean_general_text(text)
        
        return text.strip()

    def embed_text(self, text: str, source: str = "text") -> List[float]:
        """
        Generate embeddings for text with optional preprocessing
        
        Args:
            text: Input text
            source: Source type for preprocessing ('text', 'speech', 'ocr')
        
        Returns:
            List of embedding values
        """
        if not text or not text.strip():
            return [0.0] * self.DIMENSIONALITY
        
        try:
            # Preprocess text based on source
            clean_text = self.preprocess(text, source)
            
            if not clean_text:
                return [0.0] * self.DIMENSIONALITY
            
            # Generate embedding
            embedding = self.embedding_model.get_embeddings(
                [clean_text], 
                output_dimensionality=self.DIMENSIONALITY
            )
            return embedding[0].values
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.DIMENSIONALITY

    def embed_batch(self, texts: List[str], source: str = "text") -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of input texts
            source: Source type for preprocessing
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            # Preprocess all texts
            clean_texts = [self.preprocess(text, source) for text in texts]
            
            # Filter out empty texts
            valid_texts = [text for text in clean_texts if text.strip()]
            
            if not valid_texts:
                return [[0.0] * self.DIMENSIONALITY] * len(texts)
            
            # Generate embeddings in batch
            embeddings = self.embedding_model.get_embeddings(
                valid_texts,
                output_dimensionality=self.DIMENSIONALITY
            )
            
            return [emb.values for emb in embeddings]
            
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            return [[0.0] * self.DIMENSIONALITY] * len(texts)

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            'model_name': 'gemini-embedding-001',
            'dimensionality': self.DIMENSIONALITY,
            'task_type': self.TASK_TYPE,
            'project_id': self.project_id,
            'location': self.location
        }

# Global instance for easy importing
_global_embedding_generator = None

def get_embedding_generator(project_id: str = None, location: str = "us-central1") -> VertexAIEmbeddingGenerator:
    """Get or create global embedding generator instance"""
    global _global_embedding_generator
    
    if _global_embedding_generator is None:
        _global_embedding_generator = VertexAIEmbeddingGenerator(project_id, location)
    
    return _global_embedding_generator

# Convenience functions for backward compatibility
def embed_text(text: str, source: str = "text") -> List[float]:
    """Convenience function to generate embeddings"""
    generator = get_embedding_generator()
    return generator.embed_text(text, source)

def preprocess(text: str, source: str = "text") -> str:
    """Convenience function for text preprocessing"""
    generator = get_embedding_generator()
    return generator.preprocess(text, source)

# Example usage (only run if script is executed directly)
if __name__ == "__main__":
    print("🧪 Testing Vertex AI Embedding Generation...")
    
    # Initialize generator
    generator = VertexAIEmbeddingGenerator()
    
    # Example inputs from different sources
    test_sources = {
        "typed": "AI will help farmers improve crop yields and disease detection.",
        "speech": "uh AI is uh going to help farmers with... crop disease detection you know",
        "ocr": "AI will he1p f4rmers impr0ve cr0p yields.\n\nDisease detection iz important."
    }
    
    print("Testing preprocessing and embedding generation:\n")
    
    for source_type, raw_text in test_sources.items():
        clean_text = generator.preprocess(raw_text, source_type)
        embedding = generator.embed_text(raw_text, source_type)
        
        print(f"📝 {source_type.upper()} INPUT:")
        print(f"Raw Text: {raw_text}")
        print(f"Cleaned Text: {clean_text}")
        print(f"Embedding (first 5 dims): {embedding[:5]}")
        print(f"Embedding dimension: {len(embedding)}\n")
    
    # Test batch processing
    batch_texts = [
        "What is wheat price today?",
        "My tomato plants have yellow leaves",
        "Show me government farming schemes"
    ]
    
    print("Testing batch embedding generation:")
    batch_embeddings = generator.embed_batch(batch_texts)
    for i, (text, emb) in enumerate(zip(batch_texts, batch_embeddings)):
        print(f"Text {i+1}: {text[:30]}... → Embedding dim: {len(emb)}")
    
    print(f"\n✅ All tests completed successfully!")
    print(f"Model info: {generator.get_model_info()}")
