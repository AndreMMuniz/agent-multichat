from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from logging_config import setup_logger

# Configure logging
logger = setup_logger("rag_system")

# Constants
DATA_DIR = "./data"
DB_PATH = "./data/faiss_index"
MODEL_NAME = "llama3.1:8b"

def initialize_vector_store():
    """
    Scans the data directory, loads text and PDF files, 
    creates embeddings, and saves a local FAISS index.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.warning(f"Created {DATA_DIR} directory. Please add files.")
        return None

    documents = []
    
    # Load .txt files
    txt_loader = DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader)
    try:
        txt_docs = txt_loader.load()
        documents.extend(txt_docs)
        logger.info(f"Loaded {len(txt_docs)} text documents.")
    except Exception as e:
        logger.warning(f"Error loading text files: {e}")

    # Load .pdf files
    pdf_loader = DirectoryLoader(DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    try:
        pdf_docs = pdf_loader.load()
        documents.extend(pdf_docs)
        logger.info(f"Loaded {len(pdf_docs)} PDF documents.")
    except Exception as e:
        logger.warning(f"Error loading PDF files: {e}")
        
    if not documents:
        logger.warning("No documents found to index.")
        return None
        
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    
    # Create Vector Store
    try:
        embeddings = OllamaEmbeddings(model=MODEL_NAME)
        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local(DB_PATH)
        logger.info("FAISS index saved successfully.")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        return None

# Global cache for vector store (loaded once at startup)
_vector_store_cache = None
_cache_lock = None

def _get_cache_lock():
    """Get or create the cache lock (thread-safe)."""
    global _cache_lock
    if _cache_lock is None:
        import threading
        _cache_lock = threading.Lock()
    return _cache_lock

def get_vector_store():
    """
    Get the cached vector store, initializing it if necessary.
    This is called ONCE at startup and reused for all requests.
    Thread-safe singleton pattern.
    """
    global _vector_store_cache
    
    # Fast path: already loaded
    if _vector_store_cache is not None:
        return _vector_store_cache
    
    # Slow path: need to load (thread-safe)
    lock = _get_cache_lock()
    with lock:
        # Double-check pattern
        if _vector_store_cache is not None:
            return _vector_store_cache
            
        logger.info("Loading vector store into memory (one-time operation)...")
        
        # Check if index exists
        if not os.path.exists(DB_PATH):
            logger.warning("Vector store not found. Initializing...")
            _vector_store_cache = initialize_vector_store()
        else:
            try:
                embeddings = OllamaEmbeddings(model=MODEL_NAME)
                _vector_store_cache = FAISS.load_local(
                    DB_PATH, 
                    embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info("✓ Vector store loaded successfully and cached in memory")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
                logger.info("Attempting to rebuild index...")
                _vector_store_cache = initialize_vector_store()
        
        return _vector_store_cache

def retrieve_context(query: str, k: int = 3):
    """
    Retrieves the most relevant context chunks for a given query.
    Uses cached vector store (no disk I/O after first load).
    """
    try:
        vector_store = get_vector_store()
        
        if vector_store is None:
            logger.warning("Vector store not available")
            return ""
        
        results = vector_store.similarity_search(query, k=k)
        
        # Combine content
        context = "\n\n".join([doc.page_content for doc in results])
        return context
        
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return ""

def reload_vector_store():
    """
    Force reload of the vector store (e.g., after updating documents).
    Call this after adding new files to data/ folder.
    """
    global _vector_store_cache
    lock = _get_cache_lock()
    with lock:
        logger.info("Reloading vector store...")
        _vector_store_cache = None
        initialize_vector_store()
        _vector_store_cache = get_vector_store()
        logger.info("✓ Vector store reloaded")

if __name__ == "__main__":
    # Test run
    print("Initializing vector store (first time)...")
    initialize_vector_store()
    
    print("\nPreloading vector store into cache...")
    vs = get_vector_store()
    print(f"✓ Vector store cached: {vs is not None}")
    
    print("\nTesting retrieval (should be fast, no disk I/O)...")
    ctx = retrieve_context("horario de atendimento")
    print(f"Retrieved Context:\n{ctx}")
    
    print("\nTesting second retrieval (should reuse cache)...")
    ctx2 = retrieve_context("valores")
    print(f"Retrieved Context:\n{ctx2}")
