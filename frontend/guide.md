# Frontend Integration Guide

This guide provides comprehensive documentation for integrating a frontend application with the Lost & Found API backend.

## Table of Contents

1. [Base Configuration](#base-configuration)
2. [Authentication](#authentication)
3. [User Endpoints](#user-endpoints)
4. [Item Management](#item-management)
5. [Match Management](#match-management)
6. [Admin Endpoints](#admin-endpoints)
7. [File Uploads](#file-uploads)
8. [Error Handling](#error-handling)
9. [Real-time Updates](#real-time-updates)
10. [Best Practices](#best-practices)

---

## Base Configuration

### API Base URL

```
Development: http://localhost:8000
Production: [Your production URL]
```

### API Documentation

- **Swagger UI**: `{base_url}/docs`
- **ReDoc**: `{base_url}/redoc`
- **OpenAPI Schema**: `{base_url}/openapi.json`

### Content Types

- **JSON**: `application/json` (for request/response bodies)
- **Form Data**: `multipart/form-data` (for file uploads)
- **Authorization**: `Bearer {token}` (in Authorization header)

---

## Authentication

### Overview

The API uses JWT (JSON Web Tokens) for authentication. There are two types of tokens:
- **Access Token**: Short-lived (default: 60 minutes), used for API requests
- **Refresh Token**: Long-lived (default: 7 days), used to obtain new access tokens

### Registration

**Endpoint**: `POST /auth/register`

**Request Body**:
```json
{
  "name": "John Doe",
  "email": "john.doe@university.edu",
  "password": "securepassword123",
  "roll_number": "2024CS001",
  "hostel": "Hostel A",  // Optional
  "contact_number": "+1234567890"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john.doe@university.edu",
  "roll_number": "2024CS001",
  "hostel": "Hostel A",
  "contact_number": "+1234567890",
  "role": "USER",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses**:
- `409 Conflict`: Email or roll number already registered
- `422 Unprocessable Entity`: Validation errors

### Login

**Endpoint**: `POST /auth/login`

**Request Body**:
```json
{
  "email": "john.doe@university.edu",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid email or password
- `422 Unprocessable Entity`: Validation errors

### Token Refresh

**Endpoint**: `POST /auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "new_access_token...",
  "refresh_token": "new_refresh_token...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token

### Using Tokens

Include the access token in the `Authorization` header for all protected endpoints:

```
Authorization: Bearer {access_token}
```

**Token Storage Recommendations**:
- Store tokens securely (e.g., `localStorage`, `sessionStorage`, or secure HTTP-only cookies)
- Implement automatic token refresh before expiration
- Clear tokens on logout

---

## User Endpoints

### Get Current User

**Endpoint**: `GET /users/me`

**Authentication**: Required (Bearer token)

**Response** (200 OK):
```json
{
  "id": "uuid",
  "name": "John Doe",
  "email": "john.doe@university.edu",
  "roll_number": "2024CS001",
  "hostel": "Hostel A",
  "contact_number": "+1234567890",
  "role": "USER",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token

---

## Item Management

### Report Lost Item

**Endpoint**: `POST /items/report_lost`

**Authentication**: Required (Bearer token)

**Request**: `multipart/form-data`
- `description` (string, required): Description of the lost item
- `location` (string, required): Location where item was lost
- `image` (file, optional): Image of the lost item (JPEG, PNG, or WebP, max 5MB)

**Example Request** (using FormData):
```javascript
const formData = new FormData();
formData.append('description', 'Black leather wallet with ID card');
formData.append('location', 'Library');
formData.append('image', imageFile); // Optional

fetch('/items/report_lost', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "status": "LOST",
  "description": "Black leather wallet with ID card",
  "location": "Library",
  "image_url": "/static/uploads/...",
  "is_active": true,
  "is_admin_report": false,
  "reported_at": "2024-01-01T00:00:00Z",
  "reported_by": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john.doe@university.edu",
    "contact_number": "+1234567890"
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: Validation errors

### Report Found Item

**Endpoint**: `POST /items/report_found`

**Authentication**: Required (Bearer token)

**Request**: `multipart/form-data`
- `description` (string, required): Description of the found item
- `location` (string, required): Location where item was found
- `image` (file, **required**): Image of the found item (JPEG, PNG, or WebP, max 5MB)

**Response** (201 Created): Same format as Report Lost Item, with `status: "FOUND"`

**Error Responses**:
- `400 Bad Request`: Image is required for found items
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: Validation errors

### List All Found Items

**Endpoint**: `GET /items/all_found_items`

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `location` (string, optional): Filter by location (case-insensitive partial match)
- `date_after` (datetime, optional): Filter items reported after this date (ISO 8601)
- `date_before` (datetime, optional): Filter items reported before this date (ISO 8601)

**Example**:
```
GET /items/all_found_items?location=Library&date_after=2024-01-01T00:00:00Z
```

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "status": "FOUND",
    "description": "Black leather wallet",
    "location": "Library",
    "image_url": "/static/uploads/...",
    "is_active": true,
    "is_admin_report": false,
    "reported_at": "2024-01-01T00:00:00Z",
    "reported_by": {
      "id": "uuid",
      "name": "Jane Smith",
      "email": "jane.smith@university.edu",
      "contact_number": "+1234567891"
    }
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token

### Search Items

**Endpoint**: `GET /items/search`

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `q` (string, required, min 2 chars): Search query (searches in description and location)
- `status` (enum, optional): Filter by status (`LOST` or `FOUND`)

**Example**:
```
GET /items/search?q=wallet&status=FOUND
```

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "status": "FOUND",
    "description": "Black leather wallet",
    "location": "Library",
    "image_url": "/static/uploads/...",
    "is_active": true,
    "is_admin_report": false,
    "reported_at": "2024-01-01T00:00:00Z",
    "similarity_score": null
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `422 Unprocessable Entity`: Query too short or invalid status

### Resolve Item

**Endpoint**: `POST /items/{item_id}/resolve`

**Authentication**: Required (Bearer token)

**Description**: Manually mark an item as resolved (archives it). Users can only resolve their own items.

**Response** (200 OK):
```json
{
  "id": "uuid",
  "status": "LOST",
  "description": "Black leather wallet",
  "location": "Library",
  "image_url": "/static/uploads/...",
  "is_active": false,  // Now archived
  "is_admin_report": false,
  "reported_at": "2024-01-01T00:00:00Z",
  "reported_by": { ... }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not the owner of the item
- `404 Not Found`: Item not found

---

## Match Management

### Get My Matches

**Endpoint**: `GET /matches/my_matches`

**Authentication**: Required (Bearer token)

**Description**: Returns all pending matches where the current user is the owner of the lost item.

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "lost_item_id": "uuid",
    "found_item_id": "uuid",
    "confidence_score": 0.85,
    "match_status": "PENDING",
    "created_at": "2024-01-01T00:00:00Z",
    "lost_item": {
      "id": "uuid",
      "status": "LOST",
      "description": "Black leather wallet",
      "location": "Library",
      "image_url": "/static/uploads/...",
      "is_active": true,
      "is_admin_report": false,
      "reported_at": "2024-01-01T00:00:00Z",
      "reported_by": { ... }
    },
    "found_item": {
      "id": "uuid",
      "status": "FOUND",
      "description": "Black wallet found",
      "location": "Cafeteria",
      "image_url": "/static/uploads/...",
      "is_active": true,
      "is_admin_report": false,
      "reported_at": "2024-01-01T01:00:00Z",
      "reported_by": { ... }
    }
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token

### Approve Match

**Endpoint**: `POST /matches/{match_id}/approve`

**Authentication**: Required (Bearer token)

**Description**: Approve a pending match. This will:
1. Set match status to `APPROVED`
2. Archive both items (`is_active = false`)
3. Send notifications to both parties with contact information

**Response** (200 OK):
```json
{
  "match": {
    "id": "uuid",
    "lost_item_id": "uuid",
    "found_item_id": "uuid",
    "confidence_score": 0.85,
    "match_status": "APPROVED",
    "created_at": "2024-01-01T00:00:00Z",
    "lost_item": { ... },
    "found_item": { ... }
  },
  "message": "Match approved and items archived",
  "contact_shared_with_loser": {
    "name": "Jane Smith",
    "email": "jane.smith@university.edu",
    "contact_number": "+1234567891"
  },
  "contact_shared_with_finder": {
    "name": "John Doe",
    "email": "john.doe@university.edu",
    "contact_number": "+1234567890"
  }
}
```

**Note**: If either item is an admin report, the contact will be:
```json
{
  "name": "Campus Admin Office",
  "email": "admin-office@university.local",
  "contact_number": "000-000-0000"
}
```

**Error Responses**:
- `400 Bad Request`: Match already resolved
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not authorized to approve this match (not the owner)
- `404 Not Found`: Match not found

### Reject Match

**Endpoint**: `POST /matches/{match_id}/reject`

**Authentication**: Required (Bearer token)

**Description**: Reject a pending match. Sets match status to `REJECTED`.

**Response** (200 OK):
```json
{
  "id": "uuid",
  "lost_item_id": "uuid",
  "found_item_id": "uuid",
  "confidence_score": 0.65,
  "match_status": "REJECTED",
  "created_at": "2024-01-01T00:00:00Z",
  "lost_item": { ... },
  "found_item": { ... }
}
```

**Error Responses**:
- `400 Bad Request`: Match already resolved
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not authorized to reject this match
- `404 Not Found`: Match not found

---

## Admin Endpoints

All admin endpoints require the user to have `role: "ADMIN"`.

### Report Item on Behalf of User

**Endpoint**: `POST /admin/report_on_behalf`

**Authentication**: Required (Admin Bearer token)

**Request**: `multipart/form-data`
- `user_identifier` (string, required): Email or roll number of the user
- `item_status` (enum, required): `LOST` or `FOUND`
- `description` (string, required): Description of the item
- `location` (string, required): Location
- `image` (file, optional for LOST, required for FOUND): Image file

**Response** (201 Created): Same format as regular item report, with `is_admin_report: true`

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not an admin
- `404 Not Found`: User not found
- `422 Unprocessable Entity`: Validation errors

### Report Office Found Item

**Endpoint**: `POST /admin/report_office_item`

**Authentication**: Required (Admin Bearer token)

**Request**: `multipart/form-data`
- `item_status` (enum, required): Must be `FOUND`
- `description` (string, required): Description of the item
- `location` (string, required): Location
- `image` (file, required): Image file

**Description**: Reports a found item on behalf of the admin office. The item is linked to the admin's user account but marked as `is_admin_report: true`.

**Response** (201 Created): Same format as regular item report, with `is_admin_report: true`

**Error Responses**:
- `400 Bad Request`: Item status must be FOUND
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not an admin
- `422 Unprocessable Entity`: Validation errors

### Analytics Dashboard

**Endpoint**: `GET /admin/dashboard/analytics`

**Authentication**: Required (Admin Bearer token)

**Response** (200 OK):
```json
{
  "totals": {
    "users": 150,
    "lost_active": 25,
    "found_active": 30,
    "resolved": 100,
    "matches_pending": 5,
    "matches_approved": 50
  },
  "daily_reports_last_30_days": {
    "2024-01-01": {
      "LOST": 3,
      "FOUND": 2
    },
    "2024-01-02": {
      "LOST": 1,
      "FOUND": 4
    }
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not an admin

### Users Table

**Endpoint**: `GET /admin/dashboard/users`

**Authentication**: Required (Admin Bearer token)

**Query Parameters**:
- `limit` (int, optional, default: 50, max: 200): Number of users to return
- `offset` (int, optional, default: 0): Pagination offset

**Response** (200 OK):
```json
[
  {
    "id": "uuid",
    "name": "John Doe",
    "email": "john.doe@university.edu",
    "roll_number": "2024CS001",
    "hostel": "Hostel A",
    "contact_number": "+1234567890",
    "role": "USER",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not an admin

### Items Table

**Endpoint**: `GET /admin/dashboard/items`

**Authentication**: Required (Admin Bearer token)

**Query Parameters**:
- `limit` (int, optional, default: 50, max: 200): Number of items to return
- `offset` (int, optional, default: 0): Pagination offset
- `status` (enum, optional): Filter by status (`LOST` or `FOUND`)
- `include_archived` (bool, optional, default: true): Include archived items

**Response** (200 OK): Array of item objects (same format as item reports)

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not an admin

### Matches Table

**Endpoint**: `GET /admin/dashboard/matches`

**Authentication**: Required (Admin Bearer token)

**Query Parameters**:
- `limit` (int, optional, default: 50, max: 200): Number of matches to return
- `offset` (int, optional, default: 0): Pagination offset
- `status` (enum, optional): Filter by status (`PENDING`, `APPROVED`, or `REJECTED`)

**Response** (200 OK): Array of match objects (same format as match responses)

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Not an admin

---

## File Uploads

### Supported Formats

- **Image Types**: JPEG, PNG, WebP
- **Max File Size**: 5MB
- **Content Type**: `multipart/form-data`

### Image URLs

Uploaded images are served at:
```
{base_url}/static/uploads/{filename}
```

Example:
```
http://localhost:8000/static/uploads/abc123.jpg
```

### Image Display

Use the `image_url` from item responses directly in `<img>` tags:

```html
<img src="http://localhost:8000/static/uploads/abc123.jpg" alt="Item image" />
```

Or use relative URLs if frontend and backend share the same domain:
```html
<img src="/static/uploads/abc123.jpg" alt="Item image" />
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request (e.g., missing required image)
- `401 Unauthorized`: Authentication required or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., email already registered)
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Validation Errors

When validation fails (422), the response includes detailed field errors:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Token Expiration

When an access token expires:
1. The API returns `401 Unauthorized`
2. Frontend should call `/auth/refresh` with the refresh token
3. Update stored tokens with new tokens
4. Retry the original request

### Error Handling Example

```javascript
async function apiRequest(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': options.body instanceof FormData ? undefined : 'application/json'
    }
  });

  if (response.status === 401) {
    // Try to refresh token
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry original request
      return apiRequest(url, options);
    }
    // Redirect to login
    window.location.href = '/login';
    return;
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}
```

---

## Real-time Updates

### Polling Strategy

Since the API doesn't currently support WebSockets or SSE, implement polling for real-time updates:

**Recommended Approach**:
1. Poll `/matches/my_matches` every 30-60 seconds when user is on the dashboard
2. Poll `/items/all_found_items` every 60 seconds when browsing found items
3. Stop polling when user navigates away or app is in background

**Example**:
```javascript
let pollInterval;

function startPollingMatches() {
  pollInterval = setInterval(async () => {
    const matches = await fetch('/matches/my_matches', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    updateMatchesUI(matches);
  }, 30000); // Poll every 30 seconds
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
  }
}
```

### Optimistic Updates

For better UX, implement optimistic updates:
- When user approves/rejects a match, update UI immediately
- If API call fails, revert the UI change and show error

---

## Best Practices

### 1. Token Management

- Store tokens securely (consider using `httpOnly` cookies if possible)
- Implement automatic token refresh before expiration
- Clear tokens on logout
- Handle token expiration gracefully

### 2. File Uploads

- Validate file size and type on frontend before upload
- Show upload progress indicators
- Handle upload errors gracefully
- Compress images before upload if possible

### 3. Error Handling

- Display user-friendly error messages
- Log errors for debugging
- Implement retry logic for network errors
- Handle rate limiting (if implemented)

### 4. Performance

- Implement pagination for large lists
- Use lazy loading for images
- Cache frequently accessed data
- Debounce search inputs

### 5. User Experience

- Show loading states during API calls
- Implement optimistic updates where appropriate
- Provide clear feedback for all actions
- Handle edge cases (no matches, empty lists, etc.)

### 6. Security

- Never expose tokens in URLs or logs
- Validate all user inputs on frontend (but trust backend validation)
- Use HTTPS in production
- Implement CSRF protection if using cookies

### 7. Location Handling

The system supports the following standard locations:
- Cafeteria
- Library
- Hostel A
- Hostel B
- Hostel C
- Tan Block
- Cos Block
- G Block
- B Block

The matching algorithm uses location proximity as a tie-breaker when similarity scores are close to the threshold. Locations are normalized automatically, so variations like "cafe", "mess", "lib" will be matched correctly.

---

## Example Integration Code

### React Example

```typescript
// api.ts
const API_BASE = 'http://localhost:8000';

export async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (!response.ok) throw new Error('Login failed');
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  return data;
}

export async function reportFoundItem(
  description: string,
  location: string,
  image: File
) {
  const token = localStorage.getItem('access_token');
  const formData = new FormData();
  formData.append('description', description);
  formData.append('location', location);
  formData.append('image', image);
  
  const response = await fetch(`${API_BASE}/items/report_found`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  if (!response.ok) throw new Error('Failed to report item');
  return response.json();
}

export async function getMyMatches() {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${API_BASE}/matches/my_matches`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) throw new Error('Failed to fetch matches');
  return response.json();
}

export async function approveMatch(matchId: string) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${API_BASE}/matches/${matchId}/approve`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (!response.ok) throw new Error('Failed to approve match');
  return response.json();
}
```

### Vue Example

```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post('/auth/refresh', {
            refresh_token: refreshToken
          });
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          // Retry original request
          return api.request(error.config);
        } catch {
          // Redirect to login
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review error messages in responses
3. Check server logs for detailed error information
4. Contact the backend development team

---

**Last Updated**: 2024-01-01
**API Version**: 1.0.0

