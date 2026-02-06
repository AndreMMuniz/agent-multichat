"""
Debug script to inspect the database content.
Lists table counts and specifically checks UserContext.
"""
from database import SessionLocal
from models import Conversation, Message, UserContext, UserProfile, PendingAction
from sqlalchemy import text

def inspect_database():
    db = SessionLocal()
    try:
        print("\n=== Database Inspection ===")
        
        # 1. Table Counts
        print("\n[Row Counts]")
        tables = [Conversation, Message, UserContext, UserProfile, PendingAction]
        for table in tables:
            count = db.query(table).count()
            print(f"{table.__name__}: {count}")
            
        # 2. Inspect User Contexts (ALL)
        print("\n[All User Contexts]")
        contexts = db.query(UserContext).all()
        if contexts:
            for ctx in contexts:
                print(f"User: {ctx.user_identifier} | Channel: {ctx.channel} | Len: {len(ctx.context_summary)}")
                print("-" * 30)
        else:
            print("No contexts found in database.")
            
        # 3. Inspect User Profiles
        print("\n[User Profiles]")
        profiles = db.query(UserProfile).all()
        for p in profiles:
            print(f"User: {p.user_identifier} | Name: {p.name} | First Contact: {p.is_first_contact}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_database()
