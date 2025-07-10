#!/usr/bin/env python3
"""
Migration Script for Comprehensive Regulation Data Model

This script migrates existing regulation data to the new comprehensive model structure.
It preserves all existing data while adding default values for new fields.

Usage:
    python migration_script.py

Before running:
    1. Backup your database
    2. Ensure all dependencies are installed
    3. Verify database connectivity

The script will:
    1. Check existing regulation records
    2. Migrate legacy fields to new structure
    3. Add default values for new comprehensive fields
    4. Preserve backward compatibility
"""

import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.application import create_app
    from models import db, Regulation
    from sqlalchemy.exc import SQLAlchemyError
    import logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running this script from the project root directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def backup_reminder():
    """Remind user to backup database before migration"""
    print("\n" + "="*60)
    print("🚨 MIGRATION SCRIPT - BACKUP REMINDER 🚨")
    print("="*60)
    print("Before proceeding, ensure you have:")
    print("1. ✅ Backed up your database")
    print("2. ✅ Tested this script on a copy of your data")
    print("3. ✅ Have rollback plan ready")
    print("="*60)
    
    response = input("Have you backed up your database? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Please backup your database first, then re-run this script.")
        sys.exit(1)
    
    print("✅ Proceeding with migration...\n")


def migrate_property_types(regulation):
    """Migrate legacy property_type to new property_types field"""
    if regulation.property_type and not regulation.property_types:
        # Map legacy values to new structure
        legacy_mapping = {
            'Both': 'Residential,Commercial',
            'Residential': 'Residential',
            'Commercial': 'Commercial',
            'Mixed-use': 'Mixed-use'
        }
        
        regulation.property_types = legacy_mapping.get(
            regulation.property_type, 
            regulation.property_type
        )
        return True
    return False


def migrate_keywords(regulation):
    """Migrate legacy keywords to new related_keywords field"""
    if regulation.keywords and not regulation.related_keywords:
        regulation.related_keywords = regulation.keywords
        return True
    return False


def set_default_values(regulation):
    """Set default values for new comprehensive fields"""
    changes_made = False
    
    # Set default status if not set
    if not regulation.status:
        regulation.status = 'Current & Active'
        changes_made = True
    
    # Set default priority if not set
    if not regulation.priority:
        regulation.priority = 'Medium'
        changes_made = True
    
    # Set default category if it's the old 'Legal' default
    if regulation.category == 'Legal':
        regulation.category = 'General'
        changes_made = True
    
    # Ensure timestamps are set
    current_time = datetime.utcnow()
    if not regulation.created_at:
        regulation.created_at = current_time
        changes_made = True
    
    if not regulation.updated_at:
        regulation.updated_at = current_time
        changes_made = True
    
    # Convert last_updated from Date to DateTime if needed
    if regulation.last_updated and not isinstance(regulation.last_updated, datetime):
        # If it's a date, convert to datetime at midnight
        if hasattr(regulation.last_updated, 'date'):
            regulation.last_updated = datetime.combine(regulation.last_updated.date(), datetime.min.time())
        changes_made = True
    
    return changes_made


def migrate_regulations():
    """Main migration function"""
    logger.info("Starting regulation migration process")
    
    try:
        # Get all regulations
        regulations = Regulation.query.all()
        total_count = len(regulations)
        logger.info(f"Found {total_count} regulations to process")
        
        if total_count == 0:
            logger.info("No regulations found. Migration complete.")
            return True
        
        migrated_count = 0
        error_count = 0
        
        for i, regulation in enumerate(regulations, 1):
            try:
                logger.info(f"Processing regulation {i}/{total_count}: {regulation.title}")
                
                changes_made = False
                
                # Migrate property types
                if migrate_property_types(regulation):
                    logger.info(f"  - Migrated property_type: {regulation.property_type} -> {regulation.property_types}")
                    changes_made = True
                
                # Migrate keywords
                if migrate_keywords(regulation):
                    logger.info(f"  - Migrated keywords to related_keywords")
                    changes_made = True
                
                # Set default values
                if set_default_values(regulation):
                    logger.info(f"  - Set default values for new fields")
                    changes_made = True
                
                if changes_made:
                    migrated_count += 1
                    logger.info(f"  ✅ Migration changes applied")
                else:
                    logger.info(f"  ⏭️  No changes needed")
                
            except Exception as e:
                error_count += 1
                logger.error(f"  ❌ Error processing regulation {regulation.id}: {str(e)}")
                continue
        
        # Commit all changes
        if migrated_count > 0:
            logger.info(f"Committing {migrated_count} regulation changes to database...")
            db.session.commit()
            logger.info("✅ Database changes committed successfully")
        else:
            logger.info("No changes to commit")
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*50)
        logger.info(f"Total regulations processed: {total_count}")
        logger.info(f"Regulations migrated: {migrated_count}")
        logger.info(f"Errors encountered: {error_count}")
        logger.info(f"Success rate: {((total_count - error_count) / total_count * 100):.1f}%")
        logger.info("="*50)
        
        return error_count == 0
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during migration: {str(e)}")
        db.session.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {str(e)}")
        db.session.rollback()
        return False


def verify_migration():
    """Verify the migration was successful"""
    logger.info("Verifying migration results...")
    
    try:
        regulations = Regulation.query.all()
        
        # Check for required fields
        missing_status = [r for r in regulations if not r.status]
        missing_priority = [r for r in regulations if not r.priority]
        missing_category = [r for r in regulations if not r.category]
        
        if missing_status:
            logger.warning(f"Found {len(missing_status)} regulations without status")
        
        if missing_priority:
            logger.warning(f"Found {len(missing_priority)} regulations without priority")
        
        if missing_category:
            logger.warning(f"Found {len(missing_category)} regulations without category")
        
        # Check migration of legacy fields
        migrated_property_types = [r for r in regulations if r.property_types and r.property_type]
        migrated_keywords = [r for r in regulations if r.related_keywords and r.keywords]
        
        logger.info(f"Regulations with migrated property types: {len(migrated_property_types)}")
        logger.info(f"Regulations with migrated keywords: {len(migrated_keywords)}")
        
        # Sample a few regulations for detailed verification
        sample_size = min(3, len(regulations))
        sample_regulations = regulations[:sample_size]
        
        logger.info("\nSample regulation verification:")
        for reg in sample_regulations:
            logger.info(f"  ID {reg.id}: {reg.title}")
            logger.info(f"    Status: {reg.status}")
            logger.info(f"    Priority: {reg.priority}")
            logger.info(f"    Category: {reg.category}")
            logger.info(f"    Property Types: {reg.property_types}")
            logger.info(f"    Related Keywords: {reg.related_keywords}")
        
        logger.info("✅ Migration verification complete")
        return True
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return False


def main():
    """Main migration execution"""
    print("🔄 Regulation Model Migration Script")
    print("="*40)
    
    # Backup reminder
    backup_reminder()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        logger.info("Migration script started")
        
        # Run migration
        success = migrate_regulations()
        
        if success:
            logger.info("✅ Migration completed successfully")
            
            # Verify migration
            verify_migration()
            
            print("\n🎉 Migration completed successfully!")
            print("📋 Check migration.log for detailed information")
            print("🔍 Verify your data in the admin interface")
            
        else:
            logger.error("❌ Migration failed")
            print("\n💥 Migration failed!")
            print("📋 Check migration.log for error details")
            print("🔄 Database changes have been rolled back")
            sys.exit(1)


if __name__ == '__main__':
    main() 