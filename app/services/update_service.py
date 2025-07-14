"""
Update Service

Handles all update-related business logic:
- Update CRUD operations
- Update statistics and dashboard data
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from models import db, Update
import logging
from datetime import datetime


class UpdateService:
    """Service class for handling update operations"""
    
    @staticmethod
    def get_update_by_id(update_id):
        """
        Get an update by ID
        
        Args:
            update_id (int): The update ID
            
        Returns:
            Update: The update object or None if not found
        """
        try:
            from models import db
            return db.session.get(Update, update_id)
        except Exception as e:
            logging.error(f"Error getting update by ID {update_id}: {str(e)}")
            return None
    
    @staticmethod
    def create_update(update_data):
        """
        Create a new update with all fields including new ones
        
        Args:
            update_data (dict): Dictionary containing update data
            
        Returns:
            tuple: (success: bool, update: Update or None, error: str or None)
        """
        try:
            logging.info("=== UPDATE SERVICE: CREATE UPDATE STARTED ===")
            logging.info(f"Received update_data with {len(update_data)} fields")
            
            # Helper function to safely parse dates
            def parse_date(date_str):
                if not date_str:
                    return None
                try:
                    if isinstance(date_str, str):
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                    return date_str  # Already a date object
                except (ValueError, TypeError):
                    return None
            
            logging.info("=== UPDATE SERVICE: PARSING DATES ===")
            
            # Parse dates with logging
            parsed_dates = {}
            date_fields = ['update_date', 'effective_date', 'deadline_date', 'compliance_deadline', 'expected_decision_date']
            for field in date_fields:
                try:
                    original_value = update_data.get(field)
                    parsed_value = parse_date(original_value)
                    parsed_dates[field] = parsed_value
                    logging.info(f"Date field '{field}': '{original_value}' -> '{parsed_value}'")
                except Exception as e:
                    logging.error(f"Error parsing date field '{field}': {str(e)}")
                    parsed_dates[field] = None
            
            # Set default update_date if not provided
            if parsed_dates['update_date'] is None:
                parsed_dates['update_date'] = datetime.now().date()
                logging.info(f"Setting default update_date: {parsed_dates['update_date']}")
            
            logging.info("=== UPDATE SERVICE: PREPARING UPDATE OBJECT ===")
            
            # Create new update with all fields including new template fields
            new_update = Update(
                title=update_data.get('title', ''),
                description=update_data.get('description', ''),
                jurisdiction_affected=update_data.get('jurisdiction_affected', ''),
                jurisdiction_level=update_data.get('jurisdiction_level', ''),
                update_date=parsed_dates['update_date'],
                effective_date=parsed_dates['effective_date'],
                status=update_data.get('status', 'Recent'),
                category=update_data.get('category', 'General'),
                impact_level=update_data.get('impact_level', 'Medium'),
                action_required=update_data.get('action_required', False),
                action_description=update_data.get('action_description', ''),
                priority=int(update_data.get('priority', 2)),
                change_type=update_data.get('change_type', 'Recent'),
                decision_status=update_data.get('decision_status', ''),
                potential_impact=update_data.get('potential_impact', ''),
                affected_operators=update_data.get('affected_operators', ''),
                deadline_date=parsed_dates['deadline_date'],
                compliance_deadline=parsed_dates['compliance_deadline'],
                expected_decision_date=parsed_dates['expected_decision_date'],
                property_types=update_data.get('property_types', ''),
                tags=update_data.get('tags', ''),
                source_url=update_data.get('source_url', ''),
                related_regulation_ids=update_data.get('related_regulation_ids', ''),
                # New template fields
                summary=update_data.get('summary', ''),
                full_text=update_data.get('full_text', ''),
                compliance_requirements=update_data.get('compliance_requirements', ''),
                implementation_timeline=update_data.get('implementation_timeline', ''),
                official_sources=update_data.get('official_sources', ''),
                expert_analysis=update_data.get('expert_analysis', ''),
                kaystreet_commitment=update_data.get('kaystreet_commitment', '')
            )
            
            logging.info("=== UPDATE SERVICE: VALIDATING UPDATE OBJECT ===")
            
            # Log the created object fields
            for field in ['title', 'description', 'jurisdiction_affected', 'jurisdiction_level', 'status', 'category', 'impact_level']:
                value = getattr(new_update, field)
                logging.info(f"Update object field '{field}': '{value}' (type: {type(value)})")
            
            # Check for required fields
            required_fields = ['title', 'description', 'jurisdiction_affected', 'update_date', 'status', 'category', 'impact_level']
            for field in required_fields:
                value = getattr(new_update, field)
                if not value:
                    logging.error(f"Required field '{field}' is empty or None")
                    return False, None, f"Required field '{field}' is missing"
            
            logging.info("=== UPDATE SERVICE: ADDING TO DATABASE SESSION ===")
            db.session.add(new_update)
            
            logging.info("=== UPDATE SERVICE: COMMITTING TO DATABASE ===")
            db.session.commit()
            
            logging.info(f"=== UPDATE SERVICE: SUCCESS - Created new update: {new_update.id} ===")
            return True, new_update, None
            
        except Exception as e:
            logging.error(f"=== UPDATE SERVICE: ERROR - {str(e)} ===")
            logging.error(f"Exception type: {type(e)}")
            logging.error(f"Exception details:", exc_info=True)
            db.session.rollback()
            return False, None, str(e)
    
    @staticmethod
    def update_update(update_id, update_data):
        """
        Update an existing update
        
        Args:
            update_id (int): The update ID
            update_data (dict): Dictionary containing update data
            
        Returns:
            tuple: (success: bool, update: Update or None, error: str or None)
        """
        try:
            from models import db
            update = db.session.get(Update, update_id)
            if not update:
                return False, None, "Update not found"
            
            # Helper function to safely handle dates
            def safe_parse_date(date_value):
                if not date_value:
                    return None
                # If it's already a date object, return it as-is
                if hasattr(date_value, 'year') and hasattr(date_value, 'month'):
                    return date_value
                # If it's a string, try to parse it
                if isinstance(date_value, str):
                    try:
                        return datetime.strptime(date_value, '%Y-%m-%d').date()
                    except ValueError:
                        return None
                return None

            # Update all fields
            for key, value in update_data.items():
                if hasattr(update, key):
                    # Handle date fields
                    if key in ['update_date', 'effective_date', 'deadline_date', 'compliance_deadline', 'expected_decision_date']:
                        setattr(update, key, safe_parse_date(value))
                    else:
                        setattr(update, key, value)
            
            db.session.commit()
            
            logging.info(f"Updated update: {update_id}")
            return True, update, None
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating update {update_id}: {str(e)}")
            return False, None, str(e)
    
    @staticmethod
    def delete_update(update_id):
        """
        Delete an update
        
        Args:
            update_id (int): The update ID
            
        Returns:
            tuple: (success: bool, error: str or None)
        """
        try:
            from models import db
            update = db.session.get(Update, update_id)
            if not update:
                return False, "Update not found"
            
            db.session.delete(update)
            db.session.commit()
            
            logging.info(f"Deleted update: {update_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting update {update_id}: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def get_admin_statistics():
        """
        Get administrative statistics for updates
        
        Returns:
            dict: Dictionary containing statistics
        """
        try:
            total_updates = Update.query.count()
            recent_updates = Update.query.filter(Update.status == 'Recent').count()
            upcoming_updates = Update.query.filter(Update.status == 'Upcoming').count()
            proposed_updates = Update.query.filter(Update.status == 'Proposed').count()
            high_priority = Update.query.filter(Update.priority == 1).count()
            
            return {
                'total_updates': total_updates,
                'recent_updates': recent_updates,
                'upcoming_updates': upcoming_updates,
                'proposed_updates': proposed_updates,
                'high_priority': high_priority
            }
            
        except Exception as e:
            logging.error(f"Error getting admin statistics: {str(e)}")
            return {
                'total_updates': 0,
                'recent_updates': 0,
                'upcoming_updates': 0,
                'proposed_updates': 0,
                'high_priority': 0
            }
    
    @staticmethod
    def get_all_updates(order_by='created_at'):
        """
        Get all updates with optional ordering
        
        Args:
            order_by (str): Field to order by
            
        Returns:
            list: List of Update objects
        """
        try:
            if order_by == 'priority':
                return Update.query.order_by(Update.priority.asc(), Update.update_date.desc()).all()
            elif order_by == 'date':
                return Update.query.order_by(Update.update_date.desc()).all()
            else:
                return Update.query.order_by(Update.update_date.desc()).all()
            
        except Exception as e:
            logging.error(f"Error getting all updates: {str(e)}")
            return []
    
    @staticmethod
    def get_recent_upcoming_updates(filters=None):
        """
        Get recent and upcoming updates
        
        Args:
            filters (dict): Optional filters (kept for compatibility but not used)
            
        Returns:
            list: List of recent and upcoming Update objects
        """
        try:
            return Update.query.filter(
                Update.status.in_(['Recent', 'Upcoming'])
            ).order_by(Update.priority.asc(), Update.update_date.desc()).all()
            
        except Exception as e:
            logging.error(f"Error getting recent/upcoming updates: {str(e)}")
            return []
    
    @staticmethod
    def get_proposed_updates(filters=None):
        """
        Get proposed updates
        
        Args:
            filters (dict): Optional filters (kept for compatibility but not used)
            
        Returns:
            list: List of proposed Update objects
        """
        try:
            return Update.query.filter(
                Update.status == 'Proposed'
            ).order_by(Update.priority.asc(), Update.update_date.desc()).all()
            
        except Exception as e:
            logging.error(f"Error getting proposed updates: {str(e)}")
            return [] 