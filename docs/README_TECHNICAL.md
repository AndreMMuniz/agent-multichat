# Documentação Técnica do Projeto Agent-Multichat

**Versão:** 1.0.0  
**Data:** 06/02/2026

## 1. Visão Geral da Arquitetura

O **Agent-Multichat** é um assistente virtual inteligente baseado em arquitetura de agentes (LangGraph), projetado para atendimento omnichannel (WhatsApp, Telegram, Email). O sistema utiliza RAG (Retrieval-Augmented Generation) para conhecimento específico e Few-Shot Learning dinâmico para personalização de comportamento.

### Stack Tecnológico
- **Backend:** Python 3.14, FastAPI
- **Orquestração:** LangChain, LangGraph
- **LLM:** Ollama (Llama 3.1, DeepSeek R1), OpenAI (opcional)
- **Banco de Dados:** PostgreSQL (via SQLAlchemy)
- **Vetor Store:** FAISS (Local)
- **Processamento de Docs:** Unstructured, PyTesseract
- **Infraestrutura:** Docker (PostgreSQL)

---

## 2. Componentes Principais

### 2.1. Núcleo do Agente (`graph.py`, `nodes.py`)
O fluxo de conversa é gerenciado por um grafo de estados (`StateGraph`).

- **State Management (`state.py`):** Mantém o contexto da conversa (`messages`, `user_id`, `intent`, `pending_actions`).
- **Nós Principais:**
  - `classify_message`: Classifica a intenção (SALES, SUPPORT, COMPLAINT, GENERAL) usando Few-Shot.
  - `retrieve_knowledge`: Busca contexto no FAISS.
  - `generate_response`: Gera resposta final combinando histórico + RAG + Few-Shot.
  - `detect_critical_action`: Identifica ações sensíveis (reembolso, exclusão) para HITL (Human-in-the-Loop).

### 2.2. Sistema RAG (Retrieval-Augmented Generation)
Responsável por ingerir documentos e fornecer contexto factual.

- **Parsing (`parse_documents.py`):**
  - Suporta: PDF, DOCX, TXT, CSV, Imagens (OCR).
  - Saída: `data/parsed_documents.json`.
- **Embedding (`create_embeddings.py`):**
  - Modelo: `llama3.1:8b` (Ollama).
  - Store: FAISS local em `data/faiss_index`.
- **Retrieval:**
  - Busca semântica (k-NN) com score de relevância.

### 2.3. Sistema de Aprendizado (Dataset & Few-Shot)
Permite ao agente aprender com exemplos curados sem re-treinamento (fine-tuning).

- **Banco de Dados (`dataset_items`):**
  - Armazena inputs, intents e respostas ideais ("Gold Examples").
- **Injeção Dinâmica:**
  - `nodes.py` consulta o banco em tempo real para injetar os 3-5 exemplos mais relevantes no prompt do sistema.
- **Ferramentas:**
  - `dataset_manager.py`: CLI para gestão (add, list, promote).
  - `seed_dataset.py`: Popula inicial (bootstrap).
  - `evaluation.py`: Framework de teste automatizado (Classificação e Geração).

---

## 3. Modelo de Dados (`models.py`)

### Tabelas Principais (PostgreSQL)

| Tabela | Descrição | Campos Chave |
|--------|-----------|--------------|
| `conversations` | Sessões de chat | `id`, `user_identifier`, `channel` |
| `messages` | Histórico de mensagens | `content`, `sender`, `timestamp` |
| `dataset_items` | Exemplos Few-Shot | `user_input`, `expected_intent`, `quality` |
| `user_profiles` | Perfil do usuário | `name`, `preferences`, `is_first_contact` |
| `dataset_items` | Exemplos de treino | `quality` ('gold', 'silver'), `category` |

---

## 4. Fluxos de Dados

### 4.1. Fluxo de Atendimento
1. **Input:** Usuário envia mensagem.
2. **Setup:** `manage_history` carrega sessão.
3. **Classificação:** `classify_message` consulta `DatasetItem` (Few-Shot) → Define Intent.
4. **Contexto:** `retrieve_knowledge` consulta FAISS (RAG) → Retorna chunks de texto.
5. **Geração:** `generate_response` combina Prompt + Histórico + RAG + Few-Shot Examples.
6. **Segurança:** `detect_critical_action` verifica se precisa de aprovação humana.
7. **Output:** Resposta enviada ao usuário.

### 4.2. Fluxo de Melhoria Contínua (Flywheel)
1. **Erro Detectado:** Agente classifica errado ou alucina.
2. **Correção:** Engenheiro usa `dataset_manager.py` para adicionar exemplo correto.
3. **Validação:** Rodar `evaluation.py` para garantir não-regressão.
4. **Deploy:** Novo exemplo entra em vigor imediatamente (Dynamic Few-Shot).

---

## 5. Ferramentas de Manutenção e Teste

### Scripts CLI

| Script | Função | Exemplo de Uso |
|--------|--------|----------------|
| `dataset_manager.py` | Gerenciar exemplos | `python dataset_manager.py add --intent SALES ...` |
| `evaluation.py` | Testes automatizados | `python evaluation.py --test-type classification` |
| `rag_benchmark.py` | Testar qualidade do RAG | `python rag_benchmark.py --model deepseek-r1:8b` |
| `llm_judge.py` | Avaliação LLM-as-a-Judge | `python llm_judge.py --judge-model gpt-oss:20b` |

### Comandos de Infraestrutura

- **Iniciar Backend:** `.\start_backend.ps1`
- **Recriar Embeddings:** `python create_embeddings.py`
- **Migrar Banco:** `alembic upgrade head` (ou `python migrate_dataset.py` para datasets)

---

## 6. Configuração e Variáveis (.env)

O sistema depende das seguintes variáveis de ambiente essenciais:

```ini
DATABASE_URL=postgresql://user:pass@localhost/dbname
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=sk-... (Opcional, se usar GPT)
```

## 7. Próximos Passos Recomendados

1. **Melhoria de Dataset:** Focar em preencher exemplos para a categoria `SALES` (atualmente com baixa acurácia).
2. **Refinamento RAG:** Ajustar tamanho dos chunks em `create_embeddings.py` se as respostas forem muito vagas.
3. **Interface UI:** Integrar com frontend (Next.js) para visualização de logs e métricas.
