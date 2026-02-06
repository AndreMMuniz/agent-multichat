"""
Dataset Table Migration Script
Creates the dataset_items table in the database.

Usage:
    python migrate_dataset.py
"""

from database import engine, Base
from models import DatasetItem

def migrate():
    print("Creating dataset_items table...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Table created successfully!")
        print("\nYou can now add examples with:")
        print("  python dataset_manager.py add --input 'example' --intent SALES")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    migrate()
