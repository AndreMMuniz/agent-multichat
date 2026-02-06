"""
Custom PostgreSQL Checkpointer using SQLAlchemy (compatible with psycopg2).
This is a workaround for Windows environments where psycopg v3 (libpq) is not available.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import pickle
from typing import Optional, Iterator, Tuple, Any, List
import logging
from database import engine, Base as AppBase

# Checkpoint table model
class CheckpointRecord(AppBase):
    __tablename__ = "langgraph_checkpoints"
    
    thread_id = Column(String, primary_key=True)
    checkpoint_ns = Column(String, primary_key=True, default="")
    checkpoint_id = Column(String, primary_key=True)
    parent_checkpoint_id = Column(String, nullable=True)
    checkpoint_data = Column(Text)  # Pickled checkpoint
    metadata_data = Column(Text, nullable=True)  # JSON metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class CheckpointWrite(AppBase):
    __tablename__ = "langgraph_writes"
    
    thread_id = Column(String, primary_key=True)
    checkpoint_ns = Column(String, primary_key=True, default="")
    checkpoint_id = Column(String, primary_key=True)
    task_id = Column(String, primary_key=True)
    idx = Column(String, primary_key=True)
    channel = Column(String)
    type = Column(String, nullable=True)
    value = Column(Text)  # Pickled value
    created_at = Column(DateTime, default=datetime.utcnow)

class SQLAlchemyCheckpointer(BaseCheckpointSaver):
    """PostgreSQL checkpointer using SQLAlchemy (psycopg2 compatible)."""
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=engine)
        
    def setup(self):
        """Create checkpoint tables if they don't exist."""
        CheckpointRecord.__table__.create(self.engine, checkfirst=True)
        CheckpointWrite.__table__.create(self.engine, checkfirst=True)
        
    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Optional[dict] = None,
    ) -> dict:
        """Save a checkpoint."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        session = self.SessionLocal()
        try:
            record = CheckpointRecord(
                thread_id=thread_id,
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint["id"],
                parent_checkpoint_id=checkpoint.get("parent_id"),
                checkpoint_data=pickle.dumps(checkpoint).hex(),
                metadata_data=json.dumps(metadata) if metadata else None
            )
            
            # Upsert logic
            existing = session.query(CheckpointRecord).filter_by(
                thread_id=thread_id,
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint["id"]
            ).first()
            
            if existing:
                existing.checkpoint_data = record.checkpoint_data
                existing.metadata_data = record.metadata_data
                existing.created_at = datetime.utcnow()
            else:
                session.add(record)
                
            session.commit()
            session.commit()
            
            return {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": checkpoint["id"],
                }
            }
            
        finally:
            session.close()
    
    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Retrieve the latest checkpoint for a thread."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        session = self.SessionLocal()
        try:
            record = session.query(CheckpointRecord).filter_by(
                thread_id=thread_id,
                checkpoint_ns=checkpoint_ns
            ).order_by(CheckpointRecord.created_at.desc()).first()
            
            if not record:
                return None
                
            checkpoint = pickle.loads(bytes.fromhex(record.checkpoint_data))
            metadata = json.loads(record.metadata_data) if record.metadata_data else {}
            
            return CheckpointTuple(
                config,
                checkpoint,
                metadata,
                (
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": record.parent_checkpoint_id,
                        }
                    }
                    if record.parent_checkpoint_id
                    else None
                ),
            )
            
        finally:
            session.close()
    
    def list(
        self,
        config: dict,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints for a thread."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        session = self.SessionLocal()
        try:
            query = session.query(CheckpointRecord).filter_by(
                thread_id=thread_id,
                checkpoint_ns=checkpoint_ns
            ).order_by(CheckpointRecord.created_at.desc())
            
            if limit:
                query = query.limit(limit)
                
            for record in query:
                checkpoint = pickle.loads(bytes.fromhex(record.checkpoint_data))
                metadata = json.loads(record.metadata_data) if record.metadata_data else {}
                yield CheckpointTuple(
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": record.checkpoint_id,
                        }
                    },
                    checkpoint,
                    metadata,
                    (
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "checkpoint_ns": checkpoint_ns,
                                "checkpoint_id": record.parent_checkpoint_id,
                            }
                        }
                        if record.parent_checkpoint_id
                        else None
                    ),
                )
                
        finally:
            session.close()

    def put_writes(
        self,
        config: dict,
        writes: List[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Save writes (node outputs) to database."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        # Checkpoint ID handling with fallback
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        if not checkpoint_id:
            # Fallback: Get latest checkpoint ID for this thread
            # This is necessary if LangGraph doesn't pass the updated config from put
            session = self.SessionLocal()
            try:
                latest = session.query(CheckpointRecord).filter_by(
                    thread_id=thread_id,
                    checkpoint_ns=checkpoint_ns
                ).order_by(CheckpointRecord.created_at.desc()).first()
                if latest:
                    checkpoint_id = latest.checkpoint_id
            finally:
                session.close()
                
        if not checkpoint_id:
            logger_debug = logging.getLogger("checkpointer") # Using dedicated logger or just print
            print(f"Warning: No checkpoint_id found for writes (thread_id={thread_id})")
            return
            
        session = self.SessionLocal()
        try:
            for idx, (channel, value) in enumerate(writes):
                # Serialize value
                serialized_value = pickle.dumps(value).hex()
                
                record = CheckpointWrite(
                    thread_id=thread_id,
                    checkpoint_ns=checkpoint_ns,
                    checkpoint_id=checkpoint_id,
                    task_id=task_id,
                    idx=str(idx),
                    channel=channel,
                    type=None,
                    value=serialized_value
                )
                
                # Upsert logic (simplified: merge)
                session.merge(record)
                
            session.commit()
        except Exception as e:
            print(f"Error saving writes: {e}")
            session.rollback()
        finally:
            session.close()
    
    # ============ ASYNC METHODS (Non-blocking) ============
    
    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Optional[dict] = None,
    ) -> dict:
        """Async version of put - runs sync method in thread pool."""
        import asyncio
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: dict,
        writes: List[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Async version of put_writes - runs sync method in thread pool."""
        import asyncio
        return await asyncio.to_thread(self.put_writes, config, writes, task_id)
    
    async def aget_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Async version of get_tuple - runs sync method in thread pool."""
        import asyncio
        return await asyncio.to_thread(self.get_tuple, config)
    
    async def alist(
        self,
        config: dict,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Async version of list - runs sync method in thread pool."""
        import asyncio
        # Note: For generators, we need to consume in thread and return list
        def _list_sync():
            return list(self.list(config, filter=filter, before=before, limit=limit))
        
        results = await asyncio.to_thread(_list_sync)
        for item in results:
            yield item
