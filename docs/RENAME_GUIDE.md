# 🔄 Guia de Renomeação: agente-escrita → agent-analyzer

## ⚠️ IMPORTANTE: Siga os passos na ordem

### Passo 1: Parar os Servidores Rodando

Você tem 2 processos Python rodando que precisam ser parados:

**No terminal onde está rodando `python main.py`:**
```
Pressione Ctrl+C
```

**Aguarde a mensagem**: "Shutting down" ou similar

---

### Passo 2: Renomear o Diretório

**Opção A - Usando o Script (Recomendado)**:
```powershell
cd c:\Users\mandr\OneDrive\Documentos\Projeto\agente-escrita
.\rename_backend.ps1
```

**Opção B - Manual**:
```powershell
cd c:\Users\mandr\OneDrive\Documentos\Projeto
Rename-Item -Path "agente-escrita" -NewName "agent-analyzer"
```

---

### Passo 3: Verificar Renomeação

```powershell
cd c:\Users\mandr\OneDrive\Documentos\Projeto
dir
```

Você deve ver:
```
agent-analyzer          (NOVO NOME)
log-analysis-dashboard
```

---

### Passo 4: Reiniciar o Backend

```powershell
cd agent-analyzer
python main.py
```

**Saída esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### Passo 5: Testar a API

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/history" -Method GET
```

Se retornar os registros, está tudo funcionando!

---

## 📝 O que NÃO precisa ser alterado

✅ **PostgreSQL**: Container continua funcionando normalmente  
✅ **Frontend**: Já aponta para `http://127.0.0.1:8000` (não usa o nome do diretório)  
✅ **Banco de dados**: Todos os dados permanecem intactos  
✅ **Código**: Nenhuma alteração necessária nos arquivos `.py`

---

## 🧪 Teste Final

Após renomear e reiniciar:

1. **Backend**: `http://127.0.0.1:8000/docs`
2. **Frontend**: `http://localhost:3000`
3. **Teste análise**: Cole um log e processe
4. **Verifique histórico**: Deve aparecer na aba History

---

## ✅ Checklist

- [ ] Parar servidor Python (Ctrl+C)
- [ ] Renomear diretório para `agent-analyzer`
- [ ] Entrar no novo diretório
- [ ] Reiniciar backend (`python main.py`)
- [ ] Testar endpoint `/history`
- [ ] Testar frontend em `localhost:3000`

---

**Pronto! O backend agora se chama agent-analyzer** 🚀
