"""
API Endpoint Tests

Tests all REST API endpoints for the STR Compliance Toolkit.
"""

import pytest
import json
from datetime import date
from models import db, UserUpdateInteraction


class TestSearchAPI:
    """Test cases for search API endpoints."""

    def test_advanced_search_api(self, client, multiple_regulations):
        """Test the advanced search API endpoint."""
        response = client.get('/api/search/advanced?query=tax&jurisdictions=National')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['results']) == 1
        assert data['results'][0]['title'] == 'Federal STR Tax Reporting'

    def test_advanced_search_api_no_params(self, client, multiple_regulations):
        """Test advanced search API with no parameters."""
        response = client.get('/api/search/advanced')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['results']) == 3  # All regulations

    def test_advanced_search_api_multiple_categories(self, client, multiple_regulations):
        """Test advanced search API with multiple categories."""
        response = client.get('/api/search/advanced?categories=Taxes,Registration')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['results']) == 2  # Federal and Texas regulations

    def test_search_suggestions_api(self, client, multiple_regulations):
        """Test the search suggestions API endpoint."""
        response = client.get('/api/search/suggestions?q=tax')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['suggestions'], list)

    def test_search_suggestions_api_short_query(self, client, multiple_regulations):
        """Test search suggestions API with short query."""
        response = client.get('/api/search/suggestions?q=t')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['suggestions']) == 0

    def test_search_suggestions_api_missing_query(self, client):
        """Test search suggestions API without query parameter."""
        response = client.get('/api/search/suggestions')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_save_search_api(self, client):
        """Test the save search API endpoint."""
        search_data = {
            'name': 'Test API Search',
            'description': 'Test search via API',
            'criteria': {'query': 'licensing', 'categories': ['Legal']},
            'is_public': True
        }
        
        response = client.post('/api/search/save', 
                              data=json.dumps(search_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'search_id' in data
        assert data['search_id'] is not None

    def test_save_search_api_missing_data(self, client):
        """Test save search API with missing required data."""
        search_data = {'name': 'Test Search'}  # Missing required fields
        
        response = client.post('/api/search/save',
                              data=json.dumps(search_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_get_saved_searches_api(self, client, saved_search):
        """Test the get saved searches API endpoint."""
        response = client.get('/api/search/saved')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['searches'], list)
        assert len(data['searches']) >= 1

    def test_use_saved_search_api(self, client, saved_search):
        """Test the use saved search API endpoint."""
        response = client.get(f'/api/search/saved/{saved_search.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'criteria' in data
        assert data['criteria']['query'] == 'licensing'

    def test_use_saved_search_api_not_found(self, client):
        """Test use saved search API with non-existent ID."""
        response = client.get('/api/search/saved/99999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False


class TestUpdatesAPI:
    """Test cases for updates API endpoints."""

    def test_search_updates_api(self, client, multiple_updates):
        """Test the search updates API endpoint."""
        response = client.get('/api/updates/search?category=Tax Updates&impact=High')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['updates']) == 1
        assert data['updates'][0]['category'] == 'Tax Updates'
        assert data['updates'][0]['impact_level'] == 'High'

    def test_search_updates_api_text_search(self, client, multiple_updates):
        """Test updates search API with text query."""
        response = client.get('/api/updates/search?query_text=court')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['updates']) == 1
        assert 'Court' in data['updates'][0]['title']

    def test_search_updates_api_no_params(self, client, multiple_updates):
        """Test updates search API with no parameters."""
        response = client.get('/api/updates/search')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['updates']) == 3  # All updates

    def test_toggle_bookmark_api(self, client, sample_update):
        """Test the toggle bookmark API endpoint."""
        bookmark_data = {'is_bookmarked': True}
        
        response = client.post(f'/api/updates/{sample_update.id}/bookmark',
                              data=json.dumps(bookmark_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['is_bookmarked'] is True

    def test_toggle_bookmark_api_invalid_update(self, client):
        """Test bookmark API with invalid update ID."""
        bookmark_data = {'is_bookmarked': True}
        
        response = client.post('/api/updates/99999/bookmark',
                              data=json.dumps(bookmark_data),
                              content_type='application/json')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False



    def test_get_bookmarked_updates_api(self, client, sample_update):
        """Test the get bookmarked updates API endpoint."""
        # First bookmark an update
        with client.session_transaction() as sess:
            sess['user_id'] = 'test-user'
        
        interaction = UserUpdateInteraction(
            update_id=sample_update.id,
            user_session='test-user',
            is_bookmarked=True
        )
        db.session.add(interaction)
        db.session.commit()
        
        response = client.get('/api/updates/bookmarked')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['bookmarked_updates']) >= 1





class TestExportAPI:
    """Test cases for export API endpoints."""

    def test_export_csv_api(self, client, multiple_regulations):
        """Test the CSV export API endpoint."""
        response = client.get('/api/export/csv?query=tax')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        
        # Check that CSV content is present
        csv_content = response.get_data(as_text=True)
        assert 'Federal STR Tax Reporting' in csv_content

    def test_export_csv_api_no_params(self, client, multiple_regulations):
        """Test CSV export API with no parameters (export all)."""
        response = client.get('/api/export/csv')
        
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        csv_content = response.get_data(as_text=True)
        # Should contain headers and data
        assert 'ID,Title,Jurisdiction Level' in csv_content


class TestMainRoutes:
    """Test cases for main application routes."""

    def test_index_route(self, client):
        """Test the index/home page."""
        response = client.get('/')
        assert response.status_code == 200

    def test_regulations_route(self, client, multiple_regulations):
        """Test the regulations page."""
        response = client.get('/regulations')
        assert response.status_code == 200

    def test_regulation_detail_route(self, client, sample_regulation):
        """Test the regulation detail page."""
        response = client.get(f'/regulation/{sample_regulation.id}')
        assert response.status_code == 200

    def test_regulation_detail_not_found(self, client):
        """Test regulation detail page with invalid ID."""
        response = client.get('/regulation/99999')
        assert response.status_code == 404

    def test_updates_route(self, client, multiple_updates):
        """Test the updates page."""
        response = client.get('/updates')
        assert response.status_code == 200

    def test_update_detail_route(self, client, sample_update):
        """Test the update detail page."""
        response = client.get(f'/update/{sample_update.id}')
        assert response.status_code == 200

    def test_update_detail_not_found(self, client):
        """Test update detail page with invalid ID."""
        response = client.get('/update/99999')
        assert response.status_code == 404

    def test_search_route(self, client):
        """Test the search page."""
        response = client.get('/search')
        assert response.status_code == 200




class TestAdminRoutes:
    """Test cases for admin routes."""

    def test_admin_login_page(self, client):
        """Test the admin login page."""
        response = client.get('/admin/login')
        assert response.status_code == 200

    def test_admin_login_post_valid(self, client):
        """Test admin login with valid credentials."""
        response = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'test-admin-password'  # From test config
        })
        # Should redirect to dashboard
        assert response.status_code == 302

    def test_admin_login_post_invalid(self, client):
        """Test admin login with invalid credentials."""
        response = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'wrong-password'
        })
        # Should return to login page with error
        assert response.status_code == 200  # No redirect

    def test_admin_dashboard_unauthorized(self, client):
        """Test admin dashboard without authentication."""
        response = client.get('/admin/dashboard')
        # Should redirect to login
        assert response.status_code == 302

    def test_admin_dashboard_authorized(self, authenticated_admin):
        """Test admin dashboard with authentication."""
        response = authenticated_admin.get('/admin/dashboard')
        assert response.status_code == 200

    def test_admin_logout(self, authenticated_admin):
        """Test admin logout."""
        response = authenticated_admin.get('/admin/logout')
        # Should redirect to login
        assert response.status_code == 302


class TestErrorHandling:
    """Test cases for error handling."""

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    def test_api_error_handling(self, client):
        """Test API error handling with malformed requests."""
        # Test POST with invalid JSON
        response = client.post('/api/search/save',
                              data='invalid json',
                              content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_api_method_not_allowed(self, client):
        """Test API method not allowed error."""
        # Try POST on GET-only endpoint
        response = client.post('/api/search/advanced')
        assert response.status_code == 405


class TestSecurity:
    """Test cases for security measures."""

    def test_csrf_protection_disabled_in_tests(self, client):
        """Test that CSRF protection is disabled in test environment."""
        # This should work without CSRF token in tests
        response = client.post('/api/search/save',
                              data=json.dumps({'name': 'test'}),
                              content_type='application/json')
        # Should fail for missing data, not CSRF
        assert response.status_code == 400

    def test_admin_routes_protected(self, client):
        """Test that admin routes require authentication."""
        protected_routes = [
            '/admin/dashboard',
            '/admin/regulations',
            '/admin/updates'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            # Should redirect to login
            assert response.status_code == 302

    def test_sql_injection_protection(self, client, multiple_regulations):
        """Test basic SQL injection protection."""
        # Try SQL injection in search query
        malicious_query = "'; DROP TABLE regulation; --"
        
        response = client.get(f'/api/search/advanced?query={malicious_query}')
        
        # Should return normally (no error), SQLAlchemy should handle this
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True 