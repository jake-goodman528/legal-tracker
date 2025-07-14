#!/usr/bin/env python3
"""
Test script to make real form submissions to admin endpoints
"""

import requests
import re

# Base URL
BASE_URL = "http://localhost:9000"

def get_csrf_token(session, url):
    """Extract CSRF token from a form page"""
    response = session.get(url)
    # Look for csrf_token in the HTML
    match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', response.text)
    if match:
        return match.group(1)
    return None

def test_admin_login():
    """Login to admin interface"""
    session = requests.Session()
    
    # Get login page and CSRF token
    csrf_token = get_csrf_token(session, f"{BASE_URL}/admin/login")
    print(f"CSRF token: {csrf_token}")
    
    # Try to login with actual admin credentials
    login_data = {
        'csrf_token': csrf_token,
        'username': 'kaystreetmanagement',
        'password': 'LegalandComplianceTracker2001528'
    }
    
    response = session.post(f"{BASE_URL}/admin/login", data=login_data)
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200 and 'login' not in response.url:
        print("✅ Login successful")
        return session
    else:
        print("❌ Login failed")
        return None

def test_new_regulation_submission(session):
    """Test submitting a new regulation form"""
    print("\n=== Testing New Regulation Submission ===")
    
    # Get new regulation page
    csrf_token = get_csrf_token(session, f"{BASE_URL}/admin/regulations/new")
    
    if not csrf_token:
        print("❌ Could not get CSRF token")
        return
    
    # Prepare form data that should trigger the validation issue
    form_data = {
        'csrf_token': csrf_token,
        'jurisdiction': 'State',
        'jurisdiction_level': 'State',
        'location': 'California',  # This should cause "not a valid choice" if bug exists
        'title': 'Test Regulation for Location Bug',
        'overview': 'Testing location validation',
        'submit': 'Save Regulation'
    }
    
    print(f"Submitting form data: {form_data}")
    
    # Submit the form
    response = session.post(f"{BASE_URL}/admin/regulations/new", data=form_data)
    print(f"Response status: {response.status_code}")
    print(f"Response URL: {response.url}")
    
    # Check if there are validation errors in the response
    if 'not a valid choice' in response.text:
        print("❌ Found 'not a valid choice' error in response")
        return False
    elif 'created successfully' in response.text or response.url.endswith('/admin/regulations'):
        print("✅ Form submitted successfully")
        return True
    else:
        print("⚠️  Unexpected response - check logs for details")
        return False

def test_new_update_submission(session):
    """Test submitting a new update form"""
    print("\n=== Testing New Update Submission ===")
    
    # Get new update page
    csrf_token = get_csrf_token(session, f"{BASE_URL}/admin/updates/new")
    
    if not csrf_token:
        print("❌ Could not get CSRF token")
        return
    
    # Prepare form data that should trigger the validation issue
    form_data = {
        'csrf_token': csrf_token,
        'title': 'Test Update for Location Bug',
        'description': 'Testing location validation',
        'jurisdiction': 'Local',
        'jurisdiction_affected': 'Tampa',  # This should cause "not a valid choice" if bug exists
        'jurisdiction_level': 'Local',
        'update_date': '2024-01-15',
        'status': 'Recent',
        'category': 'Regulatory Changes',
        'impact_level': 'Medium',
        'action_required': 'False',
        'property_types': 'Both',
        'priority': '2',
        'change_type': 'Recent',
        'summary': 'Test summary',
        'submit': 'Save Update'
    }
    
    print(f"Submitting form data: {form_data}")
    
    # Submit the form
    response = session.post(f"{BASE_URL}/admin/updates/new", data=form_data)
    print(f"Response status: {response.status_code}")
    print(f"Response URL: {response.url}")
    
    # Check if there are validation errors in the response
    if 'not a valid choice' in response.text:
        print("❌ Found 'not a valid choice' error in response")
        return False
    elif 'created successfully' in response.text or response.url.endswith('/admin/updates'):
        print("✅ Form submitted successfully")
        return True
    else:
        print("⚠️  Unexpected response - check logs for details")
        return False

if __name__ == "__main__":
    print("Testing Form Submissions with Real HTTP Requests")
    print("=" * 60)
    
    # Login to admin
    session = test_admin_login()
    if not session:
        print("Cannot proceed without admin login")
        exit(1)
    
    # Test both forms
    regulation_success = test_new_regulation_submission(session)
    update_success = test_new_update_submission(session)
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"Regulation form: {'✅ PASSED' if regulation_success else '❌ FAILED'}")
    print(f"Update form: {'✅ PASSED' if update_success else '❌ FAILED'}")
    
    if regulation_success and update_success:
        print("🎉 All tests passed - location validation appears to be working!")
    else:
        print("🐛 Some tests failed - check application logs for debugging information")
    print("=" * 60) 