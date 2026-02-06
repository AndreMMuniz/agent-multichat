"""
Dataset Seed Script
Populates the database with high-quality gold examples for few-shot learning.

Usage:
    python seed_dataset.py
"""

import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import DatasetItem
from datetime import datetime

def seed_dataset():
    """Populate database with gold-quality examples."""
    db = SessionLocal()
    
    # Check if already seeded
    existing_count = db.query(DatasetItem).count()
    if existing_count > 0:
        print(f"⚠️  Database already has {existing_count} examples.")
        response = input("Do you want to add more examples anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            db.close()
            return
    
    print("=" * 70)
    print("🌱 Seeding Dataset with Gold Examples")
    print("=" * 70)
    
    # Gold examples for each category
    examples = [
        # ==================== SALES ====================
        {
            "user_input": "Quanto custa uma hora de desenvolvimento?",
            "expected_intent": "SALES",
            "expected_response": "Para clientes no Brasil, a hora avulsa custa R$ 150. Para clientes internacionais, o valor é USD 50 por hora.",
            "category": "sales",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Quais são os pacotes disponíveis?",
            "expected_intent": "SALES",
            "expected_response": "Oferecemos pacotes de 10h, 20h e 40h tanto para clientes no Brasil quanto internacionais. Os pacotes têm desconto em relação à hora avulsa.",
            "category": "sales",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Quanto custa para fazer um site?",
            "expected_intent": "SALES",
            "expected_response": "O custo varia conforme a complexidade. Trabalhamos por hora: R$ 150/hora (Brasil) ou USD 50/hora (internacional). Posso entender melhor seu projeto para estimar o tempo necessário?",
            "category": "sales",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Preço",
            "expected_intent": "SALES",
            "expected_response": "Nossos valores são: Brasil - R$ 150/hora avulsa ou pacotes de 10h/20h/40h. Internacional - USD 50/hora ou pacotes similares. Qual se encaixa melhor para você?",
            "category": "sales",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Gostaria de contratar vocês",
            "expected_intent": "SALES",
            "expected_response": "Que ótimo! Vamos conversar sobre seu projeto. Pode me contar mais sobre o que você precisa desenvolver?",
            "category": "sales",
            "quality": "gold",
            "source": "manual"
        },
        
        # ==================== SUPPORT ====================
        {
            "user_input": "Preciso de ajuda com um bug",
            "expected_intent": "SUPPORT",
            "expected_response": "Claro! Pode me descrever o bug que está enfrentando? Vou ajudá-lo a resolver.",
            "category": "support",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "O sistema não está funcionando",
            "expected_intent": "SUPPORT",
            "expected_response": "Entendo a sua preocupação. Pode me dar mais detalhes sobre o que exatamente não está funcionando? Isso vai me ajudar a encontrar a solução mais rápido.",
            "category": "support",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Como faço para resetar minha senha?",
            "expected_intent": "SUPPORT",
            "expected_response": "Para resetar sua senha, você pode usar a função 'Esqueci minha senha' na tela de login. Se preferir, posso encaminhar para um atendente que vai te ajudar diretamente.",
            "category": "support",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Meu código deu erro",
            "expected_intent": "SUPPORT",
            "expected_response": "Vou te ajudar! Pode me mostrar qual foi o erro que apareceu? Isso vai me ajudar a identificar o problema.",
            "category": "support",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Não consigo acessar o painel",
            "expected_intent": "SUPPORT",
            "expected_response": "Que chato! Vamos resolver isso. Você está recebendo alguma mensagem de erro específica ao tentar acessar?",
            "category": "support",
            "quality": "gold",
            "source": "manual"
        },
        
        # ==================== COMPLAINT ====================
        {
            "user_input": "Quero meu dinheiro de volta",
            "expected_intent": "COMPLAINT",
            "expected_response": "Entendo sua frustração. Vou encaminhar sua solicitação de reembolso para análise do gerente. Pode me contar o que aconteceu?",
            "category": "complaint",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Estou muito insatisfeito com o serviço",
            "expected_intent": "COMPLAINT",
            "expected_response": "Lamento muito ouvir isso. Sua satisfação é importante para nós. Pode me contar o que aconteceu para que eu possa ajudar a resolver?",
            "category": "complaint",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Isso é um absurdo!",
            "expected_intent": "COMPLAINT",
            "expected_response": "Peço desculpas pela situação. Pode me explicar o que aconteceu? Vou fazer o possível para resolver o problema.",
            "category": "complaint",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Quero cancelar tudo",
            "expected_intent": "COMPLAINT",
            "expected_response": "Entendo. Lamento que você queira cancelar. Pode me dizer o que levou a essa decisão? Talvez possamos resolver o problema.",
            "category": "complaint",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Vocês não entregaram o que prometeram",
            "expected_intent": "COMPLAINT",
            "expected_response": "Peço desculpas se não atendemos suas expectativas. Pode me detalhar o que foi acordado e o que está faltando? Vou encaminhar para resolução imediata.",
            "category": "complaint",
            "quality": "gold",
            "source": "manual"
        },
        
        # ==================== GENERAL ====================
        {
            "user_input": "Bom dia",
            "expected_intent": "GENERAL",
            "expected_response": "Bom dia! Como posso ajudá-lo hoje?",
            "category": "general",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Olá",
            "expected_intent": "GENERAL",
            "expected_response": "Olá! Seja bem-vindo. Em que posso ajudar?",
            "category": "general",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Quais tecnologias vocês usam?",
            "expected_intent": "GENERAL",
            "expected_response": "Trabalhamos com Bubble.io para no-code, n8n para automações, LangChain e LangGraph para IA, e FastAPI com Python para APIs customizadas.",
            "category": "general",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Qual o horário de atendimento?",
            "expected_intent": "GENERAL",
            "expected_response": "Nosso atendimento humano funciona de segunda a sexta, das 9h às 18h (horário de Brasília). Fora desse horário, eu fico disponível para ajudar!",
            "category": "general",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Vocês trabalham com IA?",
            "expected_intent": "GENERAL",
            "expected_response": "Sim! Somos especializados em soluções de IA usando LangChain, LangGraph e outras ferramentas modernas. Desenvolvemos chatbots, automações e sistemas personalizados.",
            "category": "general",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "O que é Bubble.io?",
            "expected_intent": "GENERAL",
            "expected_response": "Bubble.io é uma plataforma no-code que usamos para criar aplicações web completas sem precisar programar. É ótima para MVPs e prototipação rápida.",
            "category": "general",
            "quality": "gold",
            "source": "manual"
        },
        {
            "user_input": "Para que serve o n8n?",
            "expected_intent": "GENERAL",
            "expected_response": "O n8n é uma ferramenta de automação que usamos para conectar diferentes sistemas e criar workflows automatizados. É muito poderosa para integrar APIs e serviços.",
            "category": "general",
            "quality": "gold",
            "source": "manual"
        },
    ]
    
    # Insert examples
    added = 0
    for ex in examples:
        item = DatasetItem(
            user_input=ex["user_input"],
            expected_intent=ex["expected_intent"],
            expected_response=ex.get("expected_response"),
            category=ex["category"],
            quality=ex["quality"],
            source=ex["source"],
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(item)
        added += 1
        print(f"✅ Added: {ex['user_input'][:50]}... [{ex['category'].upper()}]")
    
    db.commit()
    
    print("\n" + "=" * 70)
    print(f"🎉 Successfully added {added} gold examples!")
    print("=" * 70)
    print("\nCategory breakdown:")
    
    # Show summary
    for category in ["sales", "support", "complaint", "general"]:
        count = db.query(DatasetItem).filter(
            DatasetItem.category == category,
            DatasetItem.quality == "gold"
        ).count()
        print(f"  {category.upper()}: {count} examples")
    
    print("\n💡 Next steps:")
    print("  1. Run evaluation: python evaluation.py")
    print("  2. Test the agent - it will now use these examples for few-shot learning!")
    
    db.close()


if __name__ == "__main__":
    seed_dataset()
