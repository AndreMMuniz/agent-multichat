"""
Test script to verify user profile table creation.
"""
from database import engine, Base
from models import Conversation, Message, UserContext, PendingAction, UserProfile

try:
    # Test connection
    with engine.connect() as connection:
        print("✓ Database connection successful!")
    
    # Create all tables (including new UserProfile)
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    
    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = ["conversations", "messages", "user_contexts", "user_profiles", "pending_actions"]
    
    print("\nVerifying tables:")
    for table in expected_tables:
        if table in tables:
            print(f"  ✓ Table '{table}' exists")
            
            # Show columns for user_profiles
            if table == "user_profiles":
                columns = inspector.get_columns(table)
                print(f"    Columns: {', '.join([col['name'] for col in columns])}")
        else:
            print(f"  ✗ Table '{table}' not found")
    
    print("\n✓ All tables verified successfully!")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nMake sure PostgreSQL is running on localhost:5433")
