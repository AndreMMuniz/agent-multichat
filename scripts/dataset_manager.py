"""
Dataset Manager CLI
Manage dataset items for few-shot learning and evaluation.

Usage:
    # Add new example
    python dataset_manager.py add --input "Quanto custa?" --intent SALES --quality gold
    
    # Add with response
    python dataset_manager.py add --input "Preciso de ajuda" --intent SUPPORT --response "Como posso ajudar?" --quality silver
    
    # List examples
    python dataset_manager.py list
    python dataset_manager.py list --category sales
    python dataset_manager.py list --quality gold
    
    # Promote quality
    python dataset_manager.py promote 5 --quality gold
    
    # Deactivate
    python dataset_manager.py deactivate 5
    
    # Delete
    python dataset_manager.py delete 5
"""

import argparse
import sys
import os

# Add parent directory to path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import DatasetItem
from datetime import datetime

def add_example(args):
    """Add a new dataset example."""
    db = SessionLocal()
    try:
        # Validate intent if provided
        valid_intents = ["SALES", "SUPPORT", "COMPLAINT", "GENERAL"]
        if args.intent and args.intent.upper() not in valid_intents:
            print(f"⚠️  Warning: Intent '{args.intent}' not in standard list: {valid_intents}")
        
        item = DatasetItem(
            user_input=args.input,
            expected_intent=args.intent.upper() if args.intent else None,
            expected_response=args.response,
            category=args.category or (args.intent.lower() if args.intent else "general"),
            quality=args.quality or "silver",
            source=args.source or "manual",
            channel=args.channel,
            notes=args.notes
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        print(f"✅ Added example #{item.id}")
        print(f"   Input: {item.user_input}")
        if item.expected_intent:
            print(f"   Intent: {item.expected_intent}")
        if item.expected_response:
            print(f"   Response: {item.expected_response[:50]}...")
        print(f"   Quality: {item.quality}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def list_examples(args):
    """List dataset examples."""
    db = SessionLocal()
    try:
        query = db.query(DatasetItem)
        
        # Filters
        if args.category:
            query = query.filter(DatasetItem.category == args.category.lower())
        if args.quality:
            query = query.filter(DatasetItem.quality == args.quality.lower())
        if args.active_only:
            query = query.filter(DatasetItem.is_active == True)
        
        items = query.order_by(DatasetItem.created_at.desc()).limit(args.limit).all()
        
        if not items:
            print("No examples found.")
            return
        
        print(f"\n📊 Found {len(items)} examples:\n")
        print("-" * 80)
        
        for item in items:
            status = "✓" if item.is_active else "✗"
            print(f"[{status}] #{item.id} | {item.quality.upper()} | {item.category or 'N/A'}")
            print(f"    Input: {item.user_input[:60]}...")
            if item.expected_intent:
                print(f"    Intent: {item.expected_intent}")
            if item.expected_response:
                print(f"    Response: {item.expected_response[:60]}...")
            print(f"    Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}")
            if item.notes:
                print(f"    Notes: {item.notes}")
            print("-" * 80)
        
    finally:
        db.close()


def promote_example(args):
    """Promote example quality level."""
    db = SessionLocal()
    try:
        item = db.query(DatasetItem).filter(DatasetItem.id == args.id).first()
        
        if not item:
            print(f"❌ Example #{args.id} not found.")
            return
        
        old_quality = item.quality
        item.quality = args.quality.lower()
        item.updated_at = datetime.utcnow()
        
        db.commit()
        
        print(f"✅ Example #{args.id} quality updated: {old_quality} → {args.quality}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def deactivate_example(args):
    """Deactivate an example."""
    db = SessionLocal()
    try:
        item = db.query(DatasetItem).filter(DatasetItem.id == args.id).first()
        
        if not item:
            print(f"❌ Example #{args.id} not found.")
            return
        
        item.is_active = False
        item.updated_at = datetime.utcnow()
        
        db.commit()
        
        print(f"✅ Example #{args.id} deactivated.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def delete_example(args):
    """Delete an example permanently."""
    db = SessionLocal()
    try:
        item = db.query(DatasetItem).filter(DatasetItem.id == args.id).first()
        
        if not item:
            print(f"❌ Example #{args.id} not found.")
            return
        
        if not args.force:
            print(f"⚠️  This will permanently delete example #{args.id}:")
            print(f"   Input: {item.user_input[:60]}...")
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return
        
        db.delete(item)
        db.commit()
        
        print(f"✅ Example #{args.id} deleted permanently.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Dataset Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add new example')
    add_parser.add_argument('--input', '-i', required=True, help='User input text')
    add_parser.add_argument('--intent', help='Expected intent (SALES, SUPPORT, COMPLAINT, GENERAL)')
    add_parser.add_argument('--response', '-r', help='Expected response')
    add_parser.add_argument('--category', '-c', help='Category (defaults to intent)')
    add_parser.add_argument('--quality', '-q', choices=['gold', 'silver', 'bronze'], help='Quality level')
    add_parser.add_argument('--source', '-s', help='Source (manual, production, synthetic)')
    add_parser.add_argument('--channel', help='Channel (whatsapp, email, etc.)')
    add_parser.add_argument('--notes', '-n', help='Additional notes')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List examples')
    list_parser.add_argument('--category', '-c', help='Filter by category')
    list_parser.add_argument('--quality', '-q', help='Filter by quality')
    list_parser.add_argument('--active-only', action='store_true', help='Show only active examples')
    list_parser.add_argument('--limit', '-l', type=int, default=20, help='Max results (default: 20)')
    
    # Promote command
    promote_parser = subparsers.add_parser('promote', help='Change quality level')
    promote_parser.add_argument('id', type=int, help='Example ID')
    promote_parser.add_argument('--quality', '-q', required=True, choices=['gold', 'silver', 'bronze'])
    
    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate example')
    deactivate_parser.add_argument('id', type=int, help='Example ID')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete example permanently')
    delete_parser.add_argument('id', type=int, help='Example ID')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_example(args)
    elif args.command == 'list':
        list_examples(args)
    elif args.command == 'promote':
        promote_example(args)
    elif args.command == 'deactivate':
        deactivate_example(args)
    elif args.command == 'delete':
        delete_example(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
