"""
Debug script to inspect UserContexts ONLY.
"""
from database import SessionLocal
from models import UserContext

def inspect_contexts():
    db = SessionLocal()
    try:
        print("Start Inspection")
        contexts = db.query(UserContext).all()
        print(f"Found {len(contexts)} contexts.")
        for ctx in contexts:
            print(f"User: {ctx.user_identifier}")
            print(f"Channel: {ctx.channel}")
            print(f"Summary: {ctx.context_summary}")
            print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_contexts()
