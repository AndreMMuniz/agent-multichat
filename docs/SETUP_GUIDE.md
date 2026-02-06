# 🚀 Guia de Setup: Backend + Frontend

## ✅ O que foi corrigido no Backend

### 1. **CORS Habilitado**
Adicionado middleware CORS para permitir requisições do Next.js (portas 3000/3001).

### 2. **Resposta do `/write` atualizada**
Agora retorna:
```json
{
  "status": "success",
  "diagnosis": "...",
  "solution": "...",
  "is_safe": true  // ← NOVO: para o badge de segurança
}
```

---

## 📋 Checklist de Setup

### Passo 1: Iniciar PostgreSQL (OBRIGATÓRIO)

O backend precisa do PostgreSQL rodando na porta **5433**:

```powershell
# Criar container PostgreSQL
docker run -d `
  --name log_postgres `
  -p 5433:5432 `
  -e POSTGRES_USER=log_user `
  -e POSTGRES_PASSWORD=password123 `
  -e POSTGRES_DB=log_analyzer_db `
  postgres:15-alpine

# Verificar se está rodando
docker ps | Select-String "log_postgres"
```

### Passo 2: Testar Conexão com o Banco

```powershell
python test_database.py
```

**Saída esperada:**
```
✓ Database connection successful!
✓ Database tables created successfully!
✓ Table 'analysis_results' exists
```

### Passo 3: Iniciar o Backend

```powershell
python main.py
```

**Saída esperada:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Passo 4: Testar Endpoints

#### Teste 1: Análise de Log
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/write" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"topic": "ERROR: Permission denied (publickey) for git@github.com"}'

$response | ConvertTo-Json
```

**Resposta esperada:**
```json
{
  "status": "success",
  "diagnosis": "SSH key authentication failed...",
  "solution": "Generate SSH key with: ssh-keygen...",
  "is_safe": true
}
```

#### Teste 2: Histórico
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/history" -Method GET
```

---

## 🔗 Conectando ao Frontend Next.js

### Configuração do Frontend

No seu projeto Next.js (Log Analyzer Dashboard), a API já está configurada para:

**URL da API**: `http://127.0.0.1:8000/write`

### Exemplo de Integração

```typescript
// app/page.tsx
const handleAnalyze = async () => {
  const response = await fetch('http://127.0.0.1:8000/write', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic: logInput })
  });
  
  const data = await response.json();
  // data.diagnosis, data.solution, data.is_safe
};
```

### Iniciar Frontend

```bash
cd <diretorio-do-frontend>
npm run dev
```

Acesse: `http://localhost:3000`

---

## 🧪 Teste End-to-End

1. **Backend rodando**: `http://127.0.0.1:8000`
2. **Frontend rodando**: `http://localhost:3000`
3. **PostgreSQL ativo**: porta 5433
4. **Ollama rodando**: Llama 3.1 8b disponível

### Fluxo Completo:

1. Abra o frontend em `http://localhost:3000`
2. Cole um log de erro no textarea
3. Clique em "Process"
4. Veja:
   - Loading state (Llama 3.1 processando)
   - Diagnosis exibido
   - Fix Action com botão de copiar
   - Badge de segurança (verde = safe, vermelho = unsafe)

---

## 🐛 Troubleshooting

### Erro: "Connection refused" no PostgreSQL

```powershell
# Verificar se o container está rodando
docker ps -a | Select-String "log_postgres"

# Iniciar se estiver parado
docker start log_postgres
```

### Erro: CORS no Frontend

Verifique se o backend está rodando em `127.0.0.1:8000` (não `localhost:8000`).

### Erro: "Ollama not responding"

```powershell
# Verificar se Ollama está rodando
ollama list

# Testar modelo
ollama run llama3.1:8b "test"
```

### Erro: Frontend não conecta

Verifique se as portas estão corretas:
- Backend: `127.0.0.1:8000`
- Frontend: `localhost:3000`
- CORS permite ambas as origens

---

## 📊 Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/write` | Analisa log e retorna diagnóstico + solução |
| GET | `/history` | Retorna últimas 10 análises do banco |

---

## ✨ Status Atual

✅ Backend completo com:
- PostgreSQL persistence
- CORS habilitado
- Resposta com `is_safe` para frontend
- Histórico de análises
- LangGraph workflow otimizado

✅ Pronto para conectar ao frontend Next.js!

---

## 🎯 Próximos Passos

1. Inicie o PostgreSQL: `docker run...`
2. Teste o backend: `python main.py`
3. Inicie o frontend: `npm run dev`
4. Teste a integração completa!
