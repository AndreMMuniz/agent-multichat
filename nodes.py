from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import ChatState
from database import SessionLocal
from models import Conversation, Message, UserContext, PendingAction, UserProfile, DatasetItem
from rag import retrieve_context
from async_utils import run_in_thread
from datetime import datetime
import json
import re
from logging_config import setup_logger

# Configure debug logging
logger = setup_logger("agent_nodes")

# ============================================================================
# DATASET / FEW-SHOT HELPERS
# ============================================================================

def get_few_shot_examples(intent_type: str = None, limit: int = 5):
    """Retrieve gold-quality examples for few-shot prompting."""
    db = SessionLocal()
    try:
        query = db.query(DatasetItem).filter(
            DatasetItem.quality == "gold",
            DatasetItem.is_active == True
        )
        
        if intent_type:
            query = query.filter(DatasetItem.category == intent_type.lower())
        
        examples = query.order_by(DatasetItem.created_at.desc()).limit(limit).all()
        return examples
    finally:
        db.close()

# Initialize LLM
llm = ChatOllama(model="llama3.1:8b", temperature=0)

@run_in_thread
def manage_history(state: ChatState):
    """
    Finds/Creates conversation, saves user message, and loads history.
    """
    db = SessionLocal()
    try:
        user_id = state["user_id"]
        channel = state["channel"]
        content = state["current_input"]
        
        # Find or create conversation (OMNICHANNEL: one conversation per user)
        conversation = db.query(Conversation).filter(
            Conversation.user_identifier == user_id
        ).first()
        
        if not conversation:
            # Store the first channel they used, but this is just metadata
            conversation = Conversation(
                user_identifier=user_id,
                channel=channel,  # First contact channel
                created_at=datetime.utcnow()
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
        convo_id = conversation.id
        
        # Save user message with channel tracking
        new_msg = Message(
            conversation_id=convo_id,
            content=content,
            sender='user',
            channel=channel,  # Track which channel this message came from
            timestamp=datetime.utcnow()
        )
        db.add(new_msg)
        db.commit()
        
        # Load history (last 10 messages for context)
        history_records = db.query(Message).filter(
            Message.conversation_id == convo_id
        ).order_by(Message.timestamp.asc()).all()[-10:]
        
        messages = []
        for rec in history_records:
            if rec.sender == 'user':
                messages.append(HumanMessage(content=rec.content))
            else:
                messages.append(AIMessage(content=rec.content))
                
        return {"conversation_id": convo_id, "messages": messages}
        
    finally:
        db.close()

@run_in_thread
def classify_message(state: ChatState):
    """
    Classifies the user's intent based on the conversation history.
    Uses few-shot examples from dataset for improved accuracy.
    """
    messages = state["messages"]
    
    # Get few-shot examples (gold quality)
    try:
        examples = get_few_shot_examples(limit=5)
        few_shot_text = "\n".join([
            f"User: {ex.user_input}\nIntent: {ex.expected_intent}"
            for ex in examples if ex.expected_intent
        ])
    except Exception as e:
        logger.warning(f"Could not load few-shot examples: {e}")
        few_shot_text = ""
    
    # Build system prompt with examples
    system_prompt = "You are an intelligent agent classifier."
    
    if few_shot_text:
        system_prompt += f"\n\nExamples of correct classifications:\n{few_shot_text}\n"
    
    system_prompt += "\nAnalyze the conversation and classify the user's LATEST intent into one of these categories: [SALES, SUPPORT, COMPLAINT, GENERAL]. Return ONLY the category name."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    
    # Simple fallback if model generates extra text
    intent = response.content.strip().upper()
    valid_intents = ["SALES", "SUPPORT", "COMPLAINT", "GENERAL"]
    if not any(v in intent for v in valid_intents):
        intent = "GENERAL"
        
    return {"intent": intent}

@run_in_thread
def generate_response(state: ChatState):
    """
    Generates a response based on the intent, history, and channel-specific formatting.
    Personalizes response with user's name if available.
    On first contact WITHOUT a name, asks for name BEFORE answering questions.
    """
    messages = state["messages"]
    intent = state.get("intent", "GENERAL")
    channel = state.get("channel", "unknown")
    user_context = state.get("user_context", "")
    user_profile = state.get("user_profile")
    is_first_contact = state.get("is_first_contact", False)
    has_name = state.get("has_name", False)
    
    # PRIORITY: If first contact and no name, ask for name FIRST
    if is_first_contact and not has_name:
        # Generate a friendly name request based on channel
        if channel == "whatsapp":
            return {
                "response": "Olá! 👋 Antes de começar, qual é o seu nome? Assim posso te atender melhor!"
            }
        elif channel == "email":
            return {
                "response": "Olá! Seja bem-vindo(a). Para que eu possa oferecer um atendimento personalizado, poderia me informar seu nome, por favor?"
            }
        elif channel == "telegram":
            return {
                "response": "Olá! 😊 Qual é o seu nome? Vou te atender melhor sabendo como te chamar!"
            }
        else:
            return {
                "response": "Olá! Antes de prosseguir, poderia me informar seu nome para um atendimento personalizado?"
            }
    
    # Get user's name if available
    user_name = None
    if user_profile and user_profile.get("name"):
        user_name = user_profile["name"]
        
    # PRIORITY 2: If known user returns with a greeting
    if user_name and not is_first_contact:
        current_input = state.get("current_input", "").lower()
        # Check for simple greetings (short messages with greeting words)
        is_greeting = any(w in current_input for w in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "voltei", "tudobem"])
        if is_greeting and len(current_input.split()) <= 5:
             return {
                "response": f"Oi {user_name}, que bom tê-lo de volta! Como posso ajudar?"
            }
    
    # Channel-specific styling instructions
    if channel == "whatsapp":
        style_instruction = "Keep responses under 2 sentences. Use emojis appropriately. Be casual and friendly."
    elif channel == "email":
        style_instruction = "Use formal business language. Include a greeting and professional closing. Structure with clear paragraphs."
    elif channel == "telegram":
        style_instruction = "Be concise but informative. You can use markdown formatting if helpful."
    else:
        style_instruction = "Be professional and helpful."
    
    # Retrieve RAG context
    retrieved_context = state.get("retrieved_context", "")
    
    # Get few-shot examples for this intent (for response quality)
    try:
        examples = get_few_shot_examples(intent_type=intent, limit=3)
        few_shot_responses = "\n".join([
            f"Q: {ex.user_input}\nA: {ex.expected_response}"
            for ex in examples if ex.expected_response
        ])
    except Exception as e:
        logger.warning(f"Could not load few-shot examples: {e}")
        few_shot_responses = ""

    # Build system prompt with context and styling
    system_prompt = (
        f"You are a helpful assistant responding via {channel}. "
        f"The user's intent is classified as: {intent}. "
        f"{style_instruction}\n"
    )
    
    # Add RAG Context if available - IMPROVED PROMPT
    if retrieved_context:
        system_prompt += f"""

=== KNOWLEDGE BASE (CRITICAL - USE THIS INFORMATION) ===
{retrieved_context}
=== END OF KNOWLEDGE BASE ===

INSTRUCTIONS FOR USING THE KNOWLEDGE BASE:
1. ALWAYS search the knowledge base above FIRST before answering.
2. If the answer exists in the knowledge base, USE IT EXACTLY as stated. Do not paraphrase important details like prices, hours, or technical specifications.
3. Quote specific values (prices, hours, packages) directly from the knowledge base.
4. If the question is about our services/products/prices, the answer MUST come from the knowledge base.
5. If you cannot find the answer in the knowledge base, say: "Não encontrei essa informação específica na minha base de conhecimento. Posso encaminhar para um atendente."
6. NEVER invent information about our company, prices, services, or policies.
7. If the user asks something partially covered, answer what you can and clarify what's missing.
"""

    # Add personalization instructions
    if user_name:
        system_prompt += f"\nThe user's name is {user_name}. Use their name naturally in your response to create a personalized experience.\n"
    
    if user_context:
        system_prompt += f"\nUser Context (from previous conversations): {user_context}\n"
    
    # Add few-shot examples for quality
    if few_shot_responses:
        system_prompt += f"\n\nExamples of high-quality responses for {intent}:\n{few_shot_responses}\n"
    
    system_prompt += "Maintain conversation context. Be helpful and accurate."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    
    # TRANSACTIONAL SAFETY: Save response immediately after generation
    response_text = response.content
    db = SessionLocal()
    try:
        convo_id = state["conversation_id"]
        channel = state.get("channel", "unknown")
        
        if response_text:
            msg = Message(
                conversation_id=convo_id,
                content=response_text,
                sender='agent',
                channel=channel,  # Track which channel the response was sent to
                timestamp=datetime.utcnow()
            )
            db.add(msg)
            db.commit()
            logger.info(f"Response saved immediately after generation (channel: {channel})")
    except Exception as e:
        logger.error(f"Failed to save response: {e}")
        db.rollback()
    finally:
        db.close()
    
    return {"response": response_text}

def save_response(state: ChatState):
    """
    DEPRECATED: Response is now saved immediately in generate_response for transactional safety.
    This node is kept for backward compatibility but does nothing.
    """
    logger.info("save_response called (no-op, already saved in generate_response)")
    return {}


@run_in_thread
def retrieve_knowledge(state: ChatState):
    """
    Retrieves relevant knowledge from the local vector store based on the user's input.
    """
    current_input = state["current_input"]
    logger.info(f"Retrieving knowledge for: {current_input}")
    
    context = retrieve_context(current_input)
    
    if context:
        logger.info(f"Retrieved {len(context)} characters of context.")
    else:
        logger.info("No relevant context found.")
        
    return {"retrieved_context": context}

# ============ NEW NODES FOR ADVANCED FEATURES ============

@run_in_thread
def load_user_context(state: ChatState):
    """
    Loads user's long-term context from database.
    """
    db = SessionLocal()
    try:
        user_id = state["user_id"]
        channel = state["channel"]
        
        # Omnichannel Support: Load the most recent context from ANY channel for this user
        context = db.query(UserContext).filter(
            UserContext.user_identifier == user_id
        ).order_by(UserContext.last_updated.desc()).first()
        
        if context:
            return {"user_context": context.context_summary}
        return {"user_context": None}
    finally:
        db.close()

@run_in_thread
def detect_critical_action(state: ChatState):
    """
    Detects if the interaction requires human approval using LLM.
    Covers: Refunds, Deletions, Permission Issues, and Sensitive Information Requests.
    """
    current_input = state.get("current_input", "").lower()
    response = state.get("response", "").lower()
    
    logger.info(f"DetectCritical: Analyzing input: '{current_input}'")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a specific Compliance Officer. Analyze the conversation for actions requiring manager approval.

        CRITICAL TRIGGERS for Approval:
        1. FINANCIAL: Refunds, discounts > 20%, payments, reimbursements (Keywords: estorno, reembolso, refund).
        2. SECURITY: Account deletion, data removal, password resets (Keywords: delete account, excluir dados).
        3. PERMISSION: User asks for high-level permissions or actions the agent cannot typically perform (e.g. "change database", "restart system").
        4. UNKNOWN_SENSITIVE: User asks for internal/confidential info or the agent explicitly says "I don't have permission" or "I don't know" regarding a sensitive topic.

        Return strictly a JSON object with this format (no other text):
        {{
            "requires_approval": true/false,
            "type": "refund" | "account_deletion" | "permission_issue" | "sensitive_info" | "none",
            "description": "Brief description of the request for the manager"
        }}
        """),
        ("human", "User Input: {input}\nAgent Response: {response}")
    ])
    
    chain = prompt | llm
    
    try:
        # Strict JSON mode for parsing reliability
        result = chain.invoke({"input": current_input, "response": response})
        content = result.content.strip()
        
        # Clean up potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[0].strip()
            
        analysis = json.loads(content)
        
        if analysis.get("requires_approval"):
            logger.info(f"DetectCritical: Triggered {analysis['type']}")
            return {
                "requires_approval": True,
                "pending_action": {
                    "type": analysis.get("type", "critical_action"),
                    "details": {"user_message": current_input, "agent_response_preview": response[:100]},
                    "description": analysis.get("description", "Action requires approval")
                }
            }
            
    except Exception as e:
        logger.error(f"Error in LLM detection: {e}")
        # Fallback to keyword safety net
        keywords = ["estorno", "reembolso", "cancelar conta", "excluir"]
        if any(k in current_input for k in keywords):
             return {
                "requires_approval": True,
                "pending_action": {
                    "type": "critical_action_fallback",
                    "details": {"user_message": current_input},
                    "description": "Critical keyword detected (fallback)"
                }
            }
            
    return {"requires_approval": False}

@run_in_thread
def create_pending_action(state: ChatState):
    """
    Creates a pending action record in the database for HITL approval.
    """
    db = SessionLocal()
    try:
        convo_id = state["conversation_id"]
        pending_action = state["pending_action"]
        
        # Generate thread_id for LangGraph resumption
        # Generate thread_id for LangGraph resumption - UNIFIED
        thread_id = f"user_{state['user_id']}"
        
        action_record = PendingAction(
            conversation_id=convo_id,
            action_type=pending_action["type"],
            action_details=json.dumps(pending_action["details"]),
            action_description=pending_action["description"],
            status="pending",
            thread_id=thread_id,
            created_at=datetime.utcnow()
        )
        
        db.add(action_record)
        db.commit()
        db.refresh(action_record)
        
        return {"pending_action_id": action_record.id}
    finally:
        db.close()

def execute_approved_action(state: ChatState):
    """
    Executes the approved action OR handles the rejection.
    """
    pending_action = state.get("pending_action", {})
    action_type = pending_action.get("type", "unknown")
    
    # Check if action was approved (injected by main.py via update_state)
    is_approved = state.get("action_approved", False)
    
    if not is_approved:
        # Action was rejected
        rejection_msg = "❌ Solictação Rejeitada: O Gerente não autorizou esta ação no momento."
        
        # Add context-specific rejection detail if possible
        if action_type == "refund":
             rejection_msg += " Para questões financeiras, por favor entre em contato com o suporte telefônico."
             
        current_response = state.get("response", "")
        updated_response = f"{current_response}\n\n{rejection_msg}"
        return {"response": updated_response}
    
    # Simulate action execution (Approved case)
    if action_type == "refund":
        execution_result = "✓ Refund processed successfully. Amount will be credited within 5-7 business days."
    elif action_type == "account_deletion":
        execution_result = "✓ Account deletion initiated. Your data will be removed within 30 days as per GDPR."
    else:
        execution_result = f"✓ Action '{action_type}' executed successfully."
    
    # Update response to include execution result
    current_response = state.get("response", "")
    updated_response = f"{current_response}\n\n{execution_result}"
    
    return {"response": updated_response}

@run_in_thread
def summarize_conversation(state: ChatState):
    """
    Updates user's long-term memory (summary) with the latest interaction.
    Runs on every turn to ensure context is always up-to-date.
    """
    current_input = state.get("current_input", "")
    response_text = state.get("response", "")
    existing_summary = state.get("user_context") or "No previous context."
    
    # Skip if empty interaction
    if not current_input or not response_text:
        logger.info("Summarize: Skipping due to empty input/response")
        return {"should_summarize": False}
        
    logger.info(f"Summarize: Generating summary for user {state['user_id']}")
    
    # Simplified prompt to avoid empty OLLAMA responses
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant updating a user's memory profile."),
        ("human", """Current Memory: {existing_summary}
        
Update this memory with the following new interaction:
User: {user_input}
AI: {ai_response}

Instructions:
1. Merge new facts into the existing memory.
2. Be concise.
3. Return ONLY the updated summary text.
"""),
    ])
    
    chain = prompt | llm
    try:
        inputs = {
            "existing_summary": existing_summary, 
            "user_input": current_input, 
            "ai_response": response_text
        }
        logger.info(f"Summarize Inputs: {json.dumps(inputs, ensure_ascii=False)}")
        
        response = chain.invoke(inputs)
        
        logger.info(f"Summarize LLM Output: '{response.content}'")
        
        if not response.content:
            logger.warning("Summarize: LLM returned empty content!")
        
        return {
            "conversation_summary": response.content,
            "should_summarize": True
        }
    except Exception as e:
        logger.error(f"Error summarizing conversation: {e}")
        print(f"Error summarizing conversation: {e}")
        return {"should_summarize": False}

@run_in_thread
def save_user_context(state: ChatState):
    """
    Saves or updates user context in the database.
    """
    db = SessionLocal()
    try:
        user_id = state["user_id"]
        channel = state["channel"]
        summary = state.get("conversation_summary", "")
        
        if not summary:
            logger.warning("SaveContext: No summary to save")
            return {}
        
        logger.info(f"SaveContext: Saving summary for {user_id}")
        
        # Check if context exists
        context = db.query(UserContext).filter(
            UserContext.user_identifier == user_id,
            UserContext.channel == channel
        ).first()
        
        if context:
            # Update existing context (Overwrite with new refined summary)
            context.context_summary = summary
            context.last_updated = datetime.utcnow()
            context.conversation_count += 1
        else:
            # Create new context
            context = UserContext(
                user_identifier=user_id,
                channel=channel,
                context_summary=summary,
                last_updated=datetime.utcnow(),
                conversation_count=1
            )
            db.add(context)
        
        db.commit()
        return {}
    finally:
        db.close()


# ============ USER PROFILE MANAGEMENT NODES ============

@run_in_thread
def check_user_profile(state: ChatState):
    """
    Checks if user profile exists and loads it.
    Sets is_first_contact flag if this is the first interaction.
    """
    db = SessionLocal()
    try:
        user_id = state["user_id"]
        
        profile = db.query(UserProfile).filter(
            UserProfile.user_identifier == user_id
        ).first()
        
        if profile:
            # User exists - load profile info
            profile_data = {
                "name": profile.name,
                "email": profile.email,
                "phone": profile.phone,
                "preferences": json.loads(profile.preferences) if profile.preferences else {}
            }
            
            # Mark as not first contact anymore if it was
            if profile.is_first_contact:
                profile.is_first_contact = False
                db.commit()
            
            return {
                "user_profile": profile_data,
                "is_first_contact": False,
                "has_name": profile.name is not None
            }
        else:
            # New user - create profile
            new_profile = UserProfile(
                user_identifier=user_id,
                channel=state["channel"],
                is_first_contact=True
            )
            db.add(new_profile)
            db.commit()
            
            return {
                "user_profile": None,
                "is_first_contact": True,
                "has_name": False
            }
    finally:
        db.close()

@run_in_thread
def extract_user_info(state: ChatState):
    """
    Uses LLM to extract user information (name, email, etc.) from the conversation.
    """
    messages = state["messages"]
    current_input = state.get("current_input", "")
    
    # Only try to extract if we don't have a name yet
    if state.get("has_name"):
        return {}
    
    # Simple pattern matching for common name patterns (faster than LLM)
    simple_patterns = [
        r"(?:meu nome é|me chamo|sou o|sou a|pode me chamar de)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)*)",
        r"^([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)*)$",  # Just a name
        r"(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    ]
    
    for pattern in simple_patterns:
        match = re.search(pattern, current_input, re.IGNORECASE)
        if match:
            extracted_name = match.group(1).strip()
            # Validate it's not too short or too long
            if 2 <= len(extracted_name) <= 50 and not any(word in extracted_name.lower() for word in ['olá', 'oi', 'hello', 'hi']):
                return {"extracted_name": extracted_name}
    
    # Fallback to LLM for complex cases
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an information extractor. Analyze the conversation and extract the user's name if mentioned.
        
Rules:
- Only extract if the user explicitly provides their name
- Common patterns: "My name is X", "I'm X", "This is X", "Call me X", "Meu nome é X", "Me chamo X"
- Return ONLY the name, nothing else
- If no name is found, return "NONE"
- Do not make assumptions or extract names from greetings

Examples:
User: "Hi, my name is Maria" -> Maria
User: "I'm John Silva" -> John Silva
User: "Call me Ana" -> Ana
User: "Meu nome é Carlos" -> Carlos
User: "What are your hours?" -> NONE
"""),
        ("placeholder", "{messages}"),
        ("human", "{current_input}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "messages": messages,
        "current_input": current_input
    })
    
    extracted_name = response.content.strip()
    
    if extracted_name and extracted_name != "NONE":
        return {"extracted_name": extracted_name}
    
    return {}

@run_in_thread
def save_user_profile(state: ChatState):
    """
    Saves extracted user information to the profile.
    """
    db = SessionLocal()
    try:
        user_id = state["user_id"]
        extracted_name = state.get("extracted_name")
        
        if not extracted_name:
            return {}
        
        profile = db.query(UserProfile).filter(
            UserProfile.user_identifier == user_id
        ).first()
        
        if profile:
            profile.name = extracted_name
            profile.updated_at = datetime.utcnow()
            db.commit()
            
            return {"profile_updated": True}
        
        return {}
    finally:
        db.close()


