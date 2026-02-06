"""
Document Parser Script
Reads documents from ./data folder (PDF, DOCX, PNG, JPG, TXT, CSV, etc.)
and generates a structured JSON file for embedding.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Document Loaders
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
)

# Image OCR (requires pytesseract and Pillow)
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠ pytesseract/Pillow not installed. Image OCR will be skipped.")
    print("  Install with: pip install pytesseract Pillow")

import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logger

# Configure logging
logger = setup_logger("document_parser")

# Constants
DATA_DIR = "./data"
OUTPUT_FILE = "./data/parsed_documents.json"
SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_DOCX_EXTENSIONS = {".docx", ".doc"}
SUPPORTED_CSV_EXTENSIONS = {".csv"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}


def get_file_hash(filepath: str) -> str:
    """Generate MD5 hash of file for change detection."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def extract_text_from_image(filepath: str) -> str:
    """Extract text from image using OCR."""
    if not OCR_AVAILABLE:
        return ""
    
    try:
        image = Image.open(filepath)
        text = pytesseract.image_to_string(image, lang='por+eng')
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR failed for {filepath}: {e}")
        return ""


def load_text_file(filepath: str) -> List[Dict[str, Any]]:
    """Load text file and return documents."""
    try:
        loader = TextLoader(filepath, encoding='utf-8')
        docs = loader.load()
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            loader = TextLoader(filepath, encoding='latin-1')
            docs = loader.load()
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        except Exception as e:
            logger.error(f"Failed to load text file {filepath}: {e}")
            return []
    except Exception as e:
        logger.error(f"Failed to load text file {filepath}: {e}")
        return []


def load_pdf_file(filepath: str) -> List[Dict[str, Any]]:
    """Load PDF file and return documents."""
    try:
        loader = PyPDFLoader(filepath)
        docs = loader.load()
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    except Exception as e:
        logger.error(f"Failed to load PDF file {filepath}: {e}")
        return []


def load_docx_file(filepath: str) -> List[Dict[str, Any]]:
    """Load DOCX file and return documents."""
    try:
        loader = UnstructuredWordDocumentLoader(filepath)
        docs = loader.load()
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    except Exception as e:
        logger.error(f"Failed to load DOCX file {filepath}: {e}")
        return []


def load_csv_file(filepath: str) -> List[Dict[str, Any]]:
    """Load CSV file and return documents."""
    try:
        loader = CSVLoader(filepath, encoding='utf-8')
        docs = loader.load()
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    except UnicodeDecodeError:
        try:
            loader = CSVLoader(filepath, encoding='latin-1')
            docs = loader.load()
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        except Exception as e:
            logger.error(f"Failed to load CSV file {filepath}: {e}")
            return []
    except Exception as e:
        logger.error(f"Failed to load CSV file {filepath}: {e}")
        return []


def load_image_file(filepath: str) -> List[Dict[str, Any]]:
    """Load image file and extract text using OCR."""
    text = extract_text_from_image(filepath)
    if text:
        return [{
            "content": text,
            "metadata": {
                "source": filepath,
                "type": "image_ocr"
            }
        }]
    return []


def parse_document(filepath: str) -> Dict[str, Any]:
    """Parse a single document and return structured data."""
    path = Path(filepath)
    extension = path.suffix.lower()
    
    # Get file info
    stat = os.stat(filepath)
    file_info = {
        "filename": path.name,
        "filepath": str(path.absolute()),
        "extension": extension,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "file_hash": get_file_hash(filepath),
    }
    
    # Load content based on extension
    chunks = []
    
    if extension in SUPPORTED_TEXT_EXTENSIONS:
        chunks = load_text_file(filepath)
        file_info["type"] = "text"
        
    elif extension in SUPPORTED_PDF_EXTENSIONS:
        chunks = load_pdf_file(filepath)
        file_info["type"] = "pdf"
        
    elif extension in SUPPORTED_DOCX_EXTENSIONS:
        chunks = load_docx_file(filepath)
        file_info["type"] = "docx"
        
    elif extension in SUPPORTED_CSV_EXTENSIONS:
        chunks = load_csv_file(filepath)
        file_info["type"] = "csv"
        
    elif extension in SUPPORTED_IMAGE_EXTENSIONS:
        chunks = load_image_file(filepath)
        file_info["type"] = "image"
        
    else:
        logger.warning(f"Unsupported file type: {extension}")
        file_info["type"] = "unsupported"
    
    # Build document object
    document = {
        **file_info,
        "chunks": chunks,
        "chunk_count": len(chunks),
        "total_chars": sum(len(chunk["content"]) for chunk in chunks),
    }
    
    return document


def scan_directory(directory: str) -> List[str]:
    """Scan directory for supported files."""
    all_extensions = (
        SUPPORTED_TEXT_EXTENSIONS |
        SUPPORTED_PDF_EXTENSIONS |
        SUPPORTED_DOCX_EXTENSIONS |
        SUPPORTED_CSV_EXTENSIONS |
        SUPPORTED_IMAGE_EXTENSIONS
    )
    
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Skip hidden directories and faiss_index
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'faiss_index']
        
        for filename in filenames:
            if not filename.startswith('.'):
                ext = Path(filename).suffix.lower()
                if ext in all_extensions:
                    files.append(os.path.join(root, filename))
    
    return files


def parse_all_documents() -> Dict[str, Any]:
    """Parse all documents in the data directory."""
    logger.info(f"Scanning directory: {DATA_DIR}")
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.warning(f"Created {DATA_DIR} directory. Please add files.")
        return {"documents": [], "summary": {}}
    
    # Find all supported files
    files = scan_directory(DATA_DIR)
    logger.info(f"Found {len(files)} supported files")
    
    # Parse each document
    documents = []
    stats = {
        "total_files": 0,
        "total_chunks": 0,
        "total_chars": 0,
        "by_type": {}
    }
    
    for filepath in files:
        logger.info(f"Parsing: {filepath}")
        doc = parse_document(filepath)
        
        if doc["chunk_count"] > 0:
            documents.append(doc)
            stats["total_files"] += 1
            stats["total_chunks"] += doc["chunk_count"]
            stats["total_chars"] += doc["total_chars"]
            
            # Count by type
            doc_type = doc["type"]
            if doc_type not in stats["by_type"]:
                stats["by_type"][doc_type] = {"files": 0, "chunks": 0}
            stats["by_type"][doc_type]["files"] += 1
            stats["by_type"][doc_type]["chunks"] += doc["chunk_count"]
        else:
            logger.warning(f"No content extracted from: {filepath}")
    
    # Build output
    output = {
        "parsed_at": datetime.now().isoformat(),
        "source_directory": os.path.abspath(DATA_DIR),
        "summary": stats,
        "documents": documents
    }
    
    return output


def save_to_json(data: Dict[str, Any], output_path: str):
    """Save parsed data to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved parsed documents to: {output_path}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("📄 Document Parser")
    print("=" * 60)
    print(f"\nScanning directory: {os.path.abspath(DATA_DIR)}")
    print("\nSupported formats:")
    print("  • Text: .txt, .md")
    print("  • PDF: .pdf")
    print("  • Word: .docx, .doc")
    print("  • Data: .csv")
    print("  • Images: .png, .jpg, .jpeg, .gif, .bmp, .tiff")
    print(f"\nOCR Available: {'✓ Yes' if OCR_AVAILABLE else '✗ No'}")
    print("-" * 60)
    
    # Parse all documents
    result = parse_all_documents()
    
    # Save to JSON
    save_to_json(result, OUTPUT_FILE)
    
    # Print summary
    summary = result["summary"]
    print("\n" + "=" * 60)
    print("📊 Parsing Summary")
    print("=" * 60)
    print(f"  Total Files Processed: {summary.get('total_files', 0)}")
    print(f"  Total Chunks Generated: {summary.get('total_chunks', 0)}")
    print(f"  Total Characters: {summary.get('total_chars', 0):,}")
    print("\n  By Type:")
    for doc_type, type_stats in summary.get("by_type", {}).items():
        print(f"    • {doc_type}: {type_stats['files']} files, {type_stats['chunks']} chunks")
    print("-" * 60)
    print(f"\n✅ Output saved to: {os.path.abspath(OUTPUT_FILE)}")
    print("\nNext step: Run create_embeddings.py to generate embeddings")


if __name__ == "__main__":
    main()
