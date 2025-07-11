"""
Search Service

Handles all search-related business logic:
- Advanced search with multiple criteria
- Search suggestions generation
- Saved search management
- Search suggestion tracking
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from models import db, Regulation, SavedSearch, SearchSuggestion
import logging


class SearchService:
    """
    Service class for handling search operations.
    
    This service provides comprehensive search functionality including:
    - Advanced multi-criteria search across regulations
    - Search suggestion generation and tracking
    - Saved search management with usage statistics
    - Query optimization and result ranking
    """
    
    @staticmethod
    def advanced_search(search_params: Dict[str, Any]) -> List[Regulation]:
        """
        Perform advanced search with multiple criteria.
        
        Executes a complex search query across regulations using multiple filters
        and text search capabilities. Supports date ranges, categorical filtering,
        and full-text search across titles, requirements, and keywords.
        
        Args:
            search_params: Dictionary containing search parameters:
                - query (str, optional): Text search query for full-text search
                - categories (List[str], optional): List of categories to filter by
                - compliance_levels (List[str], optional): List of compliance levels
                - property_types (List[str], optional): List of property types
                - locations (List[str], optional): List of locations to search within
                - jurisdictions (List[str], optional): List of jurisdiction levels
                - date_from (datetime, optional): Start date for date range filtering
                - date_to (datetime, optional): End date for date range filtering
                - date_range_days (int, optional): Number of days from current date
        
        Returns:
            List of Regulation objects matching the search criteria, ordered by
            last updated date (newest first).
            
        Raises:
            Exception: If database query fails or invalid parameters provided.
        """
        try:
            query = Regulation.query
            
            # Text search across multiple fields
            if search_params.get('query'):
                search_conditions = []
                search_terms = search_params['query'].split()
                
                for term in search_terms:
                    term_pattern = f'%{term}%'
                    search_conditions.append(
                        or_(
                            Regulation.title.ilike(term_pattern),
                            Regulation.key_requirements.ilike(term_pattern),
                            Regulation.keywords.ilike(term_pattern),
                            Regulation.location.ilike(term_pattern)
                        )
                    )
                
                if search_conditions:
                    query = query.filter(and_(*search_conditions))
            
            # Category filtering
            if search_params.get('categories'):
                query = query.filter(Regulation.category.in_(search_params['categories']))
            
            # Compliance level filtering
            if search_params.get('compliance_levels'):
                query = query.filter(Regulation.compliance_level.in_(search_params['compliance_levels']))
            
            # Property type filtering
            if search_params.get('property_types'):
                property_types = search_params['property_types']
                if len(property_types) == 1 and property_types[0] != 'Both':
                    query = query.filter(
                        or_(
                            Regulation.property_type == property_types[0],
                            Regulation.property_type == 'Both'
                        )
                    )
                elif 'Both' not in property_types:
                    query = query.filter(Regulation.property_type.in_(property_types))
            
            # Location filtering
            if search_params.get('locations'):
                location_conditions = [
                    Regulation.location.ilike(f'%{loc}%') 
                    for loc in search_params['locations']
                ]
                query = query.filter(or_(*location_conditions))
            
            # Jurisdiction level filtering
            if search_params.get('jurisdictions'):
                query = query.filter(Regulation.jurisdiction_level.in_(search_params['jurisdictions']))
            
            # Date range filtering
            if search_params.get('date_from') and search_params.get('date_to'):
                query = query.filter(
                    Regulation.last_updated.between(
                        search_params['date_from'], 
                        search_params['date_to']
                    )
                )
            elif search_params.get('date_range_days'):
                cutoff_date = datetime.now().date() - timedelta(days=int(search_params['date_range_days']))
                query = query.filter(Regulation.last_updated >= cutoff_date)
            
            # Execute query and return results
            results = query.order_by(Regulation.last_updated.desc()).all()
            
            # Update search suggestions if there was a text query
            # Temporarily disabled to prevent database constraint errors
            # if search_params.get('query'):
            #     SearchService.update_search_suggestions(search_params['query'], results)
            
            return results
            
        except Exception as e:
            logging.error(f"Advanced search error: {str(e)}")
            raise
    
    @staticmethod
    def get_search_suggestions(query_text: str) -> List[Dict[str, str]]:
        """
        Generate search suggestions based on user input.
        
        Provides intelligent search suggestions by matching user input against
        regulation titles, locations, categories, and keywords. Returns a ranked
        list of suggestions with type categorization for enhanced user experience.
        
        Args:
            query_text: User's partial search input (minimum 2 characters).
            
        Returns:
            List of suggestion dictionaries, each containing:
                - text (str): The suggested search term
                - type (str): Type of suggestion (title, location, category, keyword)
                - category (str): Display category for UI grouping
                
        Note:
            Returns empty list if query_text is less than 2 characters.
            Maximum of 10 unique suggestions returned.
        """
        if len(query_text) < 2:
            return []
        
        suggestions = []
        query = query_text.lower()
        
        try:
            # Get suggestions from regulation titles
            title_matches = db.session.query(Regulation.title).filter(
                Regulation.title.ilike(f'%{query}%')
            ).distinct().limit(5).all()
            
            for match in title_matches:
                suggestions.append({
                    'text': match[0],
                    'type': 'title',
                    'category': 'Regulation Titles'
                })
            
            # Get suggestions from locations
            location_matches = db.session.query(Regulation.location).filter(
                Regulation.location.ilike(f'%{query}%')
            ).distinct().limit(5).all()
            
            for match in location_matches:
                suggestions.append({
                    'text': match[0],
                    'type': 'location',
                    'category': 'Locations'
                })
            
            # Get suggestions from categories
            category_matches = db.session.query(Regulation.category).filter(
                Regulation.category.ilike(f'%{query}%')
            ).distinct().limit(5).all()
            
            for match in category_matches:
                suggestions.append({
                    'text': match[0],
                    'type': 'category',
                    'category': 'Categories'
                })
            
            # Get suggestions from keywords
            keyword_matches = db.session.query(Regulation.keywords).filter(
                Regulation.keywords.ilike(f'%{query}%')
            ).distinct().limit(3).all()
            
            for match in keyword_matches:
                if match[0]:
                    keywords = [k.strip() for k in match[0].split(',')]
                    for keyword in keywords:
                        if query in keyword.lower():
                            suggestions.append({
                                'text': keyword,
                                'type': 'keyword',
                                'category': 'Keywords'
                            })
            
            # Remove duplicates and limit results
            seen = set()
            unique_suggestions = []
            for suggestion in suggestions:
                key = (suggestion['text'], suggestion['type'])
                if key not in seen:
                    seen.add(key)
                    unique_suggestions.append(suggestion)
                    if len(unique_suggestions) >= 10:
                        break
            
            return unique_suggestions
            
        except Exception as e:
            logging.error(f"Error getting search suggestions: {str(e)}")
            return []
    
    @staticmethod
    def save_search(name: str, description: str, criteria: Dict[str, Any], is_public: bool = False) -> Tuple[bool, str, Optional[int]]:
        """
        Save a search configuration for later reuse.
        
        Persists search criteria with metadata for future execution. Validates
        search name uniqueness and handles database transactions safely.
        
        Args:
            name: Unique name for the saved search.
            description: Human-readable description of the search purpose.
            criteria: Complete search parameters dictionary as used in advanced_search.
            is_public: Whether the search should be available to all users.
            
        Returns:
            Tuple containing:
                - success (bool): Whether the save operation succeeded
                - message (str): Success or error message for user feedback
                - search_id (int or None): ID of created search, None on failure
                
        Raises:
            Exception: If database operation fails.
        """
        try:
            # Check if search name already exists
            existing = SavedSearch.query.filter_by(name=name).first()
            if existing:
                return False, 'A search with this name already exists', None
            
            # Create new saved search
            saved_search = SavedSearch(
                name=name,
                description=description,
                is_public=is_public
            )
            saved_search.set_search_criteria(criteria)
            
            db.session.add(saved_search)
            db.session.commit()
            
            return True, 'Search saved successfully', saved_search.id
            
        except Exception as e:
            logging.error(f"Save search error: {str(e)}")
            return False, 'Failed to save search', None
    
    @staticmethod
    def get_saved_searches() -> List[Dict[str, Any]]:
        """
        Retrieve all public saved searches ordered by popularity.
        
        Returns a list of publicly available saved searches, ranked by usage
        frequency to surface the most valuable search configurations first.
        
        Returns:
            List of saved search dictionaries, each containing:
                - id (int): Unique identifier for the saved search
                - name (str): Display name of the search
                - description (str): Search description
                - criteria (dict): Complete search parameters
                - use_count (int): Number of times this search has been used
                - last_used (str or None): ISO timestamp of last usage
                
        Note:
            Only returns public searches. Private searches are excluded.
            Results are ordered by use_count in descending order.
        """
        try:
            searches = SavedSearch.query.filter_by(is_public=True).order_by(
                SavedSearch.use_count.desc()
            ).all()
            
            search_data = []
            for search in searches:
                search_data.append({
                    'id': search.id,
                    'name': search.name,
                    'description': search.description,
                    'criteria': search.get_search_criteria(),
                    'use_count': search.use_count,
                    'last_used': search.last_used.isoformat() if search.last_used else None
                })
            
            return search_data
            
        except Exception as e:
            logging.error(f"Error getting saved searches: {str(e)}")
            return []
    
    @staticmethod
    def use_saved_search(search_id: int) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Execute a saved search and update usage analytics.
        
        Retrieves the search criteria for a saved search and updates usage
        statistics for analytics and ranking purposes.
        
        Args:
            search_id: Unique identifier of the saved search to execute.
            
        Returns:
            Tuple containing:
                - success (bool): Whether the search was retrieved successfully
                - criteria (dict or None): Search parameters if successful, None on failure
                - error (str or None): Error message if operation failed, None on success
                
        Raises:
            Exception: If database operation fails or search_id is invalid.
        """
        try:
            saved_search = SavedSearch.query.get_or_404(search_id)
            
            # Update usage statistics
            saved_search.use_count += 1
            saved_search.last_used = datetime.utcnow()
            db.session.commit()
            
            return True, saved_search.get_search_criteria(), None
            
        except Exception as e:
            logging.error(f"Use saved search error: {str(e)}")
            return False, None, 'Failed to load saved search'
    
    @staticmethod
    def update_search_suggestions(query_text: str, results: List[Regulation]) -> None:
        """
        Update search suggestion analytics based on successful queries.
        
        Tracks search query frequency and generates suggestions based on
        successful search results. Updates the suggestion database for
        improved future search recommendations.
        
        Args:
            query_text: The search query that was performed.
            results: List of Regulation objects that were found by the search.
            
        Note:
            This method is called automatically by advanced_search when
            a text query is provided. It helps improve suggestion quality
            over time by learning from successful search patterns.
        """
        try:
            # Use a separate transaction for suggestions to avoid rolling back the main search
            with db.session.begin_nested():
                # Update or create search suggestion for the query
                suggestion = SearchSuggestion.query.filter_by(
                    suggestion_text=query_text,
                    suggestion_type='query'
                ).first()
                
                if suggestion:
                    suggestion.frequency += 1
                    suggestion.last_used = datetime.utcnow()
                else:
                    # Use merge() to handle potential duplicates gracefully
                    suggestion = SearchSuggestion(
                        suggestion_text=query_text,
                        suggestion_type='query',
                        frequency=1,
                        created_at=datetime.utcnow(),
                        last_used=datetime.utcnow()
                    )
                    db.session.merge(suggestion)
                
                # Add suggestions based on successful results
                for result in results[:5]:  # Limit to top 5 results
                    # Add location suggestions
                    if result.location:
                        loc_suggestion = SearchSuggestion.query.filter_by(
                            suggestion_text=result.location,
                            suggestion_type='location'
                        ).first()
                        
                        if loc_suggestion:
                            loc_suggestion.frequency += 1
                            loc_suggestion.last_used = datetime.utcnow()
                        else:
                            loc_suggestion = SearchSuggestion(
                                suggestion_text=result.location,
                                suggestion_type='location',
                                frequency=1,
                                created_at=datetime.utcnow(),
                                last_used=datetime.utcnow()
                            )
                            db.session.merge(loc_suggestion)
                    
                    # Add category suggestions
                    if result.category:
                        cat_suggestion = SearchSuggestion.query.filter_by(
                            suggestion_text=result.category,
                            suggestion_type='category'
                        ).first()
                        
                        if cat_suggestion:
                            cat_suggestion.frequency += 1
                            cat_suggestion.last_used = datetime.utcnow()
                        else:
                            cat_suggestion = SearchSuggestion(
                                suggestion_text=result.category,
                                suggestion_type='category',
                                frequency=1,
                                created_at=datetime.utcnow(),
                                last_used=datetime.utcnow()
                            )
                            db.session.merge(cat_suggestion)
            
            db.session.commit()
            
        except Exception as e:
            # Log the error but don't let it break the search functionality
            logging.error(f"Error updating search suggestions: {str(e)}")
            # Rollback only the suggestion updates, not the main search
            db.session.rollback() 