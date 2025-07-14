"""
API Endpoint Tests

Tests all REST API endpoints for the STR Compliance Toolkit.
"""

import pytest
import json
from datetime import date
from models import db, UserUpdateInteraction


class TestUpdatesAPI:
    """Test cases for updates API endpoints."""

    def test_get_updates_api(self, client, sample_update):
        """Test getting all updates via API."""
        response = client.get('/api/updates')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['updates']) >= 1
        assert data['total_count'] >= 1

    def test_get_update_by_id_api(self, client, sample_update):
        """Test getting a specific update by ID via API."""
        update_id = sample_update.id
        response = client.get(f'/api/updates/{update_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['update']['id'] == update_id
        assert 'title' in data['update']

    def test_get_update_not_found(self, client):
        """Test getting a non-existent update."""
        response = client.get('/api/updates/99999')
        assert response.status_code == 404

    def test_toggle_bookmark_api(self, client, sample_update):
        """Test toggling bookmark status for an update."""
        update_id = sample_update.id
        response = client.post(f'/api/updates/{update_id}/bookmark',
                              data=json.dumps({'is_bookmarked': True}),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['is_bookmarked'] is True

    def test_toggle_bookmark_api_invalid_update(self, client):
        """Test toggling bookmark for non-existent update."""
        response = client.post('/api/updates/99999/bookmark',
                              data=json.dumps({'is_bookmarked': True}),
                              content_type='application/json')
        assert response.status_code == 404

    def test_get_bookmarked_updates_api(self, client, sample_update):
        """Test getting bookmarked updates."""
        update_id = sample_update.id
        # First bookmark an update
        client.post(f'/api/updates/{update_id}/bookmark',
                   data=json.dumps({'is_bookmarked': True}),
                   content_type='application/json')
        
        # Then get bookmarked updates
        response = client.get('/api/updates/bookmarked')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestExportAPI:
    """Test cases for export API endpoints."""

    def test_export_csv_api(self, client, multiple_regulations):
        """Test CSV export functionality."""
        response = client.get('/api/export/csv')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'attachment' in response.headers.get('Content-Disposition', '')

    def test_export_csv_api_no_params(self, client):
        """Test CSV export with no parameters."""
        response = client.get('/api/export/csv')
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'


class TestLocationsAPI:
    """Test cases for locations API endpoints."""

    def test_get_locations_by_jurisdiction(self, client):
        """Test getting locations by jurisdiction level."""
        response = client.get('/api/locations/State')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['jurisdiction_level'] == 'State'
        assert isinstance(data['locations'], list)


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
        regulation_id = sample_regulation.id
        response = client.get(f'/regulations/{regulation_id}')
        assert response.status_code == 200

    def test_regulation_detail_not_found(self, client):
        """Test regulation detail page with invalid ID."""
        response = client.get('/regulations/99999')
        assert response.status_code == 404

    def test_updates_route(self, client, sample_update):
        """Test the updates page."""
        response = client.get('/updates')
        assert response.status_code == 200

    def test_update_detail_route(self, client, sample_update):
        """Test the update detail page."""
        update_id = sample_update.id
        response = client.get(f'/updates/{update_id}')
        assert response.status_code == 200

    def test_update_detail_not_found(self, client):
        """Test update detail page with invalid ID."""
        response = client.get('/updates/99999')
        assert response.status_code == 404


class TestAdminRoutes:
    """Test cases for admin routes."""

    def test_admin_login_page(self, client):
        """Test the admin login page."""
        response = client.get('/admin/login')
        assert response.status_code == 200

    def test_admin_login_post_valid(self, client):
        """Test admin login with valid credentials."""
        response = client.post('/admin/login', data={
            'username': 'admin',  # Default admin created by app
            'password': 'test-admin-password'  # From test config
        }, follow_redirects=False)
        # Should redirect to admin area
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
        response = client.get('/admin/')
        # Should redirect to login
        assert response.status_code == 302

    def test_admin_dashboard_authorized(self, authenticated_admin):
        """Test admin dashboard with authentication."""
        response = authenticated_admin.get('/admin/')
        assert response.status_code == 302  # Redirects to manage_regulations

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

    def test_api_error_handling(self, client, sample_update):
        """Test API error handling with malformed requests."""
        # Test POST with invalid JSON to an endpoint that expects JSON
        update_id = sample_update.id
        response = client.post(f'/api/updates/{update_id}/bookmark',
                              data='invalid json',
                              content_type='application/json')
        # Should return 200 with defaults since we handle JSON errors gracefully
        assert response.status_code == 200

    def test_api_method_not_allowed(self, client):
        """Test API method not allowed error."""
        # Try POST on GET-only endpoint
        response = client.post('/api/updates')
        assert response.status_code == 405


class TestSecurity:
    """Test cases for security measures."""

    def test_csrf_protection_disabled_in_tests(self, client, sample_update):
        """Test that CSRF protection is disabled in test environment."""
        # This should work without CSRF token in tests
        update_id = sample_update.id
        response = client.post(f'/api/updates/{update_id}/bookmark',
                              data=json.dumps({'is_bookmarked': True}),
                              content_type='application/json')
        # Should work since CSRF is disabled in tests
        assert response.status_code == 200

    def test_admin_routes_protected(self, client):
        """Test that admin routes require authentication."""
        protected_routes = [
            '/admin/',
            '/admin/regulations',
            '/admin/updates'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            # Should redirect to login
            assert response.status_code == 302

    def test_basic_sql_safety(self, client):
        """Test basic SQL safety with malicious input."""
        # Try malicious input in URL path
        malicious_input = "'; DROP TABLE updates; --"
        
        response = client.get(f'/updates/{malicious_input}')
        
        # Should return 404 (invalid ID format) not 500 (SQL error)
        assert response.status_code == 404


class TestClientErrorReporting:
    """Test cases for client error reporting."""

    def test_client_error_reporting(self, client):
        """Test client error reporting endpoint."""
        error_data = {
            'error': {
                'type': 'javascript_error',
                'message': 'Test error message',
                'filename': 'test.js',
                'lineno': 10,
                'colno': 5
            },
            'level': 'error'
        }
        
        response = client.post('/api/client-errors',
                              data=json.dumps(error_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True 