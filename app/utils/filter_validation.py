"""
Filter Validation Utilities
Provides validation and sanitization for API filter parameters
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class FilterValidationError(Exception):
    """Custom exception for filter validation errors"""
    pass


class FilterValidator:
    """Validates and sanitizes filter parameters"""
    
    # Define valid filter values
    VALID_JURISDICTION_LEVELS = ['National', 'State', 'Local']
    VALID_STATUSES = ['Recent', 'Upcoming', 'Proposed', 'Current & Active', 'Expired']
    VALID_CATEGORIES = [
        'Regulatory Changes', 'Tax Updates', 'Licensing', 'Zoning', 
        'Safety', 'Environmental', 'General'
    ]
    VALID_IMPACT_LEVELS = ['High', 'Medium', 'Low']
    VALID_PRIORITIES = [1, 2, 3]
    VALID_COMPLIANCE_LEVELS = ['Mandatory', 'Recommended', 'Optional']
    VALID_PROPERTY_TYPES = ['Residential', 'Commercial', 'Mixed-use', 'Both']
    VALID_DECISION_STATUSES = ['Proposed', 'Under Review', 'Approved', 'Rejected']
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """
        Validate and sanitize search query
        
        Args:
            query: Raw search query string
            
        Returns:
            Sanitized search query
            
        Raises:
            FilterValidationError: If query is invalid
        """
        if not query:
            return ""
            
        # Strip whitespace
        query = query.strip()
        
        # Check length
        if len(query) > 500:
            raise FilterValidationError("Search query too long (max 500 characters)")
        
        # Check for SQL injection patterns first
        sql_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b',
            r'[;\'"\\]',
            r'--',
            r'/\*.*\*/'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt in search query: {query}")
                raise FilterValidationError("Invalid characters in search query")
        
        # Remove potentially dangerous characters and tags
        query = re.sub(r'<script.*?</script>', '', query, flags=re.IGNORECASE | re.DOTALL)
        query = re.sub(r'[<>"\']', '', query)
        
        return query
    
    @staticmethod
    def validate_jurisdiction_level(level: str) -> Optional[str]:
        """Validate jurisdiction level"""
        if not level:
            return None
        
        level = level.strip()
        if level not in FilterValidator.VALID_JURISDICTION_LEVELS:
            logger.warning(f"Invalid jurisdiction level: {level}")
            return None
        
        return level
    
    @staticmethod
    def validate_status(status: str) -> Optional[str]:
        """Validate status"""
        if not status:
            return None
        
        status = status.strip()
        if status not in FilterValidator.VALID_STATUSES:
            logger.warning(f"Invalid status: {status}")
            return None
        
        return status
    
    @staticmethod
    def validate_category(category: str) -> Optional[str]:
        """Validate category"""
        if not category:
            return None
        
        category = category.strip()
        if category not in FilterValidator.VALID_CATEGORIES:
            logger.warning(f"Invalid category: {category}")
            return None
        
        return category
    
    @staticmethod
    def validate_impact_level(impact: str) -> Optional[str]:
        """Validate impact level"""
        if not impact:
            return None
        
        impact = impact.strip()
        if impact not in FilterValidator.VALID_IMPACT_LEVELS:
            logger.warning(f"Invalid impact level: {impact}")
            return None
        
        return impact
    
    @staticmethod
    def validate_priority(priority: Union[str, int]) -> Optional[int]:
        """Validate priority"""
        if not priority:
            return None
        
        try:
            priority_int = int(priority)
            if priority_int not in FilterValidator.VALID_PRIORITIES:
                logger.warning(f"Invalid priority: {priority_int}")
                return None
            return priority_int
        except (ValueError, TypeError):
            logger.warning(f"Invalid priority format: {priority}")
            return None
    
    @staticmethod
    def validate_date(date_str: str) -> Optional[datetime]:
        """Validate date string"""
        if not date_str:
            return None
        
        try:
            # Try multiple date formats
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            
            raise ValueError("No valid date format found")
            
        except (ValueError, TypeError):
            logger.warning(f"Invalid date format: {date_str}")
            return None
    
    @staticmethod
    def validate_boolean(value: Union[str, bool]) -> Optional[bool]:
        """Validate boolean value"""
        if value is None:
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ['true', '1', 'yes', 'on']:
                return True
            elif value in ['false', '0', 'no', 'off']:
                return False
        
        logger.warning(f"Invalid boolean value: {value}")
        return None
    
    @staticmethod
    def validate_location(location: str) -> Optional[str]:
        """Validate location string"""
        if not location:
            return None
        
        location = location.strip()
        
        # Check length
        if len(location) > 100:
            logger.warning(f"Location too long: {location}")
            return None
        
        # Remove potentially dangerous characters
        location = re.sub(r'[<>"\']', '', location)
        
        return location
    
    @staticmethod
    def validate_array_parameter(values: List[str], valid_values: List[str]) -> List[str]:
        """Validate array parameter against valid values"""
        if not values:
            return []
        
        validated = []
        for value in values:
            if value and value.strip() in valid_values:
                validated.append(value.strip())
            else:
                logger.warning(f"Invalid array value: {value}")
        
        return validated
    
    @staticmethod
    def validate_regulations_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate regulations filter parameters
        
        Args:
            filters: Raw filter parameters
            
        Returns:
            Validated and sanitized filter parameters
        """
        validated = {}
        
        # Search query
        if 'q' in filters or 'query' in filters:
            query = filters.get('q') or filters.get('query', '')
            validated['query'] = FilterValidator.validate_search_query(query)
        
        # Jurisdiction level
        if 'jurisdiction_level' in filters:
            level = FilterValidator.validate_jurisdiction_level(filters['jurisdiction_level'])
            if level:
                validated['jurisdiction_level'] = level
        
        # Location
        if 'location' in filters:
            location = FilterValidator.validate_location(filters['location'])
            if location:
                validated['location'] = location
        
        # Categories
        if 'categories' in filters:
            categories = FilterValidator.validate_array_parameter(
                filters['categories'], FilterValidator.VALID_CATEGORIES
            )
            if categories:
                validated['categories'] = categories
        
        # Compliance levels
        if 'compliance_levels' in filters:
            levels = FilterValidator.validate_array_parameter(
                filters['compliance_levels'], FilterValidator.VALID_COMPLIANCE_LEVELS
            )
            if levels:
                validated['compliance_levels'] = levels
        
        # Property types
        if 'property_types' in filters:
            types = FilterValidator.validate_array_parameter(
                filters['property_types'], FilterValidator.VALID_PROPERTY_TYPES
            )
            if types:
                validated['property_types'] = types
        
        # Date range
        if 'date_from' in filters:
            date_from = FilterValidator.validate_date(filters['date_from'])
            if date_from:
                validated['date_from'] = date_from
        
        if 'date_to' in filters:
            date_to = FilterValidator.validate_date(filters['date_to'])
            if date_to:
                validated['date_to'] = date_to
        
        return validated
    
    @staticmethod
    def validate_updates_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate updates filter parameters
        
        Args:
            filters: Raw filter parameters
            
        Returns:
            Validated and sanitized filter parameters
        """
        validated = {}
        
        # Search query
        if 'q' in filters or 'query' in filters:
            query = filters.get('q') or filters.get('query', '')
            validated['query'] = FilterValidator.validate_search_query(query)
        
        # Status
        if 'status' in filters:
            status = FilterValidator.validate_status(filters['status'])
            if status:
                validated['status'] = status
        
        # Category
        if 'category' in filters:
            category = FilterValidator.validate_category(filters['category'])
            if category:
                validated['category'] = category
        
        # Impact level
        if 'impact_level' in filters:
            impact = FilterValidator.validate_impact_level(filters['impact_level'])
            if impact:
                validated['impact_level'] = impact
        
        # Priority
        if 'priority' in filters:
            priority = FilterValidator.validate_priority(filters['priority'])
            if priority:
                validated['priority'] = priority
        
        # Jurisdiction
        if 'jurisdiction' in filters:
            jurisdiction = FilterValidator.validate_location(filters['jurisdiction'])
            if jurisdiction:
                validated['jurisdiction'] = jurisdiction
        
        # Action required
        if 'action_required' in filters:
            action_required = FilterValidator.validate_boolean(filters['action_required'])
            if action_required is not None:
                validated['action_required'] = action_required
        
        # Date range
        if 'date_from' in filters:
            date_from = FilterValidator.validate_date(filters['date_from'])
            if date_from:
                validated['date_from'] = date_from
        
        if 'date_to' in filters:
            date_to = FilterValidator.validate_date(filters['date_to'])
            if date_to:
                validated['date_to'] = date_to
        
        return validated


def serialize_filters(filters: Dict[str, Any]) -> str:
    """
    Serialize filters to URL query string
    
    Args:
        filters: Filter parameters dictionary
        
    Returns:
        URL query string
    """
    from urllib.parse import urlencode
    
    params = []
    for key, value in filters.items():
        if value is None:
            continue
        
        if isinstance(value, list):
            for item in value:
                if item:
                    params.append((f"{key}[]", str(item)))
        elif isinstance(value, datetime):
            params.append((key, value.strftime('%Y-%m-%d')))
        elif isinstance(value, bool):
            params.append((key, 'true' if value else 'false'))
        else:
            params.append((key, str(value)))
    
    return urlencode(params)


 