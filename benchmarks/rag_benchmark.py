"""
RAG Benchmark & Analysis Script
Generates a comprehensive report with failure analysis, insights, and improvement suggestions.

Usage:
    python rag_benchmark.py
    python rag_benchmark.py --model deepseek-r1:8b
    python rag_benchmark.py --model deepseek-r1:8b -k 5
"""

import os
import csv
import json
import argparse
import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
from dotenv import load_dotenv

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import FAISS

from logging_config import setup_logger

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logger("rag_benchmark")

# Constants
DATA_DIR = "./data"
QUESTIONS_FILE = "./data/questions.csv"
DB_PATH = "./data/faiss_index"
OUTPUT_FILE = "./data/benchmark_report.md"
OUTPUT_JSON = "./data/benchmark_report.json"
DEFAULT_MODEL = "deepseek-r1:8b"


# ============================================================================
# PROMPTS
# ============================================================================

RAG_PROMPT = """Você é um assistente virtual inteligente de uma empresa de desenvolvimento de software e automação com IA.

=== BASE DE CONHECIMENTO (USE ESTA INFORMAÇÃO) ===
{context}
=== FIM DA BASE DE CONHECIMENTO ===

INSTRUÇÕES:
1. SEMPRE busque a resposta na base de conhecimento PRIMEIRO.
2. Se a resposta estiver na base, USE EXATAMENTE como está. Não parafraseie preços, horários ou especificações.
3. Cite valores específicos (preços, horas, pacotes) diretamente da base.
4. Se NÃO encontrar a resposta, diga: "Não encontrei essa informação específica."
5. NUNCA invente informações sobre preços, serviços ou políticas.

Pergunta: {question}

Resposta:"""

ANALYSIS_PROMPT = """Você é um especialista em análise de qualidade de sistemas RAG (Retrieval-Augmented Generation).

Analise a seguinte avaliação de um sistema RAG e forneça:

1. **DIAGNÓSTICO**: O que está errado nesta resposta específica?
2. **CAUSA RAIZ**: Por que o RAG falhou? (contexto incorreto, pergunta ambígua, modelo não entendeu, etc.)
3. **SUGESTÃO**: Como resolver este problema específico?
4. **PRIORIDADE**: Alta/Média/Baixa

---
**Pergunta:** {question}

**Resposta Esperada:** {expected}

**Resposta Gerada:** {generated}

**Contexto RAG Recuperado:** {context}

---

Responda em formato JSON:
{{
    "diagnosis": "...",
    "root_cause": "...",
    "suggestion": "...",
    "priority": "Alta|Média|Baixa",
    "failure_category": "retrieval_miss|wrong_context|model_hallucination|incomplete_answer|correct"
}}
"""

SUMMARY_PROMPT = """Você é um consultor especialista em sistemas RAG.

Com base nos resultados abaixo, gere um relatório executivo com:

1. **Resumo Geral**: Visão geral do desempenho
2. **Principais Problemas**: Top 3 problemas mais críticos
3. **Padrões de Falha**: Que tipos de perguntas estão falhando?
4. **Recomendações Prioritárias**: 3-5 ações concretas para melhorar o RAG
5. **Quick Wins**: Melhorias rápidas de implementar

---
**Dados da Avaliação:**
- Total de perguntas: {total}
- Corretas (score >= 8): {correct}
- Parcialmente corretas (5-7): {partial}
- Incorretas (< 5): {incorrect}
- Score médio: {avg_score}

**Categorias de Falha:**
{failure_categories}

**Detalhes das Falhas:**
{failure_details}

---

Responda em português, de forma clara e acionável.
"""


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_llm(model: str, temperature: float = 0.1):
    """Get LLM instance."""
    return OllamaLLM(model=model, temperature=temperature)


def load_vector_store(model: str = "llama3.1:8b"):
    """Load FAISS vector store."""
    if not os.path.exists(DB_PATH):
        logger.error(f"Vector store not found: {DB_PATH}")
        return None
    
    embeddings = OllamaEmbeddings(model=model)
    return FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)


def retrieve_context(vector_store, query: str, k: int = 3) -> tuple:
    """Retrieve context and sources."""
    results = vector_store.similarity_search_with_score(query, k=k)
    context = "\n\n".join([doc.page_content for doc, _ in results])
    sources = [{"content": doc.page_content[:200], "score": float(score)} for doc, score in results]
    return context, sources


def generate_answer(llm, question: str, context: str) -> str:
    """Generate answer using RAG."""
    prompt = RAG_PROMPT.format(context=context, question=question)
    return llm.invoke(prompt).strip()


def evaluate_answer(expected: str, generated: str) -> float:
    """Simple similarity-based scoring."""
    expected_words = set(expected.lower().split())
    generated_words = set(generated.lower().split())
    
    if not expected_words:
        return 0.0
    
    overlap = len(expected_words & generated_words)
    precision = overlap / len(generated_words) if generated_words else 0
    recall = overlap / len(expected_words)
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return round(f1 * 10, 2)  # Scale to 0-10


def analyze_failure(llm, question: str, expected: str, generated: str, context: str) -> Dict:
    """Use LLM to analyze why the answer failed."""
    prompt = ANALYSIS_PROMPT.format(
        question=question,
        expected=expected,
        generated=generated,
        context=context[:1500]
    )
    
    try:
        response = llm.invoke(prompt)
        
        # Parse JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        logger.warning(f"Analysis failed: {e}")
    
    return {
        "diagnosis": "Análise não disponível",
        "root_cause": "unknown",
        "suggestion": "Revisar manualmente",
        "priority": "Média",
        "failure_category": "unknown"
    }


def generate_summary(llm, results: List[Dict]) -> str:
    """Generate executive summary."""
    # Calculate stats
    scores = [r["score"] for r in results]
    correct = len([s for s in scores if s >= 8])
    partial = len([s for s in scores if 5 <= s < 8])
    incorrect = len([s for s in scores if s < 5])
    
    # Count failure categories
    categories = defaultdict(int)
    for r in results:
        cat = r.get("analysis", {}).get("failure_category", "unknown")
        categories[cat] += 1
    
    failure_categories = "\n".join([f"- {k}: {v}" for k, v in categories.items()])
    
    # Get failure details
    failures = [r for r in results if r["score"] < 8]
    failure_details = "\n".join([
        f"- Q: {f['question'][:50]}... | Score: {f['score']} | Causa: {f.get('analysis', {}).get('root_cause', 'N/A')}"
        for f in failures[:10]
    ])
    
    prompt = SUMMARY_PROMPT.format(
        total=len(results),
        correct=correct,
        partial=partial,
        incorrect=incorrect,
        avg_score=round(sum(scores) / len(scores), 2),
        failure_categories=failure_categories,
        failure_details=failure_details
    )
    
    return llm.invoke(prompt)


def load_questions(filepath: str) -> List[Dict]:
    """Load questions from CSV."""
    questions = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question = row.get('question', '').replace('[cite_start]', '').strip('"')
            answer = row.get('answer', '').replace('[cite_start]', '').strip('"')
            questions.append({'question': question, 'answer': answer})
    return questions


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_markdown_report(results: List[Dict], summary: str, config: Dict) -> str:
    """Generate markdown report."""
    scores = [r["score"] for r in results]
    
    report = f"""# 📊 RAG Benchmark Report

**Gerado em:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

**Configuração:**
- Modelo: `{config['model']}`
- Chunks (k): `{config['k']}`
- Total de perguntas: `{len(results)}`

---

## 📈 Resumo Executivo

{summary}

---

## 📉 Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| Score Médio | **{round(sum(scores)/len(scores), 2)}/10** |
| Score Máximo | {max(scores)}/10 |
| Score Mínimo | {min(scores)}/10 |
| Excelente (9-10) | {len([s for s in scores if s >= 9])} |
| Bom (7-8) | {len([s for s in scores if 7 <= s < 9])} |
| Regular (5-6) | {len([s for s in scores if 5 <= s < 7])} |
| Ruim (<5) | {len([s for s in scores if s < 5])} |

---

## ❌ Análise de Falhas

"""
    
    # Add failure details
    failures = sorted([r for r in results if r["score"] < 8], key=lambda x: x["score"])
    
    for i, f in enumerate(failures, 1):
        analysis = f.get("analysis", {})
        report += f"""### {i}. {f['question'][:60]}...

**Score:** {f['score']}/10 | **Prioridade:** {analysis.get('priority', 'N/A')} | **Categoria:** {analysis.get('failure_category', 'N/A')}

**Resposta Esperada:**
> {f['expected_answer'][:200]}...

**Resposta Gerada:**
> {f['generated_answer'][:200]}...

**🔍 Diagnóstico:** {analysis.get('diagnosis', 'N/A')}

**🎯 Causa Raiz:** {analysis.get('root_cause', 'N/A')}

**💡 Sugestão:** {analysis.get('suggestion', 'N/A')}

---

"""
    
    # Add success section
    report += """## ✅ Respostas Corretas

| Pergunta | Score |
|----------|-------|
"""
    
    successes = [r for r in results if r["score"] >= 8]
    for s in successes:
        report += f"| {s['question'][:50]}... | {s['score']}/10 |\n"
    
    return report


# ============================================================================
# MAIN
# ============================================================================

def run_benchmark(
    model: str = DEFAULT_MODEL,
    k: int = 3,
    questions_file: str = QUESTIONS_FILE,
    output_md: str = OUTPUT_FILE,
    output_json: str = OUTPUT_JSON
):
    """Run full benchmark."""
    print("=" * 70)
    print("📊 RAG Benchmark & Analysis")
    print("=" * 70)
    print(f"\n  Modelo: {model}")
    print(f"  Chunks (k): {k}")
    print("-" * 70)
    
    # Initialize
    print("\n🔧 Inicializando...")
    llm = get_llm(model, temperature=0.3)
    analysis_llm = get_llm(model, temperature=0.1)
    vector_store = load_vector_store()
    
    if not vector_store:
        print("❌ Vector store não encontrado. Execute create_embeddings.py primeiro.")
        return
    
    # Load questions
    print("📋 Carregando perguntas...")
    questions = load_questions(questions_file)
    print(f"   Encontradas {len(questions)} perguntas")
    
    # Process each question
    results = []
    print("\n" + "-" * 70)
    print("🏃 Executando benchmark...")
    print("-" * 70)
    
    for i, q in enumerate(questions, 1):
        question = q['question']
        expected = q['answer']
        
        print(f"\n[{i}/{len(questions)}] {question[:50]}...")
        
        # Get context and generate answer
        print("   → Recuperando contexto...")
        context, sources = retrieve_context(vector_store, question, k=k)
        
        print("   → Gerando resposta...")
        generated = generate_answer(llm, question, context)
        
        # Simple score
        score = evaluate_answer(expected, generated)
        
        # Analyze failures
        analysis = {}
        if score < 8:
            print("   → Analisando falha...")
            analysis = analyze_failure(analysis_llm, question, expected, generated, context)
        
        result = {
            "question": question,
            "expected_answer": expected,
            "generated_answer": generated,
            "context": context[:500],
            "sources": sources,
            "score": score,
            "analysis": analysis
        }
        results.append(result)
        
        status = "✅" if score >= 8 else "⚠️" if score >= 5 else "❌"
        print(f"   {status} Score: {score}/10")
    
    # Generate summary
    print("\n" + "-" * 70)
    print("📝 Gerando relatório...")
    print("-" * 70)
    
    print("   → Criando resumo executivo...")
    summary = generate_summary(analysis_llm, results)
    
    # Generate reports
    config = {"model": model, "k": k}
    
    print("   → Salvando relatório Markdown...")
    md_report = generate_markdown_report(results, summary, config)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print("   → Salvando dados JSON...")
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "config": config,
        "summary_text": summary,
        "results": results
    }
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # Print summary
    scores = [r["score"] for r in results]
    print("\n" + "=" * 70)
    print("📊 Benchmark Concluído!")
    print("=" * 70)
    print(f"  Score Médio: {round(sum(scores)/len(scores), 2)}/10")
    print(f"  Corretas (≥8): {len([s for s in scores if s >= 8])}")
    print(f"  Falhas (<8): {len([s for s in scores if s < 8])}")
    print("-" * 70)
    print(f"\n📄 Relatório MD: {os.path.abspath(output_md)}")
    print(f"📄 Dados JSON: {os.path.abspath(output_json)}")
    print("\n💡 Abra o relatório .md para ver análise detalhada e sugestões!")


def main():
    parser = argparse.ArgumentParser(
        description="RAG Benchmark & Analysis Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python rag_benchmark.py
  python rag_benchmark.py --model deepseek-r1:8b
  python rag_benchmark.py --model deepseek-r1:8b -k 5
  python rag_benchmark.py --model gpt-oss:20b --output ./data/report_gpt.md
        """
    )
    
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Modelo Ollama para análise (default: {DEFAULT_MODEL})"
    )
    
    parser.add_argument(
        "-k",
        type=int,
        default=3,
        help="Número de chunks RAG (default: 3)"
    )
    
    parser.add_argument(
        "--questions", "-q",
        default=QUESTIONS_FILE,
        help=f"Arquivo CSV de perguntas (default: {QUESTIONS_FILE})"
    )
    
    parser.add_argument(
        "--output", "-o",
        default=OUTPUT_FILE,
        help=f"Arquivo de saída MD (default: {OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    run_benchmark(
        model=args.model,
        k=args.k,
        questions_file=args.questions,
        output_md=args.output,
        output_json=args.output.replace('.md', '.json')
    )


if __name__ == "__main__":
    main()
