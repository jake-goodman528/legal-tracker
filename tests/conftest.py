"""
Test Configuration and Fixtures

Provides shared test fixtures and configuration for the STR Compliance Toolkit test suite.
"""

import os
import tempfile
import pytest
from datetime import datetime, date
from app.application import create_app
from models import db, Regulation, Update, AdminUser, SavedSearch, NotificationPreference


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    # Set test environment variables
    os.environ['TESTING'] = 'True'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['SESSION_SECRET'] = 'test-secret-key'
    os.environ['ADMIN_PASSWORD'] = 'test-admin-password'
    os.environ['WTF_CSRF_ENABLED'] = 'False'
    os.environ['SKIP_SAMPLE_DATA'] = 'True'  # Skip sample data loading in tests
    
    # Create test app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application."""
    return app.test_cli_runner()


@pytest.fixture
def sample_regulation(app):
    """Create a sample regulation for testing."""
    with app.app_context():
        regulation = Regulation(
            jurisdiction_level='State',
            location='California',
            title='Test STR Licensing Requirements',
            key_requirements='All STR properties must obtain a license from the state.',
            last_updated=date(2024, 1, 15),
            category='Licensing',
            compliance_level='Mandatory',
            property_type='Both',
            effective_date=date(2024, 3, 1),
            keywords='licensing, permit, registration'
        )
        db.session.add(regulation)
        db.session.commit()
        return regulation


@pytest.fixture
def sample_update(app):
    """Create a sample update for testing."""
    with app.app_context():
        update = Update(
            title='New Tax Requirements for STR',
            description='Updated tax collection requirements for short-term rentals.',
            jurisdiction_affected='San Francisco, CA',
            update_date=date(2024, 1, 10),
            status='Recent',
            category='Tax Updates',
            impact_level='High',
            effective_date=date(2024, 2, 1),
            deadline_date=date(2024, 3, 15),
            action_required=True,
            action_description='Update tax collection procedures',
            property_types='Both',
            tags='tax, collection, compliance',
            priority=1
        )
        db.session.add(update)
        db.session.commit()
        return update


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        from werkzeug.security import generate_password_hash
        admin = AdminUser(
            username='testadmin',
            password_hash=generate_password_hash('testpassword')
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def saved_search(app):
    """Create a saved search for testing."""
    with app.app_context():
        search = SavedSearch(
            name='California Licensing',
            description='Track licensing changes in California',
            is_public=True
        )
        search.set_search_criteria({
            'query': 'licensing',
            'locations': ['California'],
            'categories': ['Licensing']
        })
        db.session.add(search)
        db.session.commit()
        return search


@pytest.fixture
def notification_preferences(app):
    """Create notification preferences for testing."""
    with app.app_context():
        prefs = NotificationPreference(
            user_session='test-session-123',
            email='test@example.com',
            locations='California,New York',
            categories='Legal,Tax Updates',
            impact_levels='High,Medium',
            notify_new_updates=True,
            notify_deadlines=True,
            notify_weekly_digest=False
        )
        db.session.add(prefs)
        db.session.commit()
        return prefs


@pytest.fixture
def authenticated_admin(client, admin_user):
    """Provide an authenticated admin session."""
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_username'] = admin_user.username
    return client


@pytest.fixture
def multiple_regulations(app):
    """Create multiple regulations for testing search and filtering."""
    with app.app_context():
        regulations = [
            Regulation(
                jurisdiction_level='National',
                location='United States',
                title='Federal STR Tax Reporting',
                key_requirements='Report STR income to IRS',
                last_updated=date(2024, 1, 1),
                category='Taxes',
                compliance_level='Mandatory',
                property_type='Both',
                keywords='tax, federal, reporting'
            ),
            Regulation(
                jurisdiction_level='State',
                location='Texas',
                title='Texas STR Registration',
                key_requirements='Register with state tourism board',
                last_updated=date(2024, 1, 5),
                category='Registration',
                compliance_level='Mandatory',
                property_type='Residential',
                keywords='registration, tourism, permit'
            ),
            Regulation(
                jurisdiction_level='Local',
                location='Austin, TX',
                title='Austin STR Zoning Requirements',
                key_requirements='Comply with local zoning restrictions',
                last_updated=date(2024, 1, 10),
                category='Zoning',
                compliance_level='Mandatory',
                property_type='Both',
                keywords='zoning, local, restrictions'
            )
        ]
        
        for regulation in regulations:
            db.session.add(regulation)
        db.session.commit()
        return regulations


@pytest.fixture
def multiple_updates(app):
    """Create multiple updates for testing search and filtering."""
    with app.app_context():
        updates = [
            Update(
                title='California Tourism Tax Changes',
                description='New tourism tax rates effective next quarter',
                jurisdiction_affected='California',
                update_date=date(2024, 1, 15),
                status='Recent',
                category='Tax Updates',
                impact_level='High',
                deadline_date=date(2024, 4, 1),
                action_required=True,
                priority=1
            ),
            Update(
                title='New York Licensing Updates',
                description='Updated licensing requirements for NYC',
                jurisdiction_affected='New York',
                update_date=date(2024, 1, 12),
                status='Recent',
                category='Licensing Changes',
                impact_level='Medium',
                action_required=False,
                priority=2
            ),
            Update(
                title='Federal Court Decision on STR',
                description='Supreme Court ruling affects all jurisdictions',
                jurisdiction_affected='United States',
                update_date=date(2024, 1, 8),
                status='Recent',
                category='Court Decisions',
                impact_level='High',
                action_required=False,
                priority=1
            )
        ]
        
        for update in updates:
            db.session.add(update)
        db.session.commit()
        return updates 