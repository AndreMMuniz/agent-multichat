# 📊 RAG Benchmark Report

**Gerado em:** 2026-02-07 09:58

**Configuração:**
- Modelo: `deepseek-r1:8b`
- Chunks (k): `5`
- Total de perguntas: `16`

---

## 📈 Resumo Executivo

## Relatório Executivo: Avaliação de Sistema RAG

**Data:** [Data da Avaliação]
**Sistema Analisado:** Sistema RAG [Nome do Sistema/Assistente, se aplicável]

---

**1. Resumo Geral**

O sistema RAG apresentou desempenho insatisfatório na última avaliação. Com um total de 16 perguntas analisadas, apenas 2 perguntas (12,5%) obtiveram pontuação considerada adequada (score >= 8). O score médio foi de 3,69, significativamente abaixo do esperado. A maioria das falhas (13 perguntas, 81%) foi atribuída ao `retrieval_miss`, seguida por `incomplete_answer` (7 perguntas, 44%) e `unknown` (3 perguntas, 19%). O sistema demonstrou dificuldade em recuperar informações relevantes e fornecer respostas completas e corretas, especialmente para perguntas relacionadas aos serviços, diferencial da empresa e transferência para humanos.

---

**2. Principais Problemas**

Os três principais problemas identificados foram:

1.  **Falha Crítica em Recuperação de Informações (`retrieval_miss`):** Este foi o principal problema, ocorrendo em 6 perguntas (37,5%). O sistema frequentemente recuperou informações irrelevantes ou omitiu dados cruciais necessários para responder adequadamente, como componentes da stack tecnológica, serviços específicos, valor da hora e critérios de transferência.
2.  **Respostas Incompletas (`incomplete_answer`):** Ocorreu em 7 perguntas (44%). Mesmo quando informações relevantes foram recuperadas, o sistema frequentemente não as utilizou de forma completa para formular uma resposta abrangente, como no caso da definição do diferencial da empresa.
3.  **Recuperação Incerta (`unknown`):** Ocorreu em 3 perguntas (19%). O sistema não conseguiu determinar se as informações necessárias para responder estavam disponíveis na base de conhecimento ou se a pergunta estava fora do escopo, levando a respostas não classificadas como corretas ou incorretas neste contexto.

---

**3. Padrões de Falha**

As falhas identificadas seguem alguns padrões:

*   **Perguntas sobre Serviços e Funcionamento:** Múltas perguntas falharam ao tentar obter informações sobre o que o sistema faz, como ele funciona (transferência para humano), pacotes de horas e valores da hora. Isso sugere que a base de conhecimento ou a forma como as informações são indexadas/recuperadas não está alinhada com esses tópicos.
*   **Perguntas sobre Diferenciais e Identidade:** Perguntas simples sobre o diferencial da empresa e a função do assistente falharam, muitas vezes devido a `retrieval_miss` ou respostas `incomplete_answer`. Isso pode indicar que a base de conhecimento contém a informação, mas ela não foi adequadamente mapeada ou priorizada para respostas diretas.
*   **Ambiguidade em Referências:** Uma falha específica (Q8) apontou para uma possível ambiguidade ou confusão na referência utilizada pelo sistema, sugerindo que mesmo quando a informação está presente, a forma como o RAG a acessa pode ser frágil.
*   **Falta de Informação:** Perguntas como a referência específica ao Bubble.io não foram respondidas adequadamente, indicando que talvez essa informação não esteja suficientemente bem documentada ou acessível na base de conhecimento.

---

**4. Recomendações Prioritárias**

Para melhorar significativamente o desempenho do sistema RAG, sugerimos as seguintes ações prioritárias:

1.  **Revisar e Aumentar a Base de Conhecimento:** Avaliar e expandir a base de conhecimento com informações críticas frequentemente faltantes (serviços, valores, transferência, diferencial) e garantir que ela esteja bem estruturada e documentada.
2.  **Otimizar o Mecanismo de Busca/Recuperação:** Reavaliar o método de busca e a forma como os documentos são pesquisados e combinados para garantir que as informações relevantes sejam priorizadas e recuperadas adequadamente, especialmente para perguntas complexas ou com múltiplas partes.
3.  **Implementar Feedback e Monitoramento:** Criar um loop de feedback para coletar perguntas mal respondidas pelos usuários e usá-las para iterar e melhorar o sistema RAG, incluindo a base de conhecimento e os processos de recuperação.
4.  **Revisar a Definição de "Correto":** Clarificar e documentar os critérios de avaliação de respostas (score) para garantir consistência e que o sistema esteja alinhado com as expectativas dos usuários.

---

**5. Quick Wins**

Melhorias rápidas que podem ser implementadas com pouca complexidade:

1.  **Ajustar o Prompt Inicial:** Incluir instruções claras no prompt inicial para o modelo de linguagem sobre como lidar com `retrieval_miss` (por exemplo, "Se não encontrar informações suficientes, explique que não sei antes de tentar responder").
2.  **Criar Glossário ou Mapeamento de Termos:** Desenvolver um pequeno glossário ou mapeamento de termos-chave para facilitar a recuperação de informações específicas (ex: termos relacionados a "Bubble.io", "valor da hora", "transferência").
3.  **Revisar Exemplos de Respostas:** Analisar exemplos de perguntas bem respondidas (as 3 corretas) e identificar padrões que podem ser replicados para outras perguntas semelhantes.

---

O sistema RAG requer urgentes melhorias focadas na qualidade da base de conhecimento e na eficácia da recuperação de informações para atingir níveis de desempenho aceitáveis. As recomendações acima devem ser discutidas e priorizadas em reunião com as partes interessadas.

---

## 📉 Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| Score Médio | **3.69/10** |
| Score Máximo | 10.0/10 |
| Score Mínimo | 0.0/10 |
| Excelente (9-10) | 3 |
| Bom (7-8) | 0 |
| Regular (5-6) | 1 |
| Ruim (<5) | 12 |

---

## ❌ Análise de Falhas

### 1. Qual é a função deste assistente virtual?...

**Score:** 0.0/10 | **Prioridade:** Alta | **Categoria:** incomplete_answer

**Resposta Esperada:**
> Sou um assistente virtual inteligente projetado para responder dúvidas sobre serviços, apresentar o stack tecnológico, fornecer preços e agendar reuniões....

**Resposta Gerada:**
> Não encontrei essa informação específica....

**🔍 Diagnóstico:** A resposta não fornece a função do assistente virtual, apenas indicando a incapacidade de encontrar a informação. Isso representa uma falha na capacidade do sistema de responder perguntas básicas sobre sua própria identidade.

**🎯 Causa Raiz:** Retrieval Miss (retrieval_miss). O contexto recuperado contém informações relevantes sobre o sistema (sales pitch, ferramentas, estratégias), mas o modelo não conseguiu mapear adequadamente a pergunta sobre a função do assistente para essas informações, especialmente a resposta esperada que define explicitamente a função.

**💡 Sugestão:** Implementar uma lógica de combinação mais sofisticada no pipeline RAG. O modelo deve ser treinado para reconhecer que, embora o contexto recuperado não contenha uma definição literal de 'função' como na resposta esperada, ele contém todas as informações necessárias para construir essa resposta. Utilizar embeddings mais sofisticados ou técnicas de rag chaining para combinar múltiplas referências pode ajudar.

---

### 2. Quais são os pacotes de horas disponíveis para o Brasil?...

**Score:** 0.0/10 | **Prioridade:** Alta | **Categoria:** incomplete_answer

**Resposta Esperada:**
> Temos pacotes de 10h (R$ 1.000), 20h (R$ 1.800), 40h (R$ 3.200), 80h (R$ 6.000) e 160h (R$ 10.000)....

**Resposta Gerada:**
> Não encontrei essa informação específica....

**🔍 Diagnóstico:** A resposta não forneceu a informação solicitada pela pergunta. Em vez disso, apenas indicou a ausência de dados, o que é uma resposta insatisfatória e ineficaz para a consulta do usuário.

**🎯 Causa Raiz:** retrieval_miss

**💡 Sugestão:** 1. Verificar se os dados sobre os pacotes de horas estão disponíveis na base de conhecimento do sistema e se estão corretamente indexados. 2. Implementar mecanismos de busca mais eficientes para garantir que respostas relevantes sejam encontradas para consultas específicas como esta. 3. Educar o modelo para fornecer respostas mais proativas quando a informação é encontrada, mesmo que não esteja totalmente satisfação a pergunta.

---

### 3. Em quais situações o bot transfere para um humano?...

**Score:** 0.65/10 | **Prioridade:** Alta | **Categoria:** retrieval_miss

**Resposta Esperada:**
> Transfiro quando: o usuário solicita explicitamente; o assunto é financeiro complexo; não encontro a resposta após 2 tentativas; ou o projeto requer análise técnica fora do stack padrão....

**Resposta Gerada:**
> Não encontrei essa informação específica....

**🔍 Diagnóstico:** A resposta gerada não forneceu a informação solicitada sobre os critérios de transferência do bot para um humano. Em vez disso, apenas indicou que a informação não foi encontrada.

**🎯 Causa Raiz:** retrieval_miss: O mecanismo de busca do RAG não recuperou a informação relevante sobre os critérios de transferência do bot, que estão documentados no contexto.

**💡 Sugestão:** Implementar uma consulta de busca mais eficiente ou garantir que a base de conhecimento contenha explicitamente os critérios de transferência do bot para uma recuperação adequada.

---

### 4. Que tipos de serviços vocês oferecem?...

**Score:** 0.67/10 | **Prioridade:** Alta | **Categoria:** retrieval_miss

**Resposta Esperada:**
> Suporte Técnico, Vendas e Orçamentos, Dúvidas Gerais sobre Tecnologia e Segunda via de Fatura/Pagamentos....

**Resposta Gerada:**
> Pelo que consta na nossa base de conhecimento, oferecemos serviços relacionados a automação e IA aplicada para eliminar gargalos em operações. Nossa abordagem inclui:

1. Diagnóstico de gargalos opera...

**🔍 Diagnóstico:** A resposta não respondeu corretamente à pergunta. A pergunta pede os tipos de serviços oferecidos, mas a resposta discute estratégias de negócio, automação, IA e atendimento, sem listar os serviços.

**🎯 Causa Raiz:** retrieval_miss

**💡 Sugestão:** Reprogramar o sistema ou ajustar o contexto de busca para garantir que ele retorne informações sobre os tipos de serviços oferecidos, conforme a resposta esperada.

---

### 5. Qual o diferencial da empresa?...

**Score:** 0.95/10 | **Prioridade:** Alta | **Categoria:** retrieval_miss

**Resposta Esperada:**
> Oferecemos senioridade de 15 anos de mercado, velocidade de entrega usando Bubble.io e inteligência real através de automações com IA....

**Resposta Gerada:**
> Resposta:

O diferencial da empresa está em como utilizamos tecnologias de ponta como **n8n (orquestração & integração)**, **LangChain & LangGraph (agentes de IA)** e **FastAPI (backend de alto desemp...

**🔍 Diagnóstico:** A resposta gerada não atendeu à pergunta simples e direta sobre o diferencial da empresa. Em vez de destacar benefícios tangíveis e linguagem acessível (como na resposta esperada), ela mergulhou em detalhes técnicos irrelevantes, tornando a resposta confusa e descontextualizada para o usuário.

**🎯 Causa Raiz:** Falha de Retrieval (retrieval_miss). O contexto recuperado contém informações técnicas relevantes, mas a pergunta do usuário é simples e direta, enquanto a resposta priorizou detalhes técnicos complexos que não se alinham com a expectativa de uma resposta concisa sobre o diferencial da empresa.

**💡 Sugestão:** O sistema deve priorizar a simplicidade e a relevância no retrieval. Para perguntas básicas como 'Qual o diferencial?', o contexto recuperado deve ser filtrado para extrair apenas os pontos mais relevantes e simplificados. A resposta deve ser reescrita para combinar os benefícios técnicos com linguagem mais acessível e focada no valor proposto.

---

### 6. Para que serve o Bubble.io nos projetos?...

**Score:** 1.22/10 | **Prioridade:** Alta | **Categoria:** retrieval_miss

**Resposta Esperada:**
> Usamos Bubble.io para desenvolvimento Web e Mobile (PWA), criando plataformas robustas e escaláveis em semanas, não meses....

**Resposta Gerada:**
> Bubble.io é usado para criar interfaces visuais e experiências de usuário, enquanto ferramentas como LangChain/n8n e FastAPI lidam com processamento pesado e lógicas customizadas. Isso permite desenvo...

**🔍 Diagnóstico:** A resposta não respondeu diretamente à pergunta sobre o propósito do Bubble.io. Em vez disso, ela focou em ferramentas de backend e IA, desviando completamente do tópico.

**🎯 Causa Raiz:** Falha de Recuperação (retrieval_miss). O contexto recuperado pelo RAG foi irrelevante para a pergunta sobre Bubble.io, embora o próprio contexto recuperado (item 'Quem Somos e Nossa Visão') mencione explicitamente o Bubble.io.

**💡 Sugestão:** Reestruturar o pipeline de RAG para priorizar a recuperação de contextos diretamente relacionados ao termo de busca (Bubble.io). Além disso, o modelo deve ser re-entrenado ou ajustado para melhor entender a intenção da pergunta e recuperar informações relevantes.

---

### 7. O que acontece se eu precisar de uma tecnologia fora do stac...

**Score:** 1.61/10 | **Prioridade:** Alta | **Categoria:** incomplete_answer

**Resposta Esperada:**
> Se o cliente solicitar tecnologias fora da lista, analisaremos a viabilidade técnica do caso, sem prometer execução imediata....

**Resposta Gerada:**
> O stack padrão da empresa é composto por **n8n**, **LangChain & LangGraph** e **FastAPI**. No entanto, entendemos que às vezes é necessário utilizar tecnologias externas ou não padrão. 

Se precisar d...

**🔍 Diagnóstico:** A resposta está incompleta, pois menciona o suporte técnico para tecnologias externas, mas não fornece informações sobre preços ou pacotes, mesmo tendo sido recuperada a informação sobre serviços de suporte técnico.

**🎯 Causa Raiz:** retrieval_miss: A base de conhecimento contém informações sobre serviços de suporte técnico, vendas e orçamentos, mas o mecanismo de busca do RAG não recuperou adequadamente essas informações.

**💡 Sugestão:** Revisar a base de conhecimento para garantir que todas as informações relevantes, incluindo detalhes sobre preços e pacotes, estejam disponíveis e facilmente recuperáveis. Além disso, ajustar o mecanismo de busca para melhor cobrir variações de consulta.

---

### 8. O que vocês fazem com LangChain e LangGraph?...

**Score:** 3.12/10 | **Prioridade:** Média | **Categoria:** incomplete_answer

**Resposta Esperada:**
> Utilizamos para a engenharia de Agentes de IA, criando lógicas autônomas e suporte inteligente com memória de contexto....

**Resposta Gerada:**
> LangChain & LangGraph (Agentes de IA)  
Engenharia de agentes autônomos que possuem memória de contexto e capacidade de raciocínio....

**🔍 Diagnóstico:** A resposta, embora tecnicamente correta, não está completamente alinhada com a pergunta do usuário. A pergunta busca entender o *uso* das tecnologias (o que se faz com LangChain e LangGraph), enquanto a resposta se concentra mais na descrição das tecnologias em si, sem explicitamente abordar as aplicações ou benefícios práticos.

**🎯 Causa Raiz:** A causa raiz é a interpretação insatisfatória do contexto recuperado. O contexto menciona explicitamente como essas tecnologias são usadas (orquestração, backend, agentes autônomos), mas a resposta, embora incluindo essas informações, não as apresenta de forma destacada ou aplicada diretamente ao que o usuário está perguntando (o 'o que se faz').

**💡 Sugestão:** Melhorar a integração entre o modelo e o contexto recuperado. O prompt ou o pipeline de RAG deve ser ajustado para que o modelo seja mais direcionado a extrair e estruturar as informações sobre *como* essas tecnologias são aplicadas na prática, conforme indicado no contexto recuperado (ex: agentes autônomos, memória de contexto, raciocínio, backend pesado).

---

### 9. Qual o valor da hora avulsa para clientes no Brasil?...

**Score:** 3.48/10 | **Prioridade:** Alta | **Categoria:** retrieval_miss

**Resposta Esperada:**
> Para clientes brasileiros, a hora avulsa custa R$ 120,00....

**Resposta Gerada:**
> O valor da hora avulsa para clientes no Brasil é **R$ 120,00**. [cite: 11]...

**🔍 Diagnóstico:** A resposta gerada não forneceu a informação correta sobre o valor da hora avulsa, pois incluiu informações irrelevantes e omitiu completamente a resposta esperada.

**🎯 Causa Raiz:** retrieval_miss

**💡 Sugestão:** Revisar o mecanismo de busca do RAG para garantir que ele priorize documentos que contenham informações sobre valores e preços, e revisar a base de conhecimento para garantir que informações financeiras estejam bem indexadas.

---

### 10. Quais tecnologias compõem o stack principal?...

**Score:** 3.64/10 | **Prioridade:** Alta | **Categoria:** retrieval_miss

**Resposta Esperada:**
> Trabalhamos estritamente com: Bubble.io (No-Code Full-Stack), n8n (Integrações), LangChain/LangGraph (Agentes de IA) e FastAPI (Backend de alta performance)....

**Resposta Gerada:**
> Resposta: n8n (Orquestração & Integração), LangChain & LangGraph (Agentes de IA) e FastAPI (High-Performance Backend) [cite: 2]...

**🔍 Diagnóstico:** A resposta omitiu explicitamente 'Bubble.io' (No-Code Full-Stack) e mencionou incorretamente 'Enterprise Quality' (que não faz parte da stack esperada).

**🎯 Causa Raiz:** Retrieval Miss: O contexto recuperado incluiu informações irrelevantes (como a visão da empresa) que interferiram na resposta, e o modelo não recuperou adequadamente todos os componentes da stack (faltou 'Bubble.io').

**💡 Sugestão:** Revisar o mecanismo de busca e embeddings para garantir que todas as tecnologias da stack (incluindo Bubble.io) sejam priorizadas na recuperação de contexto. Além disso, validar o prompt para evitar interpretações adicionais (como 'Enterprise Quality').

---

### 11. Qual a função do n8n nos serviços?...

**Score:** 4.0/10 | **Prioridade:** Alta | **Categoria:** incomplete_answer

**Resposta Esperada:**
> O n8n é utilizado para orquestração de fluxos de trabalho e integração de sistemas via API....

**Resposta Gerada:**
> O cérebro das operações. Conecta APIs, automatiza fluxos de trabalho e integra diferentes sistemas sem fricção....

**🔍 Diagnóstico:** A resposta não foi precisa o suficiente ao descrever explicitamente a função do n8n. Embora contenha informações corretas, falta a definição clara de 'orquestração de fluxos de trabalho e integração de sistemas via API' conforme esperado.

**🎯 Causa Raiz:** Modelo não conseguiu mapear diretamente a pergunta para a definição mais concisa e esperada do n8n, mesmo tendo informações relevantes disponíveis no contexto recuperado.

**💡 Sugestão:** Implementar mecanismos de prompt engineering mais específicos para perguntas diretas sobre ferramentas, incentivando respostas mais curtas e precisas. Ajustar o sistema de recuperação de informações para priorizar definições concisas quando a pergunta é direta.

---

### 12. Quando o FastAPI é utilizado?...

**Score:** 4.0/10 | **Prioridade:** Média | **Categoria:** incomplete_answer

**Resposta Esperada:**
> Usamos FastAPI para backends que exigem processamento pesado ou lógica personalizada em Python que o No-code não suporta....

**Resposta Gerada:**
> FastAPI é um backend em Python para processamento pesado e lógicas customizadas que excedem as capacidades do No-Code....

**🔍 Diagnóstico:** A resposta está incompleta em relação à resposta esperada. A resposta esperada menciona explicitamente 'No-code', que não está presente na resposta gerada.

**🎯 Causa Raiz:** Retrieval Miss/Incomplete Context Utilization. O contexto recuperado menciona explicitamente 'No-code' em relação ao FastAPI, mas a resposta não incorporou essa informação.

**💡 Sugestão:** Reprogramar o sistema RAG para garantir que todas as partes relevantes do contexto recuperado sejam incorporadas na resposta final, especialmente quando o contexto contém informações contrastantes ou complementares.

---

### 13. Qual o valor da hora para clientes internacionais?...

**Score:** 6.0/10 | **Prioridade:** Média | **Categoria:** incomplete_answer

**Resposta Esperada:**
> Para clientes internacionais, a hora avulsa é $50.00 USD....

**Resposta Gerada:**
> Para clientes internacionais, a hora avulsa custa **$50.00 USD**. [cite: 11]...

**🔍 Diagnóstico:** A resposta está tecnicamente correta, mas não está completamente alinhada com o contexto ou a expectativa do usuário. Embora confirme a taxa correta para clientes internacionais, a resposta não demonstra confiança ou contextualização adequada, apenas repetindo a informação sem validação ou explicação.

**🎯 Causa Raiz:** A causa raiz é a confusão entre a resposta correta e a ambiguidade ou múltiplas interpretações na referência [cite:11]. O sistema RAG está confiando em uma referência específica que contém a informação correta, mas pode haver inconsistências ou ambiguidade nessa referência.

**💡 Sugestão:** Melhorar a qualidade e clareza das referências no sistema RAG. Implementar mecanismos de verificação cruzada entre referências para evitar respostas baseadas em informações incompletas ou ambíguas.

---

## ✅ Respostas Corretas

| Pergunta | Score |
|----------|-------|
| Quem é o responsável pelos desenvolvimentos?... | 10.0/10 |
| Quais são os pacotes para clientes internacionais?... | 10.0/10 |
| Qual o horário de atendimento humano?... | 9.7/10 |
