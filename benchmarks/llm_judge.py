"""
LLM-as-a-Judge Evaluation Script
Evaluates RAG strategy by having a second LLM judge the responses.

Usage:
    python llm_judge.py
    python llm_judge.py --judge-model mistral
    python llm_judge.py --judge-model gpt-4o-mini --judge-provider openai
    python llm_judge.py --help
"""

import os
import csv
import json
import uuid
import argparse
import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import FAISS

from logging_config import setup_logger

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logger("llm_judge")

# Constants
DATA_DIR = "./data"
QUESTIONS_FILE = "./data/questions.csv"
DB_PATH = "./data/faiss_index"
OUTPUT_FILE = "./data/evaluation_report.json"
DEFAULT_MAIN_MODEL = "llama3.1:8b"
DEFAULT_JUDGE_MODEL = "gpt-oss:20b"


# ============================================================================
# EVALUATION PROMPTS
# ============================================================================

RAG_PROMPT_TEMPLATE = """You are a helpful assistant. Use the following context to answer the question.
If you cannot find the answer in the context, say you don't have enough information.

Context:
{context}

Question: {question}

Answer:"""

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator assessing the quality of an AI assistant's response.

**Question asked:**
{question}

**Expected answer (ground truth):**
{expected_answer}

**Generated answer by AI:**
{generated_answer}

**RAG Context used:**
{rag_context}

---

Evaluate the generated answer on the following criteria, scoring each from 0 to 10:

1. **Factual Accuracy**: How accurate is the answer compared to the expected answer? Are the facts correct?
2. **Completeness**: Does the answer cover all important points from the expected answer?
3. **Relevance**: Is the answer relevant and focused on the question? No off-topic information?
4. **Coherence**: Is the answer clear, well-structured, and easy to understand?

---

Respond ONLY in the following JSON format (no other text):
{{
    "accuracy": <0-10>,
    "completeness": <0-10>,
    "relevance": <0-10>,
    "coherence": <0-10>,
    "reasoning": "<brief explanation of your evaluation>"
}}
"""


# ============================================================================
# LLM PROVIDERS
# ============================================================================

def get_llm(model: str, provider: str = "ollama", temperature: float = 0.1):
    """Get LLM instance based on provider."""
    if provider == "ollama":
        return OllamaLLM(model=model, temperature=temperature)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_embeddings(model: str = DEFAULT_MAIN_MODEL):
    """Get embeddings model."""
    return OllamaEmbeddings(model=model)


# ============================================================================
# RAG FUNCTIONS
# ============================================================================

def load_vector_store(embeddings_model: str = DEFAULT_MAIN_MODEL) -> Optional[FAISS]:
    """Load the FAISS vector store."""
    if not os.path.exists(DB_PATH):
        logger.error(f"Vector store not found at {DB_PATH}")
        return None
    
    try:
        embeddings = get_embeddings(embeddings_model)
        vector_store = FAISS.load_local(
            DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        return vector_store
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
        return None


def retrieve_context(vector_store: FAISS, query: str, k: int = 3) -> str:
    """Retrieve relevant context from vector store."""
    try:
        results = vector_store.similarity_search(query, k=k)
        context = "\n\n".join([doc.page_content for doc in results])
        return context
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return ""


def generate_answer(llm, question: str, context: str) -> str:
    """Generate answer using main LLM with RAG context."""
    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
    try:
        response = llm.invoke(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return f"Error: {e}"


# ============================================================================
# JUDGE FUNCTIONS
# ============================================================================

def evaluate_response(
    judge_llm,
    question: str,
    expected_answer: str,
    generated_answer: str,
    rag_context: str
) -> Dict[str, Any]:
    """Have the judge LLM evaluate a response."""
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        expected_answer=expected_answer,
        generated_answer=generated_answer,
        rag_context=rag_context[:2000]  # Limit context size
    )
    
    try:
        response = judge_llm.invoke(prompt)
        
        # Parse JSON response
        # Find JSON in response (handle potential extra text)
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            scores = json.loads(json_str)
            
            # Calculate total score (average)
            numeric_scores = [
                scores.get("accuracy", 0),
                scores.get("completeness", 0),
                scores.get("relevance", 0),
                scores.get("coherence", 0)
            ]
            scores["total_score"] = round(sum(numeric_scores) / len(numeric_scores), 2)
            return scores
        else:
            logger.warning(f"Could not parse JSON from judge response: {response[:200]}")
            return {
                "accuracy": 0,
                "completeness": 0,
                "relevance": 0,
                "coherence": 0,
                "total_score": 0,
                "reasoning": f"Failed to parse: {response[:200]}"
            }
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing error: {e}")
        return {
            "accuracy": 0,
            "completeness": 0,
            "relevance": 0,
            "coherence": 0,
            "total_score": 0,
            "reasoning": f"JSON parse error: {e}"
        }
    except Exception as e:
        logger.error(f"Error in evaluation: {e}")
        return {
            "accuracy": 0,
            "completeness": 0,
            "relevance": 0,
            "coherence": 0,
            "total_score": 0,
            "reasoning": f"Error: {e}"
        }


# ============================================================================
# DATA FUNCTIONS
# ============================================================================

def load_questions(filepath: str) -> List[Dict[str, str]]:
    """Load questions from CSV file."""
    questions = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up the question field (remove [cite_start] markers)
                question = row.get('question', '').replace('[cite_start]', '').strip('"')
                answer = row.get('answer', '').replace('[cite_start]', '').strip('"')
                questions.append({
                    'question': question,
                    'answer': answer,
                    'reference': row.get('reference', '')
                })
    except Exception as e:
        logger.error(f"Error loading questions: {e}")
    
    return questions


def save_report(report: Dict[str, Any], filepath: str):
    """Save evaluation report to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Report saved to: {filepath}")


# ============================================================================
# MAIN EVALUATION
# ============================================================================

def run_evaluation(
    main_model: str = DEFAULT_MAIN_MODEL,
    main_provider: str = "ollama",
    judge_model: str = DEFAULT_JUDGE_MODEL,
    judge_provider: str = "ollama",
    questions_file: str = QUESTIONS_FILE,
    output_file: str = OUTPUT_FILE,
    k: int = 3
) -> Dict[str, Any]:
    """Run the full evaluation pipeline."""
    
    print("=" * 70)
    print("⚖️  LLM-as-a-Judge Evaluation")
    print("=" * 70)
    print(f"\n  Main Model:  {main_model} ({main_provider})")
    print(f"  Judge Model: {judge_model} ({judge_provider})")
    print(f"  RAG chunks:  {k}")
    print("-" * 70)
    
    # Initialize LLMs
    print("\n🔧 Initializing LLMs...")
    main_llm = get_llm(main_model, main_provider, temperature=0.3)
    judge_llm = get_llm(judge_model, judge_provider, temperature=0.1)
    
    # Load vector store
    print("📚 Loading vector store...")
    vector_store = load_vector_store(main_model)
    if vector_store is None:
        print("❌ Failed to load vector store. Run create_embeddings.py first.")
        return {}
    
    # Load questions
    print(f"📋 Loading questions from {questions_file}...")
    questions = load_questions(questions_file)
    print(f"   Found {len(questions)} questions")
    
    if not questions:
        print("❌ No questions found.")
        return {}
    
    # Evaluate each question
    results = []
    print("\n" + "-" * 70)
    print("🏃 Running evaluation...")
    print("-" * 70)
    
    for i, q in enumerate(questions, 1):
        question = q['question']
        expected = q['answer']
        
        print(f"\n[{i}/{len(questions)}] {question[:60]}...")
        
        # Get RAG context
        context = retrieve_context(vector_store, question, k=k)
        
        # Generate answer with main LLM
        print("   → Generating answer...")
        generated = generate_answer(main_llm, question, context)
        
        # Judge the answer
        print("   → Judging response...")
        scores = evaluate_response(
            judge_llm,
            question,
            expected,
            generated,
            context
        )
        
        result = {
            "question": question,
            "expected_answer": expected,
            "generated_answer": generated,
            "rag_context": context[:500] + "..." if len(context) > 500 else context,
            "scores": {
                "accuracy": scores.get("accuracy", 0),
                "completeness": scores.get("completeness", 0),
                "relevance": scores.get("relevance", 0),
                "coherence": scores.get("coherence", 0)
            },
            "total_score": scores.get("total_score", 0),
            "judge_reasoning": scores.get("reasoning", "")
        }
        results.append(result)
        
        print(f"   ✓ Score: {scores.get('total_score', 0)}/10")
    
    # Calculate summary statistics
    all_scores = [r["total_score"] for r in results]
    summary = {
        "total_questions": len(results),
        "avg_score": round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
        "min_score": min(all_scores) if all_scores else 0,
        "max_score": max(all_scores) if all_scores else 0,
        "score_distribution": {
            "excellent_9_10": len([s for s in all_scores if s >= 9]),
            "good_7_8": len([s for s in all_scores if 7 <= s < 9]),
            "fair_5_6": len([s for s in all_scores if 5 <= s < 7]),
            "poor_below_5": len([s for s in all_scores if s < 5])
        }
    }
    
    # Build final report
    report = {
        "evaluation_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "config": {
            "main_model": main_model,
            "main_provider": main_provider,
            "judge_model": judge_model,
            "judge_provider": judge_provider,
            "rag_chunks": k,
            "questions_file": questions_file
        },
        "summary": summary,
        "results": results
    }
    
    # Save report
    save_report(report, output_file)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 Evaluation Summary")
    print("=" * 70)
    print(f"  Total Questions: {summary['total_questions']}")
    print(f"  Average Score:   {summary['avg_score']}/10")
    print(f"  Min Score:       {summary['min_score']}/10")
    print(f"  Max Score:       {summary['max_score']}/10")
    print("\n  Score Distribution:")
    print(f"    🌟 Excellent (9-10): {summary['score_distribution']['excellent_9_10']}")
    print(f"    ✅ Good (7-8):       {summary['score_distribution']['good_7_8']}")
    print(f"    ⚠️  Fair (5-6):       {summary['score_distribution']['fair_5_6']}")
    print(f"    ❌ Poor (<5):        {summary['score_distribution']['poor_below_5']}")
    print("-" * 70)
    print(f"\n✅ Report saved to: {os.path.abspath(output_file)}")
    
    return report


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-a-Judge Evaluation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (llama3.1:8b for both)
  python llm_judge.py
  
  # Use Mistral as judge
  python llm_judge.py --judge-model mistral
  
  # Use different models
  python llm_judge.py --main-model llama3.1:8b --judge-model phi3
  
  # Use OpenAI as judge (requires OPENAI_API_KEY in .env)
  python llm_judge.py --judge-model gpt-4o-mini --judge-provider openai
  
  # Custom output file
  python llm_judge.py --output ./data/my_evaluation.json
        """
    )
    
    parser.add_argument(
        "--main-model",
        default=DEFAULT_MAIN_MODEL,
        help=f"Main LLM model for generating answers (default: {DEFAULT_MAIN_MODEL})"
    )
    
    parser.add_argument(
        "--main-provider",
        default="ollama",
        choices=["ollama", "openai"],
        help="Provider for main LLM (default: ollama)"
    )
    
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"Judge LLM model for evaluation (default: {DEFAULT_JUDGE_MODEL})"
    )
    
    parser.add_argument(
        "--judge-provider",
        default="ollama",
        choices=["ollama", "openai"],
        help="Provider for judge LLM (default: ollama)"
    )
    
    parser.add_argument(
        "--questions",
        default=QUESTIONS_FILE,
        help=f"Path to questions CSV file (default: {QUESTIONS_FILE})"
    )
    
    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help=f"Path for output report JSON (default: {OUTPUT_FILE})"
    )
    
    parser.add_argument(
        "-k",
        type=int,
        default=3,
        help="Number of RAG chunks to retrieve (default: 3)"
    )
    
    args = parser.parse_args()
    
    run_evaluation(
        main_model=args.main_model,
        main_provider=args.main_provider,
        judge_model=args.judge_model,
        judge_provider=args.judge_provider,
        questions_file=args.questions,
        output_file=args.output,
        k=args.k
    )


if __name__ == "__main__":
    main()
