"""
Regulation Service

Handles all regulation-related business logic:
- Regulation CRUD operations
- Detail content generation
- Related regulation finding
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from models import db, Regulation, get_location_options_by_jurisdiction
import logging


class RegulationService:
    """
    Service class for handling regulation operations.
    
    This service provides comprehensive regulation management functionality including:
    - CRUD operations with validation and error handling
    - Content formatting and presentation
    - Related content discovery and recommendations
    """
    
    @staticmethod
    def get_location_options_by_jurisdiction_level(jurisdiction_level: str) -> List[str]:
        """
        Get location options based on jurisdiction level.
        
        Args:
            jurisdiction_level: 'National', 'State', or 'Local'
            
        Returns:
            List of location options appropriate for the jurisdiction level
        """
        return get_location_options_by_jurisdiction(jurisdiction_level)
    
    @staticmethod
    def get_regulation_by_id(regulation_id: int) -> Optional[Regulation]:
        """
        Retrieve a single regulation by its unique identifier.
        
        Args:
            regulation_id: Unique identifier of the regulation to retrieve.
            
        Returns:
            Regulation object if found, None if not found or on error.
            
        Raises:
            Exception: Logged internally if database query fails.
        """
        try:
            return Regulation.query.get_or_404(regulation_id)
        except Exception as e:
            logging.error(f"Error getting regulation by ID {regulation_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_related_regulations(regulation: Regulation) -> List[Regulation]:
        """
        Find regulations related to the given regulation.
        
        Finds related regulations based on jurisdiction and location matching.
        
        Args:
            regulation: The regulation to find related items for.
            
        Returns:
            List of related Regulation objects (excluding the input regulation).
            Limited to 5 results for display optimization.
            
        Note:
            Returns empty list if no related regulations found or on error.
        """
        try:
            return Regulation.query.filter(
                Regulation.id != regulation.id,
                db.or_(
                    Regulation.jurisdiction.ilike(f'%{regulation.jurisdiction}%'),
                    Regulation.location.ilike(f'%{regulation.location}%')
                )
            ).limit(5).all()
            
        except Exception as e:
            logging.error(f"Error finding related regulations: {str(e)}")
            return []
    
    @staticmethod
    def get_regulation_detailed_content(regulation: Regulation) -> List[Dict[str, str]]:
        """
        Generate structured content sections for regulation detail display.
        
        Transforms regulation data into formatted HTML sections suitable for
        web display. Creates organized sections for overview, requirements, compliance
        steps, forms, penalties, and recent changes with appropriate styling classes.
        
        Args:
            regulation: The regulation object to format for display.
            
        Returns:
            List of content section dictionaries, each containing:
                - title (str): Section heading for display
                - content (str): HTML-formatted section content
                - type (str): Section type for CSS styling
                
        Note:
            Generates responsive HTML with Bootstrap classes.
            Returns empty list if content generation fails.
        """
        try:
            content_sections = []
            
            # Overview section
            if regulation.overview:
                content_sections.append({
                    'title': 'Overview',
                    'content': f'<p class="regulation-overview">{regulation.overview}</p>',
                    'type': 'overview'
                })
            
            # Key Requirements section
            if regulation.key_requirements:
                content_sections.append({
                    'title': 'Key Requirements',
                    'content': f'<div class="regulation-requirements">{regulation.key_requirements}</div>',
                    'type': 'requirements'
                })
            
            # Compliance Steps section
            if regulation.compliance_steps:
                content_sections.append({
                    'title': 'Compliance Steps',
                    'content': f'<div class="regulation-compliance">{regulation.compliance_steps}</div>',
                    'type': 'compliance'
                })
            
            # Forms and Documents section
            if regulation.forms_documents:
                content_sections.append({
                    'title': 'Forms and Documents',
                    'content': f'<div class="regulation-forms">{regulation.forms_documents}</div>',
                    'type': 'forms'
                })
            
            # Penalties section
            if regulation.penalties:
                content_sections.append({
                    'title': 'Penalties',
                    'content': f'<div class="regulation-penalties">{regulation.penalties}</div>',
                    'type': 'penalties'
                })
            
            # Recent Changes section
            if regulation.recent_changes:
                content_sections.append({
                    'title': 'Recent Changes',
                    'content': f'<div class="regulation-changes">{regulation.recent_changes}</div>',
                    'type': 'changes'
                })
            
            return content_sections
            
        except Exception as e:
            logging.error(f"Error generating regulation content: {str(e)}")
            return []
    
    @staticmethod
    def create_regulation(regulation_data: Dict[str, Any]) -> Tuple[bool, Optional[Regulation], Optional[str]]:
        """
        Create a new regulation record in the database.
        
        Validates and persists a new regulation with comprehensive data handling
        and error recovery. Supports all regulation fields with proper type handling.
        
        Args:
            regulation_data: Dictionary containing regulation field data:
                - jurisdiction_level (str): National, State, or Local
                - location (str): Geographic location/jurisdiction name
                - title (str): Regulation title/name
                - key_requirements (str): Main compliance requirements
                - compliance_level (str): Mandatory, Recommended, Optional
                - property_types (str): Comma-separated property types
                - status (str): Current & Active, Upcoming, Expired
                - category (str): Regulation category (Zoning, Registration, etc.)
                - priority (str): High, Medium, Low
                - related_keywords (str): Comma-separated keywords
                - compliance_checklist (str): Actionable items for compliance
                - local_authority_contact (str): Contact information
                - effective_date (datetime, optional): When regulation takes effect
                - expiry_date (datetime, optional): When regulation expires
                - Legacy fields for backward compatibility
                
        Returns:
            Tuple containing:
                - success (bool): Whether creation succeeded
                - regulation (Regulation or None): Created object if successful
                - error (str or None): Error message if creation failed
                
        Note:
            Automatically rolls back database transaction on failure.
        """
        try:
            from datetime import datetime
            
            regulation = Regulation(
                # Core Information
                jurisdiction=regulation_data.get('jurisdiction'),
                jurisdiction_level=regulation_data.get('jurisdiction_level', 'Local'),
                location=regulation_data.get('location'),
                title=regulation_data.get('title'),
                last_updated=regulation_data.get('last_updated', datetime.utcnow()),
                
                # Rich Text Content Fields
                overview=regulation_data.get('overview'),
                detailed_requirements=regulation_data.get('detailed_requirements'),
                compliance_steps=regulation_data.get('compliance_steps'),
                required_forms=regulation_data.get('required_forms'),
                penalties_non_compliance=regulation_data.get('penalties_non_compliance'),
                recent_changes=regulation_data.get('recent_changes'),
                
                # Timestamps
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(regulation)
            db.session.commit()
            
            return True, regulation, None
            
        except Exception as e:
            logging.error(f"Error creating regulation: {str(e)}")
            db.session.rollback()
            return False, None, str(e)
    
    @staticmethod
    def update_regulation(regulation_id: int, regulation_data: Dict[str, Any]) -> Tuple[bool, Optional[Regulation], Optional[str]]:
        """
        Update an existing regulation with new data.
        
        Performs partial or complete updates to regulation records with
        automatic field validation and transaction safety.
        
        Args:
            regulation_id: Unique identifier of the regulation to update.
            regulation_data: Dictionary containing field updates (only changed fields needed).
                Supports all regulation fields as defined in create_regulation.
                
        Returns:
            Tuple containing:
                - success (bool): Whether update succeeded
                - regulation (Regulation or None): Updated object if successful
                - error (str or None): Error message if update failed
                
        Note:
            Only updates fields present in regulation_data dictionary.
            Automatically updates the updated_at timestamp.
            Automatically rolls back database transaction on failure.
        """
        try:
            from datetime import datetime
            
            regulation = Regulation.query.get_or_404(regulation_id)
            
            # Update fields
            for field, value in regulation_data.items():
                if hasattr(regulation, field):
                    setattr(regulation, field, value)
            
            # Always update the updated_at timestamp
            regulation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return True, regulation, None
            
        except Exception as e:
            logging.error(f"Error updating regulation: {str(e)}")
            db.session.rollback()
            return False, None, str(e)
    
    @staticmethod
    def delete_regulation(regulation_id: int) -> Tuple[bool, Optional[str]]:
        """
        Permanently delete a regulation from the database.
        
        Removes the regulation record and handles transaction rollback on failure.
        This operation is irreversible.
        
        Args:
            regulation_id: Unique identifier of the regulation to delete.
            
        Returns:
            Tuple containing:
                - success (bool): Whether deletion succeeded
                - error (str or None): Error message if deletion failed, None on success
                
        Warning:
            This permanently removes the regulation. Consider archiving instead
            for data integrity in production systems.
            
        Note:
            Automatically rolls back database transaction on failure.
        """
        try:
            regulation = Regulation.query.get_or_404(regulation_id)
            db.session.delete(regulation)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            logging.error(f"Error deleting regulation: {str(e)}")
            db.session.rollback()
            return False, str(e)
    


    @staticmethod
    def get_admin_statistics() -> Dict[str, Any]:
        """
        Get comprehensive statistics for admin dashboard.
        
        Returns various metrics and counts for regulation management,
        including totals, recent activity, and breakdowns by jurisdiction and location.
        
        Returns:
            Dictionary containing:
                - total: Total number of regulations
                - recent: Recently updated regulations count
                - by_jurisdiction: Count by jurisdiction
                - by_location: Count by location
                
        Note:
            Returns safe defaults if database query fails.
        """
        try:
            from models import Regulation
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            # Basic counts
            total_regulations = Regulation.query.count()
            
            # Recent regulations (updated in last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_count = Regulation.query.filter(
                Regulation.last_updated >= thirty_days_ago
            ).count()
            
            # Jurisdiction breakdown
            jurisdiction_stats = db.session.query(
                Regulation.jurisdiction,
                func.count(Regulation.id).label('count')
            ).group_by(Regulation.jurisdiction).all()
            
            by_jurisdiction = {stat.jurisdiction or 'Unspecified': stat.count for stat in jurisdiction_stats}
            
            # Location breakdown (top 10)
            location_stats = db.session.query(
                Regulation.location,
                func.count(Regulation.id).label('count')
            ).group_by(Regulation.location).order_by(func.count(Regulation.id).desc()).limit(10).all()
            
            by_location = {stat.location or 'Unspecified': stat.count for stat in location_stats}
            
            return {
                'total': total_regulations,
                'recent': recent_count,
                'by_jurisdiction': by_jurisdiction,
                'by_location': by_location,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting regulation admin statistics: {str(e)}")
            return {
                'total': 0,
                'recent': 0,
                'by_jurisdiction': {},
                'by_location': {},
                'last_updated': datetime.now().isoformat()
            } 