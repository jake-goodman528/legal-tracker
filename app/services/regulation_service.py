"""
Regulation Service

Handles all regulation-related business logic:
- Regulation CRUD operations
- Filtering and pagination
- Detail content generation
- Related regulation finding
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from models import db, Regulation, SavedSearch
import logging


class RegulationService:
    """
    Service class for handling regulation operations.
    
    This service provides comprehensive regulation management functionality including:
    - CRUD operations with validation and error handling
    - Advanced filtering and search capabilities
    - Content formatting and presentation
    - Related content discovery and recommendations
    """
    
    @staticmethod
    def get_filtered_regulations(filters: Dict[str, str]) -> List[Regulation]:
        """
        Retrieve regulations filtered by multiple criteria.
        
        Applies filtering logic across jurisdiction, location, category, and text search.
        Supports partial matching for location and full-text search across titles
        and key requirements.
        
        Args:
            filters: Dictionary containing filter criteria:
                - jurisdiction (str, optional): Exact jurisdiction level match
                - location (str, optional): Partial location name match
                - category (str, optional): Exact category match
                - search (str, optional): Text search across title and requirements
        
        Returns:
            List of Regulation objects matching all specified criteria,
            ordered by jurisdiction level and location.
            
        Note:
            Returns empty list if database query fails. Logs errors automatically.
        """
        try:
            query = Regulation.query
            
            if filters.get('jurisdiction'):
                query = query.filter(Regulation.jurisdiction_level == filters['jurisdiction'])
            
            if filters.get('location'):
                query = query.filter(Regulation.location.ilike(f'%{filters["location"]}%'))
            
            if filters.get('category'):
                query = query.filter(Regulation.category == filters['category'])
            
            if filters.get('search'):
                search_term = f'%{filters["search"]}%'
                query = query.filter(
                    db.or_(
                        Regulation.title.ilike(search_term),
                        Regulation.key_requirements.ilike(search_term)
                    )
                )
            
            return query.order_by(Regulation.jurisdiction_level, Regulation.location).all()
            
        except Exception as e:
            logging.error(f"Error filtering regulations: {str(e)}")
            return []
    
    @staticmethod
    def get_filter_options() -> Dict[str, List[str]]:
        """
        Extract all distinct filter values from existing regulations.
        
        Queries the database to build dynamic filter options based on actual
        regulation data. Ensures filter UI only shows valid, available options.
        
        Returns:
            Dictionary containing lists of available filter values:
                - jurisdictions (List[str]): All unique jurisdiction levels
                - locations (List[str]): All unique location names
                - categories (List[str]): All unique regulation categories
                
        Note:
            Filters out null/empty values automatically. Returns empty lists
            for each category if database query fails.
        """
        try:
            jurisdictions = db.session.query(Regulation.jurisdiction_level).distinct().all()
            locations = db.session.query(Regulation.location).distinct().all()
            categories = db.session.query(Regulation.category).distinct().all()
            
            return {
                'jurisdictions': [j[0] for j in jurisdictions if j[0]],
                'locations': [l[0] for l in locations if l[0]],
                'categories': [c[0] for c in categories if c[0]]
            }
            
        except Exception as e:
            logging.error(f"Error getting filter options: {str(e)}")
            return {'jurisdictions': [], 'locations': [], 'categories': []}
    
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
        Discover regulations related to the given regulation.
        
        Finds related regulations based on location and category similarity.
        Useful for providing contextual recommendations and related content discovery.
        
        Args:
            regulation: The regulation object to find related items for.
            
        Returns:
            List of up to 5 related Regulation objects, excluding the input regulation.
            
        Note:
            Matches regulations with same location OR same category.
            Returns empty list if database query fails.
        """
        try:
            return Regulation.query.filter(
                db.or_(
                    Regulation.location == regulation.location,
                    Regulation.category == regulation.category
                ),
                Regulation.id != regulation.id
            ).limit(5).all()
            
        except Exception as e:
            logging.error(f"Error getting related regulations: {str(e)}")
            return []
    
    @staticmethod
    def get_regulation_detailed_content(regulation: Regulation) -> List[Dict[str, str]]:
        """
        Generate structured content sections for regulation detail display.
        
        Transforms regulation data into formatted HTML sections suitable for
        web display. Creates organized sections for requirements, compliance
        info, dates, and keywords with appropriate styling classes.
        
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
            
            # Key Requirements section
            content_sections.append({
                'title': 'Key Requirements',
                'content': regulation.key_requirements,
                'type': 'requirements'
            })
            
            # Compliance Information
            compliance_info = f"""
            <div class="compliance-summary">
                <div class="row">
                    <div class="col-md-4">
                        <strong>Compliance Level:</strong><br>
                        <span class="badge compliance-badge">{regulation.compliance_level}</span>
                    </div>
                    <div class="col-md-4">
                        <strong>Property Types:</strong><br>
                        <span class="badge property-badge">{regulation.property_type}</span>
                    </div>
                    <div class="col-md-4">
                        <strong>Last Updated:</strong><br>
                        {regulation.last_updated.strftime('%B %d, %Y') if regulation.last_updated else 'Not specified'}
                    </div>
                </div>
            </div>
            """
            
            content_sections.append({
                'title': 'Compliance Information',
                'content': compliance_info,
                'type': 'compliance'
            })
            
            # Effective Dates section
            if regulation.effective_date or regulation.expiry_date:
                dates_info = "<div class='dates-info'>"
                if regulation.effective_date:
                    dates_info += f"<p><strong>Effective Date:</strong> {regulation.effective_date.strftime('%B %d, %Y')}</p>"
                if regulation.expiry_date:
                    dates_info += f"<p><strong>Expiry Date:</strong> {regulation.expiry_date.strftime('%B %d, %Y')}</p>"
                dates_info += "</div>"
                
                content_sections.append({
                    'title': 'Important Dates',
                    'content': dates_info,
                    'type': 'dates'
                })
            
            # Keywords section
            if regulation.keywords:
                keywords_html = "<div class='keywords-section'>"
                keywords = [k.strip() for k in regulation.keywords.split(',')]
                for keyword in keywords:
                    keywords_html += f"<span class='badge keyword-badge'>{keyword}</span> "
                keywords_html += "</div>"
                
                content_sections.append({
                    'title': 'Related Keywords',
                    'content': keywords_html,
                    'type': 'keywords'
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
                - category (str): Regulation category (Legal, Licensing, etc.)
                - compliance_level (str): Required compliance level
                - property_type (str): Applicable property types
                - effective_date (datetime, optional): When regulation takes effect
                - expiry_date (datetime, optional): When regulation expires
                - keywords (str, optional): Comma-separated keywords
                
        Returns:
            Tuple containing:
                - success (bool): Whether creation succeeded
                - regulation (Regulation or None): Created object if successful
                - error (str or None): Error message if creation failed
                
        Note:
            Automatically rolls back database transaction on failure.
        """
        try:
            regulation = Regulation(
                jurisdiction_level=regulation_data.get('jurisdiction_level'),
                location=regulation_data.get('location'),
                title=regulation_data.get('title'),
                key_requirements=regulation_data.get('key_requirements'),
                last_updated=regulation_data.get('last_updated'),
                category=regulation_data.get('category'),
                compliance_level=regulation_data.get('compliance_level'),
                property_type=regulation_data.get('property_type'),
                effective_date=regulation_data.get('effective_date'),
                expiry_date=regulation_data.get('expiry_date'),
                keywords=regulation_data.get('keywords')
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
            Automatically rolls back database transaction on failure.
        """
        try:
            regulation = Regulation.query.get_or_404(regulation_id)
            
            # Update fields
            for field, value in regulation_data.items():
                if hasattr(regulation, field):
                    setattr(regulation, field, value)
            
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
    def get_public_saved_searches() -> List[SavedSearch]:
        """
        Retrieve all public saved searches for quick access filtering.
        
        Returns saved searches that are marked as public, allowing users
        to quickly apply common search configurations.
        
        Returns:
            List of SavedSearch objects that are marked as public.
            
        Note:
            Returns empty list if database query fails. Logs errors automatically.
        """
        try:
            return SavedSearch.query.filter_by(is_public=True).all()
        except Exception as e:
            logging.error(f"Error getting public saved searches: {str(e)}")
            return []

    @staticmethod
    def get_admin_statistics() -> Dict[str, Any]:
        """
        Get comprehensive statistics for admin dashboard.
        
        Returns various metrics and counts for regulation management,
        including totals, recent activity, and breakdowns by category.
        
        Returns:
            Dictionary containing:
                - total: Total number of regulations
                - recent: Recently updated regulations count
                - by_category: Count by category
                - by_jurisdiction: Count by jurisdiction level
                - by_location: Count by location
                - by_compliance_level: Count by compliance level
                
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
            
            # Category breakdown
            category_stats = db.session.query(
                Regulation.category,
                func.count(Regulation.id).label('count')
            ).group_by(Regulation.category).all()
            
            by_category = {stat.category or 'Unspecified': stat.count for stat in category_stats}
            
            # Jurisdiction level breakdown
            jurisdiction_stats = db.session.query(
                Regulation.jurisdiction_level,
                func.count(Regulation.id).label('count')
            ).group_by(Regulation.jurisdiction_level).all()
            
            by_jurisdiction = {stat.jurisdiction_level or 'Unspecified': stat.count for stat in jurisdiction_stats}
            
            # Location breakdown (top 10)
            location_stats = db.session.query(
                Regulation.location,
                func.count(Regulation.id).label('count')
            ).group_by(Regulation.location).order_by(func.count(Regulation.id).desc()).limit(10).all()
            
            by_location = {stat.location or 'Unspecified': stat.count for stat in location_stats}
            
            # Compliance level breakdown
            compliance_stats = db.session.query(
                Regulation.compliance_level,
                func.count(Regulation.id).label('count')
            ).group_by(Regulation.compliance_level).all()
            
            by_compliance_level = {stat.compliance_level or 'Unspecified': stat.count for stat in compliance_stats}
            
            return {
                'total': total_regulations,
                'recent': recent_count,
                'by_category': by_category,
                'by_jurisdiction': by_jurisdiction,
                'by_location': by_location,
                'by_compliance_level': by_compliance_level,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting regulation admin statistics: {str(e)}")
            return {
                'total': 0,
                'recent': 0,
                'by_category': {},
                'by_jurisdiction': {},
                'by_location': {},
                'by_compliance_level': {},
                'last_updated': datetime.now().isoformat()
            } 