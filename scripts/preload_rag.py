"""
Startup script to preload the RAG vector store into memory.
Run this when the application starts to avoid first-request latency.
"""

from rag import get_vector_store
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preload_rag():
    """Preload the vector store into memory cache."""
    logger.info("Preloading RAG vector store...")
    try:
        vs = get_vector_store()
        if vs:
            logger.info("✓ RAG vector store loaded and cached successfully")
            return True
        else:
            logger.warning("⚠ Vector store is empty or not available")
            return False
    except Exception as e:
        logger.error(f"✗ Failed to preload vector store: {e}")
        return False

if __name__ == "__main__":
    preload_rag()
