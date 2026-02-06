from typing import TypedDict, List
from typing import Annotated
from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    # Input
    messages: Annotated[List[BaseMessage], add_messages]  # History of messages
    current_input: str
    channel: str
    user_id: str
    conversation_id: Optional[int]
    
    # Analysis
    intent: Optional[str]
    sentiment: Optional[str]
    
    # Output
    response: Optional[str]
    
    # Control
    iteration_count: int
    
    # Human-in-the-Loop (HITL)
    requires_approval: Optional[bool]
    pending_action: Optional[dict]  # {type, details, description}
    pending_action_id: Optional[int]
    action_approved: Optional[bool]
    
    # Long-term Memory
    user_context: Optional[str]  # Retrieved context summary
    should_summarize: Optional[bool]
    conversation_summary: Optional[str]
    retrieved_context: Optional[str]  # RAG context
    
    # Omnichannel Routing
    response_style: Optional[str]  # "formal", "casual", "concise"
    
    # User Profile
    user_profile: Optional[dict]  # {name, email, phone, preferences}
    is_first_contact: Optional[bool]
    has_name: Optional[bool]
    extracted_name: Optional[str]
    profile_updated: Optional[bool]
