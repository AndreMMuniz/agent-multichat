import os
from logging_config import setup_logger, get_recent_logs
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from graph import app_graph
from database import get_db, engine, Base
from models import Message, Conversation, PendingAction, UserContext, UserProfile

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize logger
logger = setup_logger("api_main")

app = FastAPI(title="Multichat Agent API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class MessageInput(BaseModel):
    channel: str # email, whatsapp, telegram, etc.
    user_identifier: str
    content: str

class ChatResponse(BaseModel):
    status: str  # "completed", "pending_approval", "interrupted"
    response: Optional[str] = None
    conversation_id: Optional[int] = None
    intent: Optional[str] = None
    pending_action_id: Optional[int] = None
    action_description: Optional[str] = None
    processed_at: datetime = datetime.now()

class MessageSchema(BaseModel):
    id: int
    content: str
    sender: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(input_data: MessageInput):
    """
    Main endpoint for chat interactions with HITL support.
    Receives user message, processes it via the agent graph, and returns a response.
    May return pending_approval status if critical action is detected.
    """
    try:
        # Generate thread_id for checkpointer - UNIFIED for omnichannel support
        # We use a user-centric thread_id so state is shared across all channels
        thread_id = f"user_{input_data.user_identifier}"
        
        # Initial state for the graph
        initial_state = {
            "messages": [],
            "current_input": input_data.content,
            "channel": input_data.channel,
            "user_id": input_data.user_identifier,
            "iteration_count": 0
        }
        
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 25  # Increased for longer workflow with profile nodes
        }
        
        # Invoke the graph
        final_state = await app_graph.ainvoke(initial_state, config=config)
        
        # Check if graph was interrupted (HITL)
        state_snapshot = app_graph.get_state(config)
        
        if state_snapshot.next:  # Graph is interrupted
            return {
                "status": "pending_approval",
                "conversation_id": final_state.get("conversation_id"),
                "intent": final_state.get("intent"),
                "pending_action_id": final_state.get("pending_action_id"),
                "action_description": final_state.get("pending_action", {}).get("description"),
                "response": "Action requires approval. Please review and approve/reject.",
                "processed_at": datetime.now()
            }
        else:
            return {
                "status": "completed",
                "response": final_state.get("response", "No response generated."),
                "conversation_id": final_state.get("conversation_id"),
                "intent": final_state.get("intent"),
                "processed_at": datetime.now()
            }
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{channel}/{user_identifier}", response_model=List[MessageSchema])
async def get_history(channel: str, user_identifier: str, db: Session = Depends(get_db)):
    """
    Retrieves full conversation history. 
    NOTE: Currently returns channel-specific history for UI display, 
    but the Agent maintains a unified internal state.
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.channel == channel,
            Conversation.user_identifier == user_identifier
        ).first()
        
        if not conversation:
            return []
            
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.timestamp.asc()).all()
        
        return messages
    except Exception as e:
        print(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ NEW ENDPOINTS FOR ADVANCED FEATURES ============

class ApprovalRequest(BaseModel):
    approved: bool

class PendingActionSchema(BaseModel):
    id: int
    action_type: str
    action_description: str
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserContextSchema(BaseModel):
    context_summary: str
    last_updated: datetime
    conversation_count: int
    
    model_config = ConfigDict(from_attributes=True)

@app.post("/approve-action/{action_id}")
async def approve_action(action_id: int, approval: ApprovalRequest, db: Session = Depends(get_db)):
    """
    Approve or reject a pending action and resume graph execution.
    """
    try:
        # Get pending action
        action = db.query(PendingAction).filter(PendingAction.id == action_id).first()
        
        if not action:
            raise HTTPException(status_code=404, detail="Pending action not found")
        
        if action.status != "pending":
            raise HTTPException(status_code=400, detail="Action already processed")
        
        # Update action status
        action.status = "approved" if approval.approved else "rejected"
        action.resolved_at = datetime.utcnow()
        db.commit()
        
        # Resume graph execution regardless of approval status
        # This allows the agent to inform the user about the decision
        config = {"configurable": {"thread_id": action.thread_id}}
        
        # Update state with approval status
        current_state = app_graph.get_state(config)
        updated_state = {**current_state.values, "action_approved": approval.approved}
        
        # Update state with the decision
        app_graph.update_state(config, {"action_approved": approval.approved})
        
        # Resume from interrupt
        final_state = await app_graph.ainvoke(None, config=config)
        
        if approval.approved:
            return {
                "status": "approved",
                "message": "Action approved and executed",
                "response": final_state.get("response")
            }
        else:
            return {
                "status": "rejected",
                "message": "Action rejected by user",
                "response": final_state.get("response")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error approving action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pending-actions/{channel}/{user_identifier}", response_model=List[PendingActionSchema])
async def get_pending_actions(channel: str, user_identifier: str, db: Session = Depends(get_db)):
    """
    Get all pending actions for a user.
    We verify user identity. Channel is less relevant if we want omnichannel, 
    but the frontend passes it in.
    """
    try:
        # We search for pending actions for this user across ALL channels (or specifically this one)
        # For true omnichannel, we should arguably show all pending actions for this user.
        # But let's stick to the conversation link for safety first, or just join tables.
        
        # Better approach: Find actions linked to conversations of this user
        actions = db.query(PendingAction).join(Conversation).filter(
            Conversation.user_identifier == user_identifier,
            PendingAction.status == "pending"
        ).order_by(PendingAction.created_at.desc()).all()
        
        return actions
    except Exception as e:
        print(f"Error fetching pending actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-context/{channel}/{user_identifier}", response_model=Optional[UserContextSchema])
async def get_user_context(channel: str, user_identifier: str, db: Session = Depends(get_db)):
    """
    Get user's long-term memory context.
    Prioritizes the most recently updated context across ANY channel for this user.
    """
    try:
        context = db.query(UserContext).filter(
            UserContext.user_identifier == user_identifier
        ).order_by(UserContext.last_updated.desc()).first()
        
        if not context:
            return None
        
        return context
    except Exception as e:
        print(f"Error fetching user context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class UserProfileSchema(BaseModel):
    user_identifier: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_first_contact: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

@app.get("/user-profile/{user_identifier}", response_model=Optional[UserProfileSchema])
async def get_user_profile(user_identifier: str, db: Session = Depends(get_db)):
    """
    Get user's profile information (name, email, etc.).
    """
    try:
        profile = db.query(UserProfile).filter(
            UserProfile.user_identifier == user_identifier
        ).first()
        
        if not profile:
            return None
        
        return profile
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server...")
    # Binding to 127.0.0.1 for local development
    uvicorn.run(app, host="127.0.0.1", port=8000)

@app.get("/logs", tags=["Admin"])
async def read_logs(lines: int = 50):
    """
    Get recent system logs for analysis.
    Useful for debugging errors or checking execution flow.
    """
    return {"logs": get_recent_logs(lines)}