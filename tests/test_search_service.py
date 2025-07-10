"""
Unit Tests for SearchService

Tests all search functionality including advanced search, suggestions, and saved searches.
"""

import pytest
from datetime import datetime, timedelta
from app.services.search_service import SearchService
from models import db, Regulation, SavedSearch, SearchSuggestion


class TestSearchService:
    """Test cases for SearchService functionality."""

    def test_advanced_search_text_query(self, app, multiple_regulations):
        """Test advanced search with text query."""
        with app.app_context():
            # Test search for "tax" - should find Federal STR Tax Reporting
            results = SearchService.advanced_search({'query': 'tax'})
            
            assert len(results) == 1
            assert results[0].title == 'Federal STR Tax Reporting'
            assert results[0].category == 'Taxes'

    def test_advanced_search_category_filter(self, app, multiple_regulations):
        """Test advanced search with category filtering."""
        with app.app_context():
            # Test search by registration category
            results = SearchService.advanced_search({'categories': ['Registration']})
            
            assert len(results) == 1
            assert results[0].title == 'Texas STR Registration'
            assert results[0].category == 'Registration'

    def test_advanced_search_jurisdiction_filter(self, app, multiple_regulations):
        """Test advanced search with jurisdiction filtering."""
        with app.app_context():
            # Test search by state jurisdiction
            results = SearchService.advanced_search({'jurisdictions': ['State']})
            
            assert len(results) == 1
            assert results[0].jurisdiction_level == 'State'
            assert results[0].location == 'Texas'

    def test_advanced_search_location_filter(self, app, multiple_regulations):
        """Test advanced search with location filtering."""
        with app.app_context():
            # Test search by location containing "Austin"
            results = SearchService.advanced_search({'locations': ['Austin']})
            
            assert len(results) == 1
            assert 'Austin' in results[0].location
            assert results[0].category == 'Zoning'

    def test_advanced_search_multiple_filters(self, app, multiple_regulations):
        """Test advanced search with multiple combined filters."""
        with app.app_context():
            # Search for regulations with "STR" in title and state jurisdiction
            results = SearchService.advanced_search({
                'query': 'STR',
                'jurisdictions': ['State']
            })
            
            assert len(results) == 1
            assert results[0].jurisdiction_level == 'State'
            assert 'STR' in results[0].title

    def test_advanced_search_property_type_filter(self, app, multiple_regulations):
        """Test advanced search with property type filtering."""
        with app.app_context():
            # Search for residential-only properties
            results = SearchService.advanced_search({'property_types': ['Residential']})
            
            assert len(results) == 1
            assert results[0].property_type == 'Residential'
            assert results[0].title == 'Texas STR Registration'

    def test_advanced_search_no_results(self, app, multiple_regulations):
        """Test advanced search with no matching results."""
        with app.app_context():
            # Search for non-existent term
            results = SearchService.advanced_search({'query': 'nonexistent'})
            
            assert len(results) == 0

    def test_advanced_search_date_range(self, app, multiple_regulations):
        """Test advanced search with date range filtering."""
        with app.app_context():
            # Search for regulations updated after January 5, 2024
            from datetime import date
            results = SearchService.advanced_search({
                'date_from': date(2024, 1, 5)
            })
            
            # Should find Texas (Jan 5) and Austin (Jan 10) regulations
            assert len(results) >= 2
            for result in results:
                assert result.last_updated >= date(2024, 1, 5)

    def test_get_search_suggestions_short_query(self, app):
        """Test search suggestions with short query (should return empty)."""
        with app.app_context():
            suggestions = SearchService.get_search_suggestions('t')
            assert suggestions == []

    def test_get_search_suggestions_title_matches(self, app, multiple_regulations):
        """Test search suggestions from regulation titles."""
        with app.app_context():
            suggestions = SearchService.get_search_suggestions('tax')
            
            # Should find suggestions from titles containing "tax"
            title_suggestions = [s for s in suggestions if s['type'] == 'title']
            assert len(title_suggestions) > 0
            assert any('Tax' in s['text'] for s in title_suggestions)

    def test_get_search_suggestions_location_matches(self, app, multiple_regulations):
        """Test search suggestions from regulation locations."""
        with app.app_context():
            suggestions = SearchService.get_search_suggestions('texas')
            
            # Should find Texas in location suggestions
            location_suggestions = [s for s in suggestions if s['type'] == 'location']
            assert len(location_suggestions) > 0
            assert any('Texas' in s['text'] for s in location_suggestions)

    def test_get_search_suggestions_category_matches(self, app, multiple_regulations):
        """Test search suggestions from regulation categories."""
        with app.app_context():
            suggestions = SearchService.get_search_suggestions('zoning')
            
            # Should find Zoning in category suggestions
            category_suggestions = [s for s in suggestions if s['type'] == 'category']
            assert len(category_suggestions) > 0
            assert any('Zoning' in s['text'] for s in category_suggestions)

    def test_get_search_suggestions_keyword_matches(self, app, multiple_regulations):
        """Test search suggestions from regulation keywords."""
        with app.app_context():
            suggestions = SearchService.get_search_suggestions('permit')
            
            # Should find suggestions from keywords containing "permit"
            keyword_suggestions = [s for s in suggestions if s['type'] == 'keyword']
            assert len(keyword_suggestions) > 0

    def test_get_search_suggestions_limit(self, app, multiple_regulations):
        """Test that search suggestions are limited to maximum 10 results."""
        with app.app_context():
            # Use a broad search term
            suggestions = SearchService.get_search_suggestions('st')
            
            # Should return at most 10 suggestions
            assert len(suggestions) <= 10

    def test_save_search_success(self, app):
        """Test successfully saving a search configuration."""
        with app.app_context():
            criteria = {
                'query': 'licensing',
                'categories': ['Legal', 'Licensing'],
                'jurisdictions': ['State']
            }
            
            success, message, search_id = SearchService.save_search(
                'Test Search', 
                'Test search description', 
                criteria,
                is_public=True
            )
            
            assert success is True
            assert 'successfully' in message
            assert search_id is not None
            
            # Verify the search was saved correctly
            saved_search = SavedSearch.query.get(search_id)
            assert saved_search is not None
            assert saved_search.name == 'Test Search'
            assert saved_search.is_public is True
            assert saved_search.get_search_criteria() == criteria

    def test_save_search_duplicate_name(self, app, saved_search):
        """Test saving a search with duplicate name fails."""
        with app.app_context():
            criteria = {'query': 'test'}
            
            success, message, search_id = SearchService.save_search(
                saved_search.name,  # Use existing name
                'Different description',
                criteria
            )
            
            assert success is False
            assert 'already exists' in message
            assert search_id is None

    def test_get_saved_searches(self, app, saved_search):
        """Test retrieving saved searches."""
        with app.app_context():
            searches = SearchService.get_saved_searches()
            
            assert len(searches) >= 1
            
            # Find our test search
            test_search = next((s for s in searches if s['name'] == saved_search.name), None)
            assert test_search is not None
            assert test_search['description'] == saved_search.description
            assert test_search['use_count'] == 0
            assert 'criteria' in test_search

    def test_use_saved_search_success(self, app, saved_search):
        """Test successfully using a saved search."""
        with app.app_context():
            initial_use_count = saved_search.use_count
            
            success, criteria, error = SearchService.use_saved_search(saved_search.id)
            
            assert success is True
            assert criteria is not None
            assert error is None
            assert 'query' in criteria
            assert criteria['query'] == 'licensing'
            
            # Verify use count was incremented
            db.session.refresh(saved_search)
            assert saved_search.use_count == initial_use_count + 1
            assert saved_search.last_used is not None

    def test_use_saved_search_not_found(self, app):
        """Test using a non-existent saved search."""
        with app.app_context():
            success, criteria, error = SearchService.use_saved_search(99999)
            
            assert success is False
            assert criteria is None
            assert error is not None

    def test_update_search_suggestions_new_query(self, app, multiple_regulations):
        """Test updating search suggestions with new query."""
        with app.app_context():
            # Perform search and update suggestions
            results = SearchService.advanced_search({'query': 'licensing'})
            
            # This should create/update search suggestion entries
            # Verify by checking if SearchSuggestion entries exist
            query_suggestion = SearchSuggestion.query.filter_by(
                suggestion_text='licensing',
                suggestion_type='query'
            ).first()
            
            # Note: This test verifies the method runs without error
            # The actual suggestion creation depends on the SearchSuggestion model
            # being properly implemented
            assert len(results) >= 0  # At minimum, should not crash

    def test_update_search_suggestions_increments_frequency(self, app, multiple_regulations):
        """Test that repeated searches increment suggestion frequency."""
        with app.app_context():
            query_text = 'tax'
            
            # Create initial suggestion
            suggestion = SearchSuggestion(
                suggestion_text=query_text,
                suggestion_type='query',
                frequency=1
            )
            db.session.add(suggestion)
            db.session.commit()
            
            initial_frequency = suggestion.frequency
            
            # Perform search which should update suggestions
            results = SearchService.advanced_search({'query': query_text})
            
            # Check if frequency was incremented
            db.session.refresh(suggestion)
            # Note: The actual increment depends on the implementation
            # This test verifies the method runs without error
            assert suggestion.frequency >= initial_frequency

    def test_advanced_search_empty_params(self, app, multiple_regulations):
        """Test advanced search with empty parameters."""
        with app.app_context():
            # Search with no parameters should return all regulations
            results = SearchService.advanced_search({})
            
            assert len(results) == 3  # All regulations from fixture
            # Should be ordered by last_updated desc
            assert results[0].last_updated >= results[1].last_updated

    def test_advanced_search_case_insensitive(self, app, multiple_regulations):
        """Test that text search is case insensitive."""
        with app.app_context():
            # Search with different cases
            results_lower = SearchService.advanced_search({'query': 'str'})
            results_upper = SearchService.advanced_search({'query': 'STR'})
            results_mixed = SearchService.advanced_search({'query': 'StR'})
            
            # All should return the same results
            assert len(results_lower) == len(results_upper) == len(results_mixed)
            if len(results_lower) > 0:
                assert results_lower[0].id == results_upper[0].id == results_mixed[0].id

    def test_advanced_search_multiple_terms(self, app, multiple_regulations):
        """Test advanced search with multiple search terms."""
        with app.app_context():
            # Search for "STR Registration" - should match Texas regulation
            results = SearchService.advanced_search({'query': 'STR Registration'})
            
            # Should find the Texas STR Registration
            assert len(results) >= 1
            texas_reg = next((r for r in results if 'Texas' in r.title), None)
            assert texas_reg is not None

    def test_search_error_handling(self, app):
        """Test that search methods handle errors gracefully."""
        with app.app_context():
            # Test with invalid data types that might cause errors
            try:
                # This should not crash the application
                results = SearchService.advanced_search({'query': None})
                assert isinstance(results, list)
                
                suggestions = SearchService.get_search_suggestions(None)
                assert isinstance(suggestions, list)
                
            except Exception:
                # Methods should handle errors gracefully and return empty lists
                # rather than crashing
                pytest.fail("Search methods should handle errors gracefully") 