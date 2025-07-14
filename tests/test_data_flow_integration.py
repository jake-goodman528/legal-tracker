"""
Data Flow Integration Tests

Tests complete data flow integration between admin and public views,
including all new fields, error handling, and route functionality.
"""

import pytest
from datetime import datetime, date, timedelta
from flask import url_for
from models import db, Update, Regulation, AdminUser
from app.services import UpdateService
import json


class TestDataFlowIntegration:
    """Test complete data flow integration"""

    def test_update_crud_with_new_fields(self, app, client):
        """Test that all CRUD operations work with new fields"""
        with app.app_context():
            # Test data with all new fields
            update_data = {
                'title': 'Test Update with New Fields',
                'description': 'Test description',
                'jurisdiction_affected': 'Test City',
                'update_date': date.today(),
                'status': 'Recent',
                'category': 'Regulatory Changes',
                'impact_level': 'High',
                'priority': 1,
                'action_required': True,
                'action_description': 'Test action required',
                'property_types': 'Residential',
                'tags': 'test,integration',
                'source_url': 'https://example.com',
                # New fields
                'expected_decision_date': date.today() + timedelta(days=30),
                'potential_impact': 'High impact on operators',
                'decision_status': 'Under Review',
                'change_type': 'Recent',
                'compliance_deadline': date.today() + timedelta(days=60),
                'affected_operators': 'All residential operators',
                'related_regulation_ids': '1,2,3'
            }
            
            # Test create
            success, update, error = UpdateService.create_update(update_data)
            assert success, f"Create failed: {error}"
            assert update is not None
            assert update.expected_decision_date == update_data['expected_decision_date']
            assert update.potential_impact == update_data['potential_impact']
            assert update.decision_status == update_data['decision_status']
            assert update.change_type == update_data['change_type']
            assert update.compliance_deadline == update_data['compliance_deadline']
            assert update.affected_operators == update_data['affected_operators']
            
            # Test read
            retrieved_update = UpdateService.get_update_by_id(update.id)
            assert retrieved_update is not None
            assert retrieved_update.title == update_data['title']
            assert retrieved_update.expected_decision_date == update_data['expected_decision_date']
            
            # Test update
            updated_data = {
                'title': 'Updated Title',
                'potential_impact': 'Updated impact assessment',
                'decision_status': 'Approved'
            }
            success, updated_update, error = UpdateService.update_update(update.id, updated_data)
            assert success, f"Update failed: {error}"
            assert updated_update.title == 'Updated Title'
            assert updated_update.potential_impact == 'Updated impact assessment'
            assert updated_update.decision_status == 'Approved'
            
            # Test delete
            success, error = UpdateService.delete_update(update.id)
            assert success, f"Delete failed: {error}"
            
            # Verify deletion
            deleted_update = UpdateService.get_update_by_id(update.id)
            assert deleted_update is None

    def test_public_routes_with_new_fields(self, app, client):
        """Test that public routes display new fields correctly"""
        with app.app_context():
            # Create test update with new fields
            update_data = {
                'title': 'Public View Test Update',
                'description': 'Test description for public view',
                'jurisdiction_affected': 'Test City',
                'update_date': date.today(),
                'status': 'Recent',
                'category': 'Regulatory Changes',
                'impact_level': 'High',
                'priority': 1,
                'change_type': 'Recent',
                'expected_decision_date': date.today() + timedelta(days=30),
                'potential_impact': 'Significant impact on all operators',
                'decision_status': 'Under Review',
                'compliance_deadline': date.today() + timedelta(days=60),
                'affected_operators': 'All short-term rental operators'
            }
            
            success, update, error = UpdateService.create_update(update_data)
            assert success, f"Setup failed: {error}"
            
            # Test main updates page
            response = client.get('/updates')
            assert response.status_code == 200
            assert 'Public View Test Update' in response.get_data(as_text=True)
            
            # Test update detail page
            response = client.get(f'/updates/{update.id}')
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'Public View Test Update' in data
            assert 'Significant impact on all operators' in data
            assert 'Under Review' in data
            
            # Test viewing new fields
            assert 'Under Review' in response.get_data(as_text=True)
            assert 'Regulatory Changes' in response.get_data(as_text=True)

    def test_api_endpoints_with_new_fields(self, app, client):
        """Test that API endpoints return new fields correctly"""
        with app.app_context():
            # Create test update
            update_data = {
                'title': 'API Test Update',
                'description': 'Test description for API',
                'jurisdiction_affected': 'API Test City',
                'update_date': date.today(),
                'status': 'Recent',
                'category': 'Regulatory Changes',
                'impact_level': 'Medium',
                'priority': 2,
                'change_type': 'Recent',
                'expected_decision_date': date.today() + timedelta(days=15),
                'potential_impact': 'Moderate impact on operations',
                'decision_status': 'Proposed',
                'compliance_deadline': date.today() + timedelta(days=45),
                'affected_operators': 'Commercial operators only'
            }
            
            success, update, error = UpdateService.create_update(update_data)
            assert success, f"Setup failed: {error}"
            
            # Test get all updates API
            response = client.get('/api/updates')
            assert response.status_code == 200
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            assert len(data['updates']) > 0
            
            # Find our test update
            test_update = None
            for api_update in data['updates']:
                if api_update['title'] == 'API Test Update':
                    test_update = api_update
                    break
            
            assert test_update is not None
            assert test_update['expected_decision_date'] is not None
            assert test_update['potential_impact'] == 'Moderate impact on operations'
            assert test_update['decision_status'] == 'Proposed'
            assert test_update['change_type'] == 'Recent'
            assert test_update['compliance_deadline'] is not None
            assert test_update['affected_operators'] == 'Commercial operators only'
            
            # Test get single update API
            response = client.get(f'/api/updates/{update.id}')
            assert response.status_code == 200
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            assert data['update']['title'] == 'API Test Update'
            assert data['update']['potential_impact'] == 'Moderate impact on operations'
            
            # Test search API with new fields
            response = client.get('/api/updates/search?decision_statuses[]=Proposed')
            assert response.status_code == 200
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True

    def test_admin_routes_with_new_fields(self, app, client):
        """Test that admin routes handle new fields correctly"""
        with app.app_context():
            # Create admin user
            admin = AdminUser(username='testadmin', password_hash='test')
            db.session.add(admin)
            db.session.commit()
            
            # Login as admin using correct session key
            with client.session_transaction() as sess:
                sess['admin_id'] = admin.id
            
            # Test admin updates list
            response = client.get('/admin/updates')
            assert response.status_code == 200
            
            # Test admin new update form
            response = client.get('/admin/updates/new')
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'Expected Decision Date' in data
            assert 'Potential Impact' in data
            assert 'Decision Status' in data
            assert 'Change Type' in data
            assert 'Compliance Deadline' in data
            assert 'Affected Operators' in data
            
            # Test creating update through admin
            form_data = {
                'title': 'Admin Created Update',
                'description': 'Created through admin interface',
                'jurisdiction_affected': 'Admin Test City',
                'update_date': date.today().isoformat(),
                'status': 'Recent',
                'category': 'Regulatory Changes',
                'impact_level': 'High',
                'priority': '1',
                'action_required': 'False',
                'property_types': 'Both',
                'change_type': 'Recent',
                'expected_decision_date': (date.today() + timedelta(days=30)).isoformat(),
                'potential_impact': 'High impact through admin',
                'decision_status': 'Under Review',
                'compliance_deadline': (date.today() + timedelta(days=60)).isoformat(),
                'affected_operators': 'All operators via admin'
            }
            
            response = client.post('/admin/updates/new', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify the update was created with new fields
            updates = Update.query.filter_by(title='Admin Created Update').all()
            assert len(updates) == 1
            update = updates[0]
            assert update.potential_impact == 'High impact through admin'
            assert update.decision_status == 'Under Review'
            assert update.affected_operators == 'All operators via admin'

    def test_error_handling(self, app, client):
        """Test comprehensive error handling"""
        with app.app_context():
            # Test 404 for non-existent update
            response = client.get('/updates/99999')
            assert response.status_code == 404
            assert 'Page Not Found' in response.get_data(as_text=True)
            
            # Test 404 for non-existent regulation
            response = client.get('/regulations/99999')
            assert response.status_code == 404
            
            # Test invalid routes
            response = client.get('/updates/invalid-route')
            assert response.status_code == 404
            
            # Test API error handling
            response = client.get('/api/updates/99999')
            assert response.status_code == 404
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is False
            assert 'not found' in data['error'].lower()

    def test_update_management(self, app, client):
        """Test update management functionality with new fields"""
        with app.app_context():
            # Create test updates with different field values
            updates_data = [
                {
                    'title': 'High Priority Update',
                    'description': 'High priority test',
                    'jurisdiction_affected': 'City A',
                    'update_date': date.today(),
                    'status': 'Recent',
                    'category': 'Regulatory Changes',
                    'impact_level': 'High',
                    'priority': 1,
                    'change_type': 'Recent',
                    'decision_status': 'Under Review',
                    'potential_impact': 'High impact on operations'
                },
                {
                    'title': 'Medium Priority Update',
                    'description': 'Medium priority test',
                    'jurisdiction_affected': 'City B',
                    'update_date': date.today(),
                    'status': 'Proposed',
                    'category': 'Tax Updates',
                    'impact_level': 'Medium',
                    'priority': 2,
                    'change_type': 'Proposed',
                    'decision_status': 'Proposed',
                    'potential_impact': 'Medium impact on operations'
                }
            ]
            
            # Create the updates
            for update_data in updates_data:
                success, update, error = UpdateService.create_update(update_data)
                assert success, f"Setup failed: {error}"
            
            # Test basic update access
            response = client.get('/updates')
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'High Priority Update' in data
            assert 'Medium Priority Update' in data

    def test_responsive_design_elements(self, app, client):
        """Test that responsive design elements are present"""
        with app.app_context():
            # Test main updates page has responsive elements
            response = client.get('/updates')
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            
            # Check for Bootstrap responsive classes
            assert 'container-fluid' in data or 'container' in data
            assert 'row' in data
            assert 'col-' in data
            
            # Check for mobile-friendly meta tags in base template
            assert 'viewport' in data
            
            # Test admin pages have responsive elements
            with client.session_transaction() as sess:
                sess['admin_id'] = 1
            
            response = client.get('/admin/updates')
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'container' in data or 'container-fluid' in data

    def test_data_synchronization(self, app, client):
        """Test that data synchronizes properly between admin and public views"""
        with app.app_context():
            # Create update through service
            update_data = {
                'title': 'Sync Test Update',
                'description': 'Testing data synchronization',
                'jurisdiction_affected': 'Sync City',
                'update_date': date.today(),
                'status': 'Recent',
                'category': 'Regulatory Changes',
                'impact_level': 'High',
                'priority': 1,
                'change_type': 'Recent',
                'expected_decision_date': date.today() + timedelta(days=30),
                'potential_impact': 'Sync test impact',
                'decision_status': 'Under Review'
            }
            
            success, update, error = UpdateService.create_update(update_data)
            assert success, f"Setup failed: {error}"
            
            # Verify it appears in public view
            response = client.get('/updates')
            assert response.status_code == 200
            assert 'Sync Test Update' in response.get_data(as_text=True)
            
            # Verify it appears in admin view
            with client.session_transaction() as sess:
                sess['admin_id'] = 1
            
            response = client.get('/admin/updates')
            assert response.status_code == 200
            assert 'Sync Test Update' in response.get_data(as_text=True)
            
            # Update through admin interface
            form_data = {
                'title': 'Updated Sync Test',
                'description': 'Updated through admin',
                'jurisdiction_affected': 'Sync City',
                'update_date': date.today().isoformat(),
                'status': 'Recent',
                'category': 'Regulatory Changes',
                'impact_level': 'High',
                'priority': '1',
                'action_required': 'False',
                'property_types': 'Both',
                'change_type': 'Recent',
                'potential_impact': 'Updated sync test impact',
                'decision_status': 'Approved'
            }
            
            response = client.post(f'/admin/updates/{update.id}/edit', data=form_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify changes appear in public view
            response = client.get('/updates')
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'Updated Sync Test' in data
            assert 'Sync Test Update' not in data  # Old title should be gone

    def test_bulk_operations(self, app, client):
        """Test bulk operations functionality"""
        with app.app_context():
            # Create multiple test updates
            updates = []
            for i in range(3):
                update_data = {
                    'title': f'Bulk Test Update {i+1}',
                    'description': f'Bulk test description {i+1}',
                    'jurisdiction_affected': 'Bulk City',
                    'update_date': date.today(),
                    'status': 'Recent',
                    'category': 'Regulatory Changes',
                    'impact_level': 'Medium',
                    'priority': 2,
                    'change_type': 'Recent'
                }
                
                success, update, error = UpdateService.create_update(update_data)
                assert success, f"Setup failed: {error}"
                updates.append(update)
            
            # Login as admin
            with client.session_transaction() as sess:
                sess['admin_id'] = 1
            
            # Test bulk status change
            update_ids = [update.id for update in updates]
            response = client.post('/admin/updates/bulk-status-change',
                                 json={'update_ids': update_ids, 'new_status': 'Proposed'},
                                 content_type='application/json')
            assert response.status_code == 200
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            
            # Verify status changes
            for update in updates:
                db.session.refresh(update)
                assert update.status == 'Proposed'
                assert update.change_type == 'Proposed'
            
            # Test bulk delete
            response = client.post('/admin/updates/bulk-delete',
                                 json={'update_ids': update_ids},
                                 content_type='application/json')
            assert response.status_code == 200
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            
            # Verify deletions
            for update in updates:
                deleted_update = db.session.get(Update, update.id)
                assert deleted_update is None



    def test_csv_import_export(self, app, client):
        """Test CSV import and export functionality"""
        with app.app_context():
            # Login as admin
            with client.session_transaction() as sess:
                sess['admin_id'] = 1
            
            # Test CSV export
            response = client.get('/admin/updates/export-csv')
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
            
            # Test CSV import page
            response = client.get('/admin/updates/import-csv')
            assert response.status_code == 200
            data = response.get_data(as_text=True)
            assert 'CSV' in data
            assert 'import' in data.lower()
            assert 'upload' in data.lower() 