"""
Test script to verify database connection and table creation.
Run this before starting the FastAPI server.
"""
from database import engine, Base
from models import AnalysisModel

try:
    # Test connection
    with engine.connect() as connection:
        print("✓ Database connection successful!")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    
    # Verify table exists
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if "analysis_results" in tables:
        print(f"✓ Table 'analysis_results' exists")
        
        # Show columns
        columns = inspector.get_columns("analysis_results")
        print("\nTable schema:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    else:
        print("✗ Table 'analysis_results' not found")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nMake sure PostgreSQL is running on localhost:5433")
    print("Connection string: postgresql://log_user:password123@localhost:5433/log_analyzer_db")
