# STR Compliance Toolkit - API Documentation

## Overview

The STR Compliance Toolkit provides a comprehensive REST API for managing short-term rental compliance data. This API enables programmatic access to regulations, updates, and user interactions.

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



### 📈 Updates & Tracking



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





### 📊 Data Export

#### Export Regulations to CSV
```http
GET /api/export/csv
```

Export regulations database in CSV format.
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

### Update Tracking Workflow
```bash
# 1. Get all updates
curl "http://localhost:5000/api/updates"

# 2. Bookmark important update
curl -X POST "http://localhost:5000/api/updates/456/bookmark" \
  -H "Content-Type: application/json" \
  -d '{"is_bookmarked": true}'

# 3. Get bookmarked updates
curl "http://localhost:5000/api/updates/bookmarked"
```

## SDKs and Integration

### JavaScript/Node.js Example
```javascript
// Get all updates
const getUpdates = async () => {
  const response = await fetch('/api/updates');
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
    
    def get_updates(self):
        response = self.session.get(f"{self.base_url}/api/updates")
        return response.json()
    
    def bookmark_update(self, update_id, is_bookmarked):
        data = {"is_bookmarked": is_bookmarked}
        response = self.session.post(f"{self.base_url}/api/updates/{update_id}/bookmark", json=data)
        return response.json()
```

## Changelog

### Version 2.0.0 (Current)
- Complete API redesign with RESTful endpoints
- Comprehensive regulation and update management
- User interaction tracking (bookmarks, reminders)
- Comprehensive notification system
- CSV export functionality
- Improved error handling and documentation

### Version 1.0.0 (Legacy)
- Basic regulation retrieval endpoints
- Basic regulation browsing
- Limited admin interface

---

**For support and questions, please contact the development team or refer to the main README.md documentation.** 