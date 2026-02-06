from langgraph.graph import StateGraph, START, END
from checkpointer import SQLAlchemyCheckpointer
from database import engine
from state import ChatState
from nodes import (
    manage_history, check_user_profile, load_user_context, classify_message, 
    generate_response, extract_user_info, save_user_profile,
    detect_critical_action, create_pending_action,
    execute_approved_action, save_response, summarize_conversation,
    save_user_context, retrieve_knowledge
)

# Initialize with PERSISTENT PostgreSQL checkpointer for HITL
# Using custom SQLAlchemy-based checkpointer (psycopg2 compatible)
checkpointer = SQLAlchemyCheckpointer(engine)
checkpointer.setup()  # Creates checkpoint table if it doesn't exist

workflow = StateGraph(ChatState)

# Add all nodes
workflow.add_node("manage_history", manage_history)
workflow.add_node("check_user_profile", check_user_profile)
workflow.add_node("load_user_context", load_user_context)
workflow.add_node("classify_message", classify_message)
workflow.add_node("generate_response", generate_response)
workflow.add_node("extract_user_info", extract_user_info)
workflow.add_node("save_user_profile", save_user_profile)
workflow.add_node("detect_critical_action", detect_critical_action)
workflow.add_node("create_pending_action", create_pending_action)
workflow.add_node("execute_approved_action", execute_approved_action)
workflow.add_node("save_response", save_response)
workflow.add_node("summarize_conversation", summarize_conversation)
workflow.add_node("save_user_context", save_user_context)
workflow.add_node("retrieve_knowledge", retrieve_knowledge)

# Build workflow - LINEAR FLOW with conditionals
workflow.add_edge(START, "manage_history")
workflow.add_edge("manage_history", "check_user_profile")
workflow.add_edge("check_user_profile", "load_user_context")
workflow.add_edge("load_user_context", "classify_message")
workflow.add_edge("load_user_context", "classify_message")
workflow.add_edge("classify_message", "retrieve_knowledge")
workflow.add_edge("retrieve_knowledge", "generate_response")

# After generating response, extract user info and save profile
workflow.add_edge("generate_response", "extract_user_info")
workflow.add_edge("extract_user_info", "save_user_profile")

# Then check for critical actions
workflow.add_edge("save_user_profile", "detect_critical_action")

# Conditional routing for critical actions (HITL)
def should_interrupt(state: ChatState) -> str:
    """Route to pending action creation if approval is required."""
    if state.get("requires_approval"):
        return "create_pending"
    return "save_response"

workflow.add_conditional_edges(
    "detect_critical_action",
    should_interrupt,
    {
        "create_pending": "create_pending_action",
        "save_response": "save_response"
    }
)

# Interrupt before executing critical action (wait for human approval)
workflow.add_edge("create_pending_action", "execute_approved_action")

# Continue to save and summarize
workflow.add_edge("execute_approved_action", "save_response")
workflow.add_edge("save_response", "summarize_conversation")

# Conditional: only save context if conversation is substantial
def should_save_context(state: ChatState) -> str:
    """Route to context saving if summary was generated."""
    if state.get("should_summarize"):
        return "save_context"
    return "end"

workflow.add_conditional_edges(
    "summarize_conversation",
    should_save_context,
    {
        "save_context": "save_user_context",
        "end": END
    }
)

workflow.add_edge("save_user_context", END)

# Compile with PERSISTENT checkpointer and interrupt
app_graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute_approved_action"]
)