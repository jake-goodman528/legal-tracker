# STR Compliance Toolkit - API Documentation

## Overview

The STR Compliance Toolkit provides a comprehensive REST API for managing short-term rental compliance data. This API enables programmatic access to regulations, updates, search functionality, and user interactions.

**Base URL**: `http://localhost:5000`  
**API Version**: 2.0  
**Content-Type**: `application/json`

## Authentication

Currently, the API uses session-based authentication for user interactions and separate admin authentication for administrative endpoints.

### Admin Authentication
```http
POST /admin/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your-admin-password
```

## API Endpoints

### 🔍 Search & Regulations

#### Advanced Search
```http
GET /api/search/advanced
```

Perform advanced search across regulations with multiple criteria.

**Query Parameters:**
- `query` (string, optional): Text search query
- `categories` (array, optional): Filter by categories
- `compliance_levels` (array, optional): Filter by compliance levels  
- `property_types` (array, optional): Filter by property types
- `locations` (array, optional): Filter by locations
- `jurisdictions` (array, optional): Filter by jurisdiction levels
- `date_from` (string, optional): Start date (YYYY-MM-DD)
- `date_to` (string, optional): End date (YYYY-MM-DD)
- `date_range_days` (integer, optional): Days from current date

**Example Request:**
```http
GET /api/search/advanced?query=licensing&categories=Legal,Licensing&jurisdictions=State&locations=California
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "title": "California Short-Term Rental Licensing Requirements",
      "jurisdiction_level": "State",
      "location": "California",
      "category": "Licensing",
      "compliance_level": "Mandatory",
      "property_type": "Both",
      "key_requirements": "All STR properties must obtain state license...",
      "last_updated": "2024-01-15",
      "effective_date": "2024-03-01",
      "keywords": "licensing, permit, registration"
    }
  ],
  "total": 1
}
```

#### Search Suggestions
```http
GET /api/search/suggestions
```

Get intelligent search suggestions based on user input.

**Query Parameters:**
- `q` (string, required): Search query (minimum 2 characters)

**Example Request:**
```http
GET /api/search/suggestions?q=califor
```

**Response:**
```json
{
  "success": true,
  "suggestions": [
    {
      "text": "California",
      "type": "location",
      "category": "Locations"
    },
    {
      "text": "California Coastal Commission",
      "type": "title",
      "category": "Regulation Titles"
    }
  ]
}
```

#### Save Search Configuration
```http
POST /api/search/save
```

Save a search configuration for later reuse.

**Request Body:**
```json
{
  "name": "California Licensing Updates",
  "description": "Track licensing changes in California",
  "criteria": {
    "query": "licensing",
    "locations": ["California"],
    "categories": ["Legal", "Licensing"]
  },
  "is_public": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Search saved successfully",
  "search_id": 123
}
```

#### Get Saved Searches
```http
GET /api/search/saved
```

Retrieve all public saved searches.

**Response:**
```json
{
  "success": true,
  "searches": [
    {
      "id": 123,
      "name": "California Licensing Updates",
      "description": "Track licensing changes in California",
      "criteria": { "query": "licensing", "locations": ["California"] },
      "use_count": 5,
      "last_used": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Use Saved Search
```http
GET /api/search/saved/{search_id}
```

Execute a saved search and get its criteria.

**Response:**
```json
{
  "success": true,
  "criteria": {
    "query": "licensing",
    "locations": ["California"],
    "categories": ["Legal", "Licensing"]
  }
}
```

### 📈 Updates & Tracking

#### Search Updates
```http
GET /api/updates/search
```

Search and filter regulatory updates.

**Query Parameters:**
- `query_text` (string, optional): Text search
- `category` (string, optional): Category filter
- `impact` (string, optional): Impact level filter
- `status` (string, optional): Status filter
- `jurisdiction` (string, optional): Jurisdiction filter
- `has_deadline` (boolean, optional): Filter by deadline presence
- `action_required` (boolean, optional): Filter by action requirement

**Example Request:**
```http
GET /api/updates/search?category=Tax Updates&impact=High&has_deadline=true
```

**Response:**
```json
{
  "success": true,
  "updates": [
    {
      "id": 456,
      "title": "New Tourism Tax Requirements",
      "description": "Updated tax collection requirements for STR properties",
      "jurisdiction_affected": "San Francisco, CA",
      "status": "Recent",
      "category": "Tax Updates",
      "impact_level": "High",
      "deadline_date": "2024-03-15",
      "action_required": true,
      "action_description": "Update tax collection procedures",
      "priority": 1,
      "tags": ["tourism tax", "collection", "compliance"]
    }
  ]
}
```

#### Get User Bookmarks
```http
GET /api/updates/bookmarked
```

Retrieve user's bookmarked updates.

**Response:**
```json
{
  "success": true,
  "bookmarked_updates": [
    {
      "id": 456,
      "title": "New Tourism Tax Requirements",
      "bookmarked_at": "2024-01-10T14:30:00Z",
      "is_read": true,
      "deadline_date": "2024-03-15"
    }
  ]
}
```

#### Toggle Bookmark
```http
POST /api/updates/{update_id}/bookmark
```

Add or remove an update from user's bookmarks.

**Request Body:**
```json
{
  "is_bookmarked": true
}
```

**Response:**
```json
{
  "success": true,
  "is_bookmarked": true,
  "message": "Update bookmarked successfully"
}
```

#### Set Reminder
```http
POST /api/updates/{update_id}/reminder
```

Set a custom reminder for an update.

**Request Body:**
```json
{
  "reminder_date": "2024-02-15",
  "reminder_type": "custom",
  "email": "user@example.com",
  "notes": "Review before implementation"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reminder set successfully",
  "reminder_id": 789
}
```

### 🔔 Notifications

#### Get Notification Preferences
```http
GET /api/notifications/preferences
```

Retrieve user's notification preferences.

**Response:**
```json
{
  "success": true,
  "preferences": {
    "email": "user@example.com",
    "locations": ["California", "New York"],
    "categories": ["Legal", "Tax Updates"],
    "impact_levels": ["High", "Medium"],
    "notify_new_updates": true,
    "notify_deadlines": true,
    "notify_weekly_digest": false
  }
}
```

#### Update Notification Preferences
```http
POST /api/notifications/preferences
```

Update user's notification preferences.

**Request Body:**
```json
{
  "email": "user@example.com",
  "locations": ["California", "Texas"],
  "categories": ["Legal", "Licensing"],
  "impact_levels": ["High"],
  "notify_new_updates": true,
  "notify_deadlines": true,
  "notify_weekly_digest": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preferences updated successfully"
}
```

#### Get Urgent Alerts
```http
GET /api/notifications/alerts
```

Get urgent notifications for deadlines and high-priority updates.

**Response:**
```json
{
  "success": true,
  "alerts": [
    {
      "id": 456,
      "title": "New Tourism Tax Requirements",
      "type": "deadline",
      "urgency": "high",
      "deadline_date": "2024-02-15",
      "days_until_deadline": 3,
      "message": "Deadline approaching in 3 days"
    }
  ]
}
```

#### Generate Weekly Digest
```http
GET /api/notifications/weekly-digest
```

Generate a weekly digest of regulatory activity.

**Response:**
```json
{
  "success": true,
  "digest": {
    "period": "2024-01-08 to 2024-01-14",
    "total_updates": 12,
    "high_priority_updates": 3,
    "upcoming_deadlines": 2,
    "new_regulations": 1,
    "summary": "This week saw significant activity in tax regulations...",
    "updates_by_category": {
      "Tax Updates": 5,
      "Licensing Changes": 3,
      "Legal": 2,
      "Court Decisions": 2
    },
    "featured_updates": [
      {
        "id": 456,
        "title": "New Tourism Tax Requirements",
        "category": "Tax Updates",
        "impact_level": "High"
      }
    ]
  }
}
```

### 📊 Data Export

#### Export Search Results to CSV
```http
GET /api/export/csv
```

Export search results in CSV format.

**Query Parameters:**
- Same as `/api/search/advanced` parameters
- `format` (string): "csv" (default)

**Response:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="regulations_export.csv"

ID,Title,Jurisdiction Level,Location,Category,Compliance Level,Last Updated
1,"California STR Licensing",State,California,Licensing,Mandatory,2024-01-15
```

### 🛠 Administrative Endpoints

#### Get Dashboard Statistics
```http
GET /admin/api/statistics
```

Get administrative dashboard statistics.

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_regulations": 150,
    "total_updates": 89,
    "recent_updates": 12,
    "high_priority_updates": 5,
    "updates_by_category": {
      "Legal": 25,
      "Tax Updates": 20,
      "Licensing": 18
    },
    "regulations_by_jurisdiction": {
      "National": 15,
      "State": 75,
      "Local": 60
    }
  }
}
```

#### Create Regulation
```http
POST /admin/api/regulations
```

Create a new regulation record.

**Request Body:**
```json
{
  "jurisdiction_level": "State",
  "location": "California",
  "title": "New STR Registration Requirements",
  "key_requirements": "All STR properties must register with state agency...",
  "category": "Legal",
  "compliance_level": "Mandatory",
  "property_type": "Both",
  "effective_date": "2024-06-01",
  "keywords": "registration, permit, state"
}
```

**Response:**
```json
{
  "success": true,
  "regulation": {
    "id": 151,
    "title": "New STR Registration Requirements",
    "jurisdiction_level": "State",
    "location": "California"
  },
  "message": "Regulation created successfully"
}
```

#### Update Regulation
```http
PUT /admin/api/regulations/{regulation_id}
```

Update an existing regulation.

**Request Body:**
```json
{
  "title": "Updated STR Registration Requirements",
  "key_requirements": "Updated requirements text...",
  "last_updated": "2024-01-20"
}
```

**Response:**
```json
{
  "success": true,
  "regulation": {
    "id": 151,
    "title": "Updated STR Registration Requirements"
  },
  "message": "Regulation updated successfully"
}
```

#### Delete Regulation
```http
DELETE /admin/api/regulations/{regulation_id}
```

Delete a regulation record.

**Response:**
```json
{
  "success": true,
  "message": "Regulation deleted successfully"
}
```

## Error Handling

All API endpoints return consistent error responses:

### Error Response Format
```json
{
  "success": false,
  "error": "Error message description",
  "code": "ERROR_CODE"
}
```

### Common HTTP Status Codes
- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters or request format
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

### Common Error Codes
- `INVALID_PARAMETERS`: Missing or invalid request parameters
- `UNAUTHORIZED`: Authentication required
- `NOT_FOUND`: Requested resource not found
- `DUPLICATE_ENTRY`: Attempting to create duplicate resource
- `DATABASE_ERROR`: Database operation failed

## Rate Limiting

API requests are currently not rate-limited but this may be implemented in future versions for production deployments.

## Data Formats

### Date Format
All dates are in ISO 8601 format: `YYYY-MM-DD`

### DateTime Format  
All timestamps are in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

### Boolean Values
Boolean parameters accept: `true`, `false`, `1`, `0`

## Examples

### Complete Search Workflow
```bash
# 1. Get search suggestions
curl "http://localhost:5000/api/search/suggestions?q=tax"

# 2. Perform advanced search
curl "http://localhost:5000/api/search/advanced?query=tax&categories=Tax%20Updates&jurisdictions=State"

# 3. Save search for later
curl -X POST "http://localhost:5000/api/search/save" \
  -H "Content-Type: application/json" \
  -d '{"name": "Tax Updates", "criteria": {"query": "tax", "categories": ["Tax Updates"]}}'

# 4. Export results to CSV
curl "http://localhost:5000/api/export/csv?query=tax&categories=Tax%20Updates" \
  -H "Accept: text/csv"
```

### Update Tracking Workflow
```bash
# 1. Search for updates
curl "http://localhost:5000/api/updates/search?category=Tax%20Updates&impact=High"

# 2. Bookmark important update
curl -X POST "http://localhost:5000/api/updates/456/bookmark" \
  -H "Content-Type: application/json" \
  -d '{"is_bookmarked": true}'

# 3. Set reminder for deadline
curl -X POST "http://localhost:5000/api/updates/456/reminder" \
  -H "Content-Type: application/json" \
  -d '{"reminder_date": "2024-02-15", "email": "user@example.com"}'

# 4. Get bookmarked updates
curl "http://localhost:5000/api/updates/bookmarked"
```

### Notification Management
```bash
# 1. Get current preferences
curl "http://localhost:5000/api/notifications/preferences"

# 2. Update preferences
curl -X POST "http://localhost:5000/api/notifications/preferences" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "locations": ["California"], "notify_deadlines": true}'

# 3. Check for urgent alerts
curl "http://localhost:5000/api/notifications/alerts"

# 4. Get weekly digest
curl "http://localhost:5000/api/notifications/weekly-digest"
```

## SDKs and Integration

### JavaScript/Node.js Example
```javascript
// Search for regulations
const searchRegulations = async (query, filters = {}) => {
  const params = new URLSearchParams({ query, ...filters });
  const response = await fetch(`/api/search/advanced?${params}`);
  return response.json();
};

// Bookmark an update
const bookmarkUpdate = async (updateId, isBookmarked) => {
  const response = await fetch(`/api/updates/${updateId}/bookmark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_bookmarked: isBookmarked })
  });
  return response.json();
};
```

### Python Example
```python
import requests

class STRComplianceAPI:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def search_regulations(self, query, **filters):
        params = {"query": query, **filters}
        response = self.session.get(f"{self.base_url}/api/search/advanced", params=params)
        return response.json()
    
    def bookmark_update(self, update_id, is_bookmarked):
        data = {"is_bookmarked": is_bookmarked}
        response = self.session.post(f"{self.base_url}/api/updates/{update_id}/bookmark", json=data)
        return response.json()
```

## Changelog

### Version 2.0.0 (Current)
- Complete API redesign with RESTful endpoints
- Enhanced search capabilities with advanced filtering
- User interaction tracking (bookmarks, reminders)
- Comprehensive notification system
- CSV export functionality
- Improved error handling and documentation

### Version 1.0.0 (Legacy)
- Basic regulation retrieval endpoints
- Simple search functionality
- Limited admin interface

---

**For support and questions, please contact the development team or refer to the main README.md documentation.** 