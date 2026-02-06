from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, index=True)  # e.g., 'whatsapp', 'email', 'telegram'
    user_identifier = Column(String, index=True)  # e.g., phone number, email address
    created_at = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    content = Column(Text)
    sender = Column(String)  # 'user' or 'agent'
    channel = Column(String, nullable=True)  # Track which channel this message came from
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class UserContext(Base):
    """Long-term memory storage for user preferences and conversation summaries."""
    __tablename__ = "user_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_identifier = Column(String, index=True)
    channel = Column(String, index=True)
    context_summary = Column(Text)  # AI-generated summary of key points
    last_updated = Column(DateTime, default=datetime.utcnow)
    conversation_count = Column(Integer, default=0)

class UserProfile(Base):
    """Stores structured user profile information (name, preferences, etc.)."""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_identifier = Column(String, unique=True, index=True)
    channel = Column(String, index=True)
    name = Column(String, nullable=True)  # User's name
    email = Column(String, nullable=True)  # Email if provided
    phone = Column(String, nullable=True)  # Phone if provided
    preferences = Column(Text, nullable=True)  # JSON string with preferences
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_first_contact = Column(Boolean, default=True)  # Flag for first interaction

class PendingAction(Base):
    """Stores actions requiring human approval (HITL)."""
    __tablename__ = "pending_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    action_type = Column(String)  # e.g., "refund", "account_deletion"
    action_details = Column(Text)  # JSON string with action parameters
    action_description = Column(Text)  # Human-readable description
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    thread_id = Column(String)  # LangGraph thread ID for resumption
    
    conversation = relationship("Conversation")

class DatasetItem(Base):
    """Stores training/evaluation examples for few-shot learning and testing."""
    __tablename__ = "dataset_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Input/Output
    user_input = Column(Text, nullable=False)
    expected_intent = Column(String, nullable=True)  # For classification (SALES, SUPPORT, etc.)
    expected_response = Column(Text, nullable=True)  # For generation quality
    
    # Metadata
    category = Column(String, index=True)  # e.g., "sales", "support", "pricing"
    quality = Column(String, default="silver")  # "gold", "silver", "bronze"
    source = Column(String)  # "manual", "production", "synthetic"
    
    # Context (optional)
    channel = Column(String, nullable=True)
    user_context = Column(Text, nullable=True)
    
    # Versioning
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
