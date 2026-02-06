"""
Automated Evaluation Script
Runs test cases from dataset to prevent regressions and measure accuracy.

Usage:
    # Run all tests
    python evaluation.py
    
    # Run specific category
    python evaluation.py --category sales
    
    # Only test intent classification
    python evaluation.py --test-type classification
    
    # Only test response generation
    python evaluation.py --test-type generation
"""

import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import asyncio
import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

from database import SessionLocal
from models import DatasetItem
from state import ChatState
from nodes import classify_message, generate_response, retrieve_knowledge
from langchain_core.messages import HumanMessage

from logging_config import setup_logger

logger = setup_logger("evaluation")

# ============================================================================
# EVALUATION FUNCTIONS (ASYNC - nodes.py uses @run_in_thread)
# ============================================================================

async def test_classification(item: DatasetItem) -> Dict:
    """Test intent classification accuracy."""
    # Simulate state
    state = ChatState(
        user_id="eval_test",
        channel="test",
        current_input=item.user_input,
        messages=[HumanMessage(content=item.user_input)],
        conversation_id=0
    )
    
    # Run classification (awaitable due to @run_in_thread)
    result = await classify_message(state)
    predicted_intent = result.get("intent")
    
    # Compare
    correct = predicted_intent == item.expected_intent
    
    return {
        "input": item.user_input,
        "expected": item.expected_intent,
        "predicted": predicted_intent,
        "correct": correct,
        "item_id": item.id
    }


async def test_generation(item: DatasetItem) -> Dict:
    """Test response generation quality."""
    # Simulate state with RAG
    state = ChatState(
        user_id="eval_test",
        channel="test",
        current_input=item.user_input,
        messages=[HumanMessage(content=item.user_input)],
        conversation_id=0,
        intent=item.expected_intent or "GENERAL"
    )
    
    # Get RAG context (awaitable)
    rag_result = await retrieve_knowledge(state)
    state.update(rag_result)
    
    # Generate response (awaitable)
    result = await generate_response(state)
    predicted_response = result.get("response")
    
    # Simple similarity check (could be improved with LLM judge)
    expected_words = set(item.expected_response.lower().split())
    predicted_words = set(predicted_response.lower().split())
    
    overlap = len(expected_words & predicted_words)
    similarity = overlap / len(expected_words) if expected_words else 0
    
    return {
        "input": item.user_input,
        "expected": item.expected_response,
        "predicted": predicted_response,
        "similarity": round(similarity, 2),
        "item_id": item.id
    }


async def run_evaluation(
    category: str = None,
    test_type: str = "both",
    quality_filter: str = None,
    output_file: str = "./data/evaluation_results.json"
):
    """Run full evaluation suite (async)."""
    db = SessionLocal()
    
    print("=" * 70)
    print("🧪 Dataset Evaluation")
    print("=" * 70)
    
    try:
        # Load test items
        query = db.query(DatasetItem).filter(DatasetItem.is_active == True)
        
        if category:
            query = query.filter(DatasetItem.category == category.lower())
        
        if quality_filter:
            query = query.filter(DatasetItem.quality == quality_filter.lower())
        
        items = query.all()
        
        if not items:
            print("❌ No test items found.")
            return
        
        print(f"\n📋 Found {len(items)} test items")
        if category:
            print(f"   Category: {category}")
        if quality_filter:
            print(f"   Quality: {quality_filter}")
        print("-" * 70)
        
        # Run tests
        classification_results = []
        generation_results = []
        
        for i, item in enumerate(items, 1):
            print(f"\n[{i}/{len(items)}] Testing: {item.user_input[:50]}...")
            
            # Classification test
            if test_type in ["both", "classification"] and item.expected_intent:
                try:
                    result = await test_classification(item)
                    classification_results.append(result)
                    status = "✅" if result["correct"] else "❌"
                    print(f"   {status} Classification: {result['predicted']} (expected: {result['expected']})")
                except Exception as e:
                    logger.error(f"Classification test failed: {e}")
                    print(f"   ❌ Classification error: {e}")
            
            # Generation test
            if test_type in ["both", "generation"] and item.expected_response:
                try:
                    result = await test_generation(item)
                    generation_results.append(result)
                    print(f"   📝 Generation similarity: {result['similarity']:.2%}")
                except Exception as e:
                    logger.error(f"Generation test failed: {e}")
                    print(f"   ❌ Generation error: {e}")
        
        # Calculate metrics
        print("\n" + "=" * 70)
        print("📊 Results Summary")
        print("=" * 70)
        
        metrics = {}
        
        if classification_results:
            correct = sum(1 for r in classification_results if r["correct"])
            total = len(classification_results)
            accuracy = correct / total
            
            print(f"\n🎯 Classification Accuracy: {accuracy:.2%} ({correct}/{total})")
            
            # Confusion matrix
            confusion = defaultdict(lambda: defaultdict(int))
            for r in classification_results:
                confusion[r["expected"]][r["predicted"]] += 1
            
            print("\nConfusion Matrix:")
            for exp, preds in confusion.items():
                print(f"  {exp}: {dict(preds)}")
            
            metrics["classification"] = {
                "accuracy": accuracy,
                "correct": correct,
                "total": total,
                "confusion_matrix": {k: dict(v) for k, v in confusion.items()}
            }
        
        if generation_results:
            avg_similarity = sum(r["similarity"] for r in generation_results) / len(generation_results)
            print(f"\n📝 Average Response Similarity: {avg_similarity:.2%}")
            
            metrics["generation"] = {
                "average_similarity": avg_similarity,
                "total": len(generation_results)
            }
        
        # Save results
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "category": category,
                "test_type": test_type,
                "quality_filter": quality_filter
            },
            "metrics": metrics,
            "classification_results": classification_results,
            "generation_results": generation_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        print("=" * 70)
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Automated Dataset Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--category", "-c",
        help="Filter by category (e.g., sales, support)"
    )
    
    parser.add_argument(
        "--test-type", "-t",
        choices=["both", "classification", "generation"],
        default="both",
        help="Type of test to run (default: both)"
    )
    
    parser.add_argument(
        "--quality", "-q",
        choices=["gold", "silver", "bronze"],
        help="Filter by quality level"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="./data/evaluation_results.json",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    # Run async evaluation
    asyncio.run(run_evaluation(
        category=args.category,
        test_type=args.test_type,
        quality_filter=args.quality,
        output_file=args.output
    ))


if __name__ == "__main__":
    main()

