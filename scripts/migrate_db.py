# Database Migration Script
# Run this to add the 'channel' column to the messages table

from database import engine, Base
from sqlalchemy import text

def migrate():
    """Add channel column to messages table for omnichannel tracking."""
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='messages' AND column_name='channel'
            """))
            
            if result.fetchone() is None:
                print("Adding 'channel' column to messages table...")
                conn.execute(text("""
                    ALTER TABLE messages 
                    ADD COLUMN channel VARCHAR
                """))
                conn.commit()
                print("✓ Migration completed successfully!")
            else:
                print("✓ Column 'channel' already exists. No migration needed.")
                
        except Exception as e:
            print(f"Migration failed: {e}")
            print("\nAlternative: Drop and recreate tables (WARNING: loses all data)")
            print("Run in Python console:")
            print("  from database import Base, engine")
            print("  Base.metadata.drop_all(bind=engine)")
            print("  Base.metadata.create_all(bind=engine)")

if __name__ == "__main__":
    migrate()
