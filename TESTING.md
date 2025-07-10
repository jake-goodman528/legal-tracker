# STR Compliance Toolkit - Testing Guide

## 🧪 Overview

The STR Compliance Toolkit includes a comprehensive testing suite built with pytest to ensure code quality, reliability, and proper functionality. This guide covers test setup, execution, and development practices.

## 📋 Test Categories

### Unit Tests
- **SearchService**: Advanced search functionality, suggestions, saved searches
- **RegulationService**: CRUD operations, filtering, content generation
- **UpdateService**: Update management and filtering
- **UserInteractionService**: Bookmarks, reminders, session management
- **NotificationService**: Alert generation and preferences

### Integration Tests
- **API Endpoints**: REST API functionality and error handling
- **Database Operations**: Model interactions and transactions
- **Service Layer Integration**: Cross-service functionality

### End-to-End Tests
- **Web Interface**: Full user workflows
- **Admin Interface**: Administrative operations
- **Export Functionality**: CSV generation and downloads

## 🚀 Quick Start

### Prerequisites
```bash
# Install testing dependencies
python3 -m pip install pytest pytest-flask pytest-cov

# Or install from requirements.txt
python3 -m pip install -r requirements.txt
```

### Running Tests

#### Run All Tests
```bash
python3 -m pytest
```

#### Run with Coverage Report
```bash
python3 -m pytest --cov=app --cov=models --cov-report=html --cov-report=term
```

#### Run Specific Test Categories
```bash
# Unit tests only
python3 -m pytest -m unit

# API tests only
python3 -m pytest -m api

# Integration tests only
python3 -m pytest -m integration
```

#### Run Specific Test Files
```bash
# Search service tests
python3 -m pytest tests/test_search_service.py

# API endpoint tests
python3 -m pytest tests/test_api_endpoints.py
```

#### Run Single Test
```bash
python3 -m pytest tests/test_search_service.py::TestSearchService::test_advanced_search_text_query -v
```

### Using the Test Runner Script
```bash
# Run all tests with coverage
python3 run_tests.py --coverage --verbose

# Run only unit tests
python3 run_tests.py --type unit

# Run API tests only
python3 run_tests.py --type api
```

## 🏗 Test Architecture

### Test Configuration (`conftest.py`)
The test configuration provides:
- **Isolated Test Database**: Temporary SQLite database for each test session
- **Flask App Factory**: Configured Flask application for testing
- **Test Fixtures**: Pre-populated test data (regulations, updates, users)
- **Authentication Helpers**: Authenticated admin sessions

### Key Test Fixtures

#### Application Fixtures
```python
@pytest.fixture
def app():
    """Create and configure test Flask application"""
    
@pytest.fixture
def client(app):
    """Create test client for HTTP requests"""
    
@pytest.fixture
def authenticated_admin(client, admin_user):
    """Provide authenticated admin session"""
```

#### Data Fixtures
```python
@pytest.fixture
def sample_regulation(app):
    """Create single regulation for testing"""
    
@pytest.fixture
def multiple_regulations(app):
    """Create multiple regulations for search/filter testing"""
    
@pytest.fixture
def sample_update(app):
    """Create single update for testing"""
    
@pytest.fixture
def notification_preferences(app):
    """Create notification preferences for testing"""
```

### Test Environment Configuration

Tests automatically configure environment variables:
```bash
TESTING=True
SKIP_SAMPLE_DATA=True          # Disable sample data loading
SESSION_SECRET=test-secret-key
ADMIN_PASSWORD=test-admin-password
WTF_CSRF_ENABLED=False         # Disable CSRF for testing
```

## 📝 Test Examples

### Unit Test Example
```python
def test_advanced_search_text_query(self, app, multiple_regulations):
    """Test advanced search with text query."""
    with app.app_context():
        # Test search for "tax" - should find Federal STR Tax Reporting
        results = SearchService.advanced_search({'query': 'tax'})
        
        assert len(results) == 1
        assert results[0].title == 'Federal STR Tax Reporting'
        assert results[0].category == 'Taxes'
```

### API Test Example
```python
def test_advanced_search_api(self, client, multiple_regulations):
    """Test the advanced search API endpoint."""
    response = client.get('/api/search/advanced?query=tax&jurisdictions=National')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['results']) == 1
    assert data['results'][0]['title'] == 'Federal STR Tax Reporting'
```

### Integration Test Example
```python
def test_bookmark_workflow(self, client, sample_update):
    """Test complete bookmark workflow."""
    # Bookmark an update
    response = client.post(f'/api/updates/{sample_update.id}/bookmark',
                          json={'is_bookmarked': True})
    assert response.status_code == 200
    
    # Verify bookmark appears in bookmarked list
    response = client.get('/api/updates/bookmarked')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['bookmarked_updates']) >= 1
```

## 🔧 Writing New Tests

### Test Organization
```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_search_service.py   # SearchService unit tests
├── test_regulation_service.py # RegulationService unit tests
├── test_api_endpoints.py    # API endpoint tests
├── test_admin_routes.py     # Admin interface tests
└── test_integration.py     # Cross-system integration tests
```

### Test Naming Conventions
- **Test Files**: `test_*.py`
- **Test Classes**: `Test*` (e.g., `TestSearchService`)
- **Test Methods**: `test_*` (e.g., `test_advanced_search_filters`)

### Test Structure Best Practices

#### Arrange-Act-Assert Pattern
```python
def test_save_search_success(self, app):
    """Test successfully saving a search configuration."""
    with app.app_context():
        # Arrange
        criteria = {
            'query': 'licensing',
            'categories': ['Legal', 'Licensing'],
            'jurisdictions': ['State']
        }
        
        # Act
        success, message, search_id = SearchService.save_search(
            'Test Search', 
            'Test search description', 
            criteria,
            is_public=True
        )
        
        # Assert
        assert success is True
        assert 'successfully' in message
        assert search_id is not None
```

#### Test Data Isolation
- Use fixtures for test data creation
- Each test gets fresh database state
- No dependencies between tests

#### Error Testing
```python
def test_search_error_handling(self, app):
    """Test that search methods handle errors gracefully."""
    with app.app_context():
        # Test with invalid data types
        results = SearchService.advanced_search({'query': None})
        assert isinstance(results, list)  # Should return empty list, not crash
```

### Adding Test Markers
```python
import pytest

@pytest.mark.unit
def test_unit_functionality():
    """Unit test for isolated functionality"""
    pass

@pytest.mark.api
def test_api_endpoint():
    """API endpoint test"""
    pass

@pytest.mark.slow
def test_long_running_operation():
    """Test that takes significant time"""
    pass
```

## 📊 Coverage Reporting

### Generating Coverage Reports
```bash
# HTML coverage report
python3 -m pytest --cov=app --cov=models --cov-report=html

# Terminal coverage report
python3 -m pytest --cov=app --cov=models --cov-report=term

# Coverage with missing lines
python3 -m pytest --cov=app --cov=models --cov-report=term-missing
```

### Coverage Targets
- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Components**: 95%+ (security, data integrity)

### Viewing Coverage Reports
After running with `--cov-report=html`:
```bash
open htmlcov/index.html  # macOS
# or visit file:///path/to/project/htmlcov/index.html
```

## 🐛 Debugging Tests

### Verbose Output
```bash
python3 -m pytest -v  # Verbose test names
python3 -m pytest -vv # Very verbose with test docstrings
```

### Debug Output
```bash
python3 -m pytest -s  # Show print statements
python3 -m pytest --tb=long  # Long traceback format
python3 -m pytest --pdb  # Drop into debugger on failure
```

### Common Debugging Techniques
```python
def test_debug_example(self, app, sample_data):
    """Example of debugging techniques in tests."""
    with app.app_context():
        # Print debugging
        print(f"Sample data: {sample_data}")
        
        # Assert with detailed messages
        result = some_operation()
        assert result is not None, f"Expected result, got None with data: {sample_data}"
        
        # Use pytest's built-in debugging
        import pytest
        pytest.set_trace()  # Debugger breakpoint
```

## ⚠️ Known Test Issues

### Current Test Status
- **Total Tests**: 25 implemented
- **Passing**: 19 (76%)
- **Failing**: 6 (24%)

### Common Issues and Solutions

#### SQLAlchemy Session Issues
**Problem**: `DetachedInstanceError` when accessing model attributes
```python
# Solution: Access attributes within app context
with app.app_context():
    db.session.add(model_instance)
    # Access attributes here
    name = model_instance.name
```

#### Fixture Scope Issues
**Problem**: Fixtures not properly isolated between tests
```python
# Solution: Use function-scoped fixtures
@pytest.fixture(scope="function")
def isolated_data():
    # Fresh data for each test
    pass
```

#### Date/Time Sensitivity
**Problem**: Tests failing due to time-dependent data
```python
# Solution: Use fixed dates in test data
from datetime import date
test_date = date(2024, 1, 15)  # Fixed date for consistency
```

## 🔒 Security Testing

### Authentication Tests
```python
def test_admin_routes_protected(self, client):
    """Test that admin routes require authentication."""
    protected_routes = ['/admin/dashboard', '/admin/regulations']
    
    for route in protected_routes:
        response = client.get(route)
        assert response.status_code == 302  # Redirect to login
```

### Input Validation Tests
```python
def test_sql_injection_protection(self, client):
    """Test basic SQL injection protection."""
    malicious_query = "'; DROP TABLE regulation; --"
    
    response = client.get(f'/api/search/advanced?query={malicious_query}')
    assert response.status_code == 200  # Should handle gracefully
```

### CSRF Protection Tests
```python
def test_csrf_protection_in_production(self, app):
    """Test CSRF protection is enabled in production."""
    if not app.config.get('TESTING'):
        # CSRF should be enabled in production
        assert app.config.get('WTF_CSRF_ENABLED', True)
```

## 🚀 Continuous Integration

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: python3 -m pytest --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python3 -m pytest
        language: system
        pass_filenames: false
        always_run: true
```

## 📈 Performance Testing

### Load Testing Example
```python
import time

def test_search_performance(self, app, large_dataset):
    """Test search performance with large dataset."""
    with app.app_context():
        start_time = time.time()
        results = SearchService.advanced_search({'query': 'test'})
        duration = time.time() - start_time
        
        assert duration < 1.0  # Should complete within 1 second
        assert len(results) > 0
```

### Memory Testing
```python
import psutil
import os

def test_memory_usage(self, app):
    """Test memory usage during operations."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    with app.app_context():
        # Perform memory-intensive operation
        large_operation()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert reasonable memory usage
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB increase
```

## 🔄 Test Maintenance

### Regular Test Reviews
- **Monthly**: Review failing tests and update fixtures
- **Quarterly**: Update test dependencies and pytest version
- **Release**: Full test suite execution with coverage analysis

### Test Data Management
- Keep test data minimal but representative
- Update test data when models change
- Document test scenarios in docstrings

### Deprecation Handling
```python
import warnings

def test_deprecated_functionality():
    """Test deprecated functionality with proper warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Call deprecated function
        deprecated_function()
        
        # Verify warning was raised
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
```

## 📚 Additional Resources

### Testing Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [Flask Testing Guide](https://flask.palletsprojects.com/en/2.0.x/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

### Best Practices
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://testdriven.io/)
- [Testing Pyramid Concept](https://martinfowler.com/articles/practical-test-pyramid.html)

---

**For questions about testing or to report test issues, please contact the development team.** 