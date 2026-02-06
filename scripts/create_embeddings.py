"""
Embedding Creation Script
Reads the parsed documents JSON and creates FAISS embeddings.
"""

import os
import json
import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from logging_config import setup_logger

# Configure logging
logger = setup_logger("embedding_creator")

# Constants
PARSED_JSON_PATH = "./data/parsed_documents.json"
DB_PATH = "./data/faiss_index"
MODEL_NAME = "llama3.1:8b"

# Chunking settings
CHUNK_SIZE = 700
CHUNK_OVERLAP = 200


def load_parsed_documents(json_path: str) -> Dict[str, Any]:
    """Load parsed documents from JSON file."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Parsed documents file not found: {json_path}\n"
            "Please run parse_documents.py first."
        )
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def json_to_langchain_documents(parsed_data: Dict[str, Any]) -> List[Document]:
    """Convert parsed JSON data to LangChain Document objects."""
    documents = []
    
    for doc in parsed_data.get("documents", []):
        filename = doc.get("filename", "unknown")
        filepath = doc.get("filepath", "unknown")
        doc_type = doc.get("type", "unknown")
        
        for i, chunk in enumerate(doc.get("chunks", [])):
            content = chunk.get("content", "")
            if not content.strip():
                continue
            
            # Build metadata
            metadata = {
                "source": filepath,
                "filename": filename,
                "doc_type": doc_type,
                "chunk_index": i,
                **chunk.get("metadata", {})
            }
            
            documents.append(Document(
                page_content=content,
                metadata=metadata
            ))
    
    return documents


def split_documents(documents: List[Document]) -> List[Document]:
    """Split documents into smaller chunks for better embedding."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    return chunks


def create_vector_store(chunks: List[Document]) -> FAISS:
    """Create FAISS vector store from document chunks."""
    logger.info(f"Creating embeddings using model: {MODEL_NAME}")
    
    embeddings = OllamaEmbeddings(model=MODEL_NAME)
    
    # Create vector store
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    return vector_store


def save_vector_store(vector_store: FAISS, path: str):
    """Save vector store to disk."""
    vector_store.save_local(path)
    logger.info(f"Vector store saved to: {path}")


def create_embedding_report(
    parsed_data: Dict[str, Any],
    num_docs: int,
    num_chunks: int,
    output_path: str
):
    """Create a report file with embedding statistics."""
    report = {
        "created_at": datetime.now().isoformat(),
        "source_json": PARSED_JSON_PATH,
        "model": MODEL_NAME,
        "chunk_settings": {
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP
        },
        "statistics": {
            "original_documents": len(parsed_data.get("documents", [])),
            "langchain_documents": num_docs,
            "final_chunks": num_chunks
        },
        "source_summary": parsed_data.get("summary", {})
    }
    
    report_path = os.path.join(output_path, "embedding_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Report saved to: {report_path}")
    return report


def main():
    """Main entry point."""
    print("=" * 60)
    print("🔮 Embedding Creator")
    print("=" * 60)
    print(f"\nSource: {PARSED_JSON_PATH}")
    print(f"Model: {MODEL_NAME}")
    print(f"Output: {DB_PATH}")
    print("-" * 60)
    
    # Step 1: Load parsed documents
    print("\n📖 Loading parsed documents...")
    try:
        parsed_data = load_parsed_documents(PARSED_JSON_PATH)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return
    
    # Step 2: Convert to LangChain documents
    print("🔄 Converting to LangChain format...")
    documents = json_to_langchain_documents(parsed_data)
    print(f"   Found {len(documents)} document segments")
    
    if not documents:
        print("\n❌ No documents found to process.")
        print("   Make sure parse_documents.py generated valid content.")
        return
    
    # Step 3: Split into chunks
    print("✂️  Splitting into chunks...")
    chunks = split_documents(documents)
    print(f"   Created {len(chunks)} chunks")
    
    # Step 4: Create embeddings
    print("🧠 Creating embeddings (this may take a while)...")
    try:
        vector_store = create_vector_store(chunks)
    except Exception as e:
        print(f"\n❌ Error creating embeddings: {e}")
        print("   Make sure Ollama is running with the llama3.1:8b model.")
        print("   Run: ollama pull llama3.1:8b")
        return
    
    # Step 5: Save vector store
    print("💾 Saving vector store...")
    save_vector_store(vector_store, DB_PATH)
    
    # Step 6: Create report
    print("📝 Creating report...")
    report = create_embedding_report(
        parsed_data,
        len(documents),
        len(chunks),
        DB_PATH
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Embedding Summary")
    print("=" * 60)
    print(f"  Original Documents: {report['statistics']['original_documents']}")
    print(f"  Document Segments: {report['statistics']['langchain_documents']}")
    print(f"  Final Chunks: {report['statistics']['final_chunks']}")
    print(f"  Model Used: {MODEL_NAME}")
    print(f"  Chunk Size: {CHUNK_SIZE} chars")
    print(f"  Chunk Overlap: {CHUNK_OVERLAP} chars")
    print("-" * 60)
    print(f"\n✅ Vector store saved to: {os.path.abspath(DB_PATH)}")
    print("\n🚀 Ready to use! The RAG system will automatically use the new embeddings.")


def test_retrieval(query: str = "teste"):
    """Test the retrieval functionality."""
    print(f"\n🔍 Testing retrieval with query: '{query}'")
    
    if not os.path.exists(DB_PATH):
        print("❌ Vector store not found. Run main() first.")
        return
    
    embeddings = OllamaEmbeddings(model=MODEL_NAME)
    vector_store = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    
    results = vector_store.similarity_search(query, k=3)
    
    print(f"\n📄 Found {len(results)} results:")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i + 1} ---")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Content: {doc.page_content[:200]}...")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        query = sys.argv[2] if len(sys.argv) > 2 else "teste"
        test_retrieval(query)
    else:
        main()
