"""
Update Service

Handles all update-related business logic:
- Update CRUD operations
- Update filtering and searching
- Update statistics and dashboard data
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from models import db, Update
import logging


class UpdateService:
    """Service class for handling update operations"""
    
    @staticmethod
    def get_filtered_updates(filters):
        """
        Get updates with applied filters
        
        Args:
            filters (dict): Dictionary containing filter criteria
                - status: status filter
                - jurisdiction: jurisdiction filter
                - category: category filter
                - impact: impact level filter
                - search: text search query
        
        Returns:
            list: List of filtered Update objects
        """
        try:
            query = Update.query
            
            if filters.get('status'):
                query = query.filter(Update.status == filters['status'])
            
            if filters.get('jurisdiction'):
                query = query.filter(Update.jurisdiction_affected.ilike(f'%{filters["jurisdiction"]}%'))
            
            if filters.get('category'):
                query = query.filter(Update.category == filters['category'])
            
            if filters.get('impact'):
                query = query.filter(Update.impact_level == filters['impact'])
            
            if filters.get('search'):
                search_terms = f'%{filters["search"]}%'
                query = query.filter(
                    db.or_(
                        Update.title.ilike(search_terms),
                        Update.description.ilike(search_terms),
                        Update.tags.ilike(search_terms),
                        Update.jurisdiction_affected.ilike(search_terms)
                    )
                )
            
            # Order by priority (1=high, 2=medium, 3=low) then by date
            return query.order_by(Update.priority.asc(), Update.update_date.desc()).all()
            
        except Exception as e:
            logging.error(f"Error filtering updates: {str(e)}")
            return []
    
    @staticmethod
    def get_filter_options():
        """
        Get available filter options for updates
        
        Returns:
            dict: Dictionary containing filter options
        """
        try:
            # Get distinct jurisdictions from updates
            jurisdictions_query = Update.query.distinct(Update.jurisdiction_affected).all()
            jurisdictions = [u.jurisdiction_affected for u in jurisdictions_query if u.jurisdiction_affected]
            
            return {
                'statuses': ['Recent', 'Upcoming', 'Proposed'],
                'jurisdictions': list(set(jurisdictions)),  # Remove duplicates
                'categories': ['Regulatory Changes', 'Tax Updates', 'Licensing Changes', 'Court Decisions', 'Industry News'],
                'impact_levels': ['High', 'Medium', 'Low']
            }
            
        except Exception as e:
            logging.error(f"Error getting update filter options: {str(e)}")
            return {
                'statuses': ['Recent', 'Upcoming', 'Proposed'],
                'jurisdictions': [],
                'categories': ['Regulatory Changes', 'Tax Updates', 'Licensing Changes', 'Court Decisions', 'Industry News'],
                'impact_levels': ['High', 'Medium', 'Low']
            }
    
    @staticmethod
    def search_updates(search_params):
        """
        Perform advanced search within updates
        
        Args:
            search_params (dict): Dictionary containing search parameters
                - query_text: text search
                - category: category filter
                - impact: impact level filter
                - status: status filter
                - jurisdiction: jurisdiction filter
                - has_deadline: deadline filter
                - action_required: action required filter
        
        Returns:
            list: List of Update objects matching criteria
        """
        try:
            query = Update.query
            
            if search_params.get('query_text'):
                search_terms = f'%{search_params["query_text"]}%'
                query = query.filter(
                    db.or_(
                        Update.title.ilike(search_terms),
                        Update.description.ilike(search_terms),
                        Update.tags.ilike(search_terms),
                        Update.action_description.ilike(search_terms)
                    )
                )
            
            if search_params.get('category'):
                query = query.filter(Update.category == search_params['category'])
            
            if search_params.get('impact'):
                query = query.filter(Update.impact_level == search_params['impact'])
            
            if search_params.get('status'):
                query = query.filter(Update.status == search_params['status'])
            
            if search_params.get('jurisdiction'):
                query = query.filter(Update.jurisdiction_affected.ilike(f'%{search_params["jurisdiction"]}%'))
            
            has_deadline = search_params.get('has_deadline')
            if has_deadline == 'true':
                query = query.filter(Update.deadline_date.isnot(None))
            elif has_deadline == 'false':
                query = query.filter(Update.deadline_date.is_(None))
            
            action_required = search_params.get('action_required')
            if action_required == 'true':
                query = query.filter(Update.action_required == True)
            elif action_required == 'false':
                query = query.filter(Update.action_required == False)
            
            return query.order_by(Update.priority.asc(), Update.update_date.desc()).limit(50).all()
            
        except Exception as e:
            logging.error(f"Error searching updates: {str(e)}")
            return []
    
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
            return Update.query.get_or_404(update_id)
        except Exception as e:
            logging.error(f"Error getting update by ID {update_id}: {str(e)}")
            return None
    
    @staticmethod
    def create_update(update_data):
        """
        Create a new update
        
        Args:
            update_data (dict): Dictionary containing update data
            
        Returns:
            tuple: (success: bool, update: Update or None, error: str or None)
        """
        try:
            update = Update(
                title=update_data.get('title'),
                description=update_data.get('description'),
                jurisdiction_affected=update_data.get('jurisdiction_affected'),
                update_date=update_data.get('update_date'),
                status=update_data.get('status'),
                category=update_data.get('category'),
                impact_level=update_data.get('impact_level'),
                effective_date=update_data.get('effective_date'),
                deadline_date=update_data.get('deadline_date'),
                action_required=update_data.get('action_required', False),
                action_description=update_data.get('action_description'),
                property_types=update_data.get('property_types'),
                related_regulation_ids=update_data.get('related_regulation_ids'),
                tags=update_data.get('tags'),
                source_url=update_data.get('source_url'),
                priority=int(update_data.get('priority', 3))  # Default to low priority
            )
            
            db.session.add(update)
            db.session.commit()
            
            return True, update, None
            
        except Exception as e:
            logging.error(f"Error creating update: {str(e)}")
            db.session.rollback()
            return False, None, str(e)
    
    @staticmethod
    def update_update(update_id, update_data):
        """
        Update an existing update
        
        Args:
            update_id (int): ID of the update to update
            update_data (dict): Dictionary containing updated update data
            
        Returns:
            tuple: (success: bool, update: Update or None, error: str or None)
        """
        try:
            update = Update.query.get_or_404(update_id)
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(update, field):
                    if field == 'priority':
                        setattr(update, field, int(value))
                    else:
                        setattr(update, field, value)
            
            db.session.commit()
            
            return True, update, None
            
        except Exception as e:
            logging.error(f"Error updating update: {str(e)}")
            db.session.rollback()
            return False, None, str(e)
    
    @staticmethod
    def delete_update(update_id):
        """
        Delete an update
        
        Args:
            update_id (int): ID of the update to delete
            
        Returns:
            tuple: (success: bool, error: str or None)
        """
        try:
            update = Update.query.get_or_404(update_id)
            db.session.delete(update)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            logging.error(f"Error deleting update: {str(e)}")
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_admin_statistics():
        """
        Get statistics for admin dashboard
        
        Returns:
            dict: Dictionary containing update statistics matching expected interface
        """
        try:
            from datetime import datetime, timedelta
            
            total_updates = Update.query.count()
            
            # Recent updates (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_updates = Update.query.filter(
                Update.update_date >= thirty_days_ago
            ).count()
            
            # Upcoming updates (future effective dates)
            upcoming_updates = Update.query.filter(
                Update.effective_date > datetime.now()
            ).count()
            
            # Proposed updates
            proposed_updates = Update.query.filter(Update.status == 'Proposed').count()
            
            return {
                'total': total_updates,
                'recent': recent_updates,
                'upcoming': upcoming_updates,
                'proposed': proposed_updates,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting admin statistics: {str(e)}")
            return {
                'total': 0,
                'recent': 0,
                'upcoming': 0,
                'proposed': 0,
                'last_updated': datetime.now().isoformat()
            }
    
    @staticmethod
    def get_all_updates(order_by='created_at'):
        """
        Get all updates for admin management
        
        Args:
            order_by (str): Field to order by (default: 'created_at')
            
        Returns:
            list: List of all Update objects
        """
        try:
            if order_by == 'created_at' and hasattr(Update, 'created_at'):
                return Update.query.order_by(Update.created_at.desc()).all()
            else:
                return Update.query.order_by(Update.update_date.desc()).all()
                
        except Exception as e:
            logging.error(f"Error getting all updates: {str(e)}")
            return [] 