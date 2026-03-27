# DTC PR Application - API Documentation

## Overview

The DTC PR Application provides a comprehensive REST API for managing Purchase Requisitions with full RBAC, approval workflows, and file management.

## Base URL

```
http://localhost:8000/
```

## Authentication

All endpoints require authentication using Django session cookies. Users must be logged in via `/auth/login/`.

### Login

**Endpoint:** `POST /auth/login/`

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "role": "Requester"
  }
}
```

## API Endpoints

### Purchase Requisitions (PR)

#### List PRs

**Endpoint:** `GET /api/pr/`

**Query Parameters:**
- `status`: Filter by status (DRAFT, PENDING_APPROVAL, APPROVED, REJECTED)
- `pr_type`: Filter by type (OPEX, CAPEX)
- `search`: Search by PR ID, requester name, or purpose
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `page`: Page number (default: 1)

**Response:**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/pr/?page=2",
  "results": [
    {
      "pr_id": "PR/03/2026/312",
      "requester_name": "John Doe",
      "department": "IT",
      "status": "PENDING_APPROVAL",
      "total_value": 150000,
      "created_at": "2026-03-25T10:30:00Z"
    }
  ]
}
```

#### Get PR Details

**Endpoint:** `GET /api/pr/<pr_id>/`

**Response:**
```json
{
  "pr_id": "PR/03/2026/312",
  "requester_name": "John Doe",
  "department": "IT",
  "purpose_of_requirement": "Server upgrade",
  "pr_type": "CAPEX",
  "plant": "CBE",
  "status": "PENDING_APPROVAL",
  "created_at": "2026-03-25T10:30:00Z",
  "items": [
    {
      "item_number": 1,
      "short_text": "Server",
      "quantity": 2,
      "unit": "PC",
      "unit_price": 75000,
      "total_value": 150000
    }
  ],
  "approvals": [
    {
      "approver": "Jane Manager",
      "status": "PENDING",
      "sequence": 1
    }
  ],
  "attachments": [
    {
      "id": 1,
      "file_name": "quotation.pdf",
      "uploaded_by": "John Doe",
      "uploaded_at": "2026-03-25T11:00:00Z"
    }
  ]
}
```

#### Create PR

**Endpoint:** `POST /api/pr/create/`

**Request Body:**
```json
{
  "requester_name": "John Doe",
  "department": "IT",
  "purpose_of_requirement": "Server upgrade",
  "pr_type": "CAPEX",
  "plant": "CBE",
  "pr_date": "2026-03-25",
  "ipc_approval_required": true,
  "cipc_approval_required": false,
  "items": [
    {
      "short_text": "Server",
      "quantity": 2,
      "unit": "PC",
      "unit_price": 75000,
      "asset_code": "AST001",
      "cost_center": "CC001",
      "gl_code": "4100"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "pr_id": "PR/03/2026/312",
  "status": "DRAFT"
}
```

#### Submit PR for Approval

**Endpoint:** `POST /api/pr/<pr_id>/submit/`

**Response:**
```json
{
  "success": true,
  "message": "PR submitted for approval",
  "status": "PENDING_APPROVAL"
}
```

#### Approve/Reject PR

**Endpoint:** `POST /api/pr/<pr_id>/approve/`

**Request Body:**
```json
{
  "action": "APPROVED",
  "comments": "Approved by manager"
}
```

**Response:**
```json
{
  "success": true,
  "message": "PR approved successfully",
  "next_approvers": ["Director"]
}
```

### Vendors

#### List Vendors

**Endpoint:** `GET /api/vendor/`

**Query Parameters:**
- `search`: Search by name or email
- `status`: Filter by status (ACTIVE, INACTIVE, BLACKLISTED)

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "Intellifer Systems",
      "email": "vendor@intellifer.in",
      "phone": "9876543210",
      "location": "Mumbai",
      "status": "ACTIVE"
    }
  ]
}
```

#### Get Vendor Details

**Endpoint:** `GET /api/vendor/<vendor_id>/`

**Response:**
```json
{
  "id": 1,
  "name": "Intellifer Systems",
  "email": "vendor@intellifer.in",
  "contacts": [
    {
      "id": 1,
      "name": "Mrs. Aparnaa",
      "email": "aparnaa@intellifer.in",
      "designation": "Sales Manager"
    }
  ]
}
```

#### Create Vendor

**Endpoint:** `POST /api/vendor/create/`

**Request Body:**
```json
{
  "name": "Vendor Name",
  "email": "vendor@example.com",
  "phone": "9876543210",
  "location": "City",
  "status": "ACTIVE",
  "contacts": [
    {
      "name": "Contact Name",
      "email": "contact@vendor.com",
      "designation": "Manager"
    }
  ]
}
```

### File Attachments

#### List Attachments for PR

**Endpoint:** `GET /api/attachments/pr/<pr_id>/`

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "file_name": "quotation.pdf",
      "attachment_type": "QUOTATION",
      "file_size": 256000,
      "uploaded_by": "John Doe",
      "uploaded_at": "2026-03-25T11:00:00Z"
    }
  ]
}
```

#### Upload Attachment

**Endpoint:** `POST /api/attachments/upload/<pr_id>/`

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: (binary) File to upload
- `attachment_type`: QUOTATION | COMPARISON_SHEET | RFQ | SPECIFICATION | APPROVAL_LETTER | OTHER
- `description`: (optional) Description

**Response:** `201 Created`
```json
{
  "success": true,
  "attachment_id": 1,
  "file_name": "quotation.pdf"
}
```

#### Download Attachment

**Endpoint:** `GET /api/attachments/download/<attachment_id>/`

**Response:** File binary content

#### Delete Attachment

**Endpoint:** `DELETE /api/attachments/delete/<attachment_id>/`

**Response:**
```json
{
  "success": true,
  "message": "Attachment deleted"
}
```

### Dashboard & Reports

#### Dashboard Overview

**Endpoint:** `GET /api/dashboard/`

**Response:**
```json
{
  "total_prs": 150,
  "pending_approval": 25,
  "approved": 100,
  "rejected": 25,
  "total_pr_value": 5000000,
  "status_distribution": [
    {
      "status": "APPROVED",
      "count": 100
    }
  ],
  "monthly_trend": [
    {
      "month": "Feb 2026",
      "count": 45
    }
  ]
}
```

#### My PRs (for Requester)

**Endpoint:** `GET /api/dashboard/my-prs/`

**Response:**
```json
{
  "total_prs": 20,
  "draft_prs": 2,
  "pending_prs": 5,
  "approved_prs": 10,
  "rejected_prs": 3,
  "total_value": 500000
}
```

#### Approvals Queue (for Approver)

**Endpoint:** `GET /api/dashboard/approvals-queue/`

**Response:**
```json
{
  "pending_count": 5,
  "total_approved": 45,
  "total_rejected": 2,
  "pending_approvals": [
    {
      "pr_id": "PR/03/2026/312",
      "requester": "John Doe",
      "total_value": 150000,
      "days_pending": 3
    }
  ]
}
```

#### Audit Log

**Endpoint:** `GET /api/audit/`

**Query Parameters:**
- `action`: Filter by action type
- `user`: Filter by user
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "user": "John Doe",
      "action": "CREATE",
      "object_type": "PurchaseRequisition",
      "description": "PR created",
      "created_at": "2026-03-25T10:30:00Z"
    }
  ]
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| UNAUTHORIZED | 401 | User not authenticated |
| FORBIDDEN | 403 | User lacks required permissions |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Invalid input data |
| CONFLICT | 409 | Duplicate resource or state conflict |
| SERVER_ERROR | 500 | Internal server error |

## Rate Limiting

- 100 requests per minute per user
- 1000 requests per hour per user

## Pagination

Default page size: 20 items
Maximum page size: 100 items

```
?page=1&page_size=50
```

## Filtering Examples

### Search PRs by Requester

```
GET /api/pr/?search=John%20Doe
```

### Filter by Date Range

```
GET /api/pr/?date_from=2026-01-01&date_to=2026-03-31
```

### Get Pending Approvals

```
GET /api/pr/?status=PENDING_APPROVAL
```

## Sorting

Results are sorted by creation date (newest first) unless otherwise specified.

## Response Headers

```
X-Total-Count: 150  (Total number of items)
X-Request-ID: unique-request-id
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1648126800
```

## Webhooks (Commented - Enable with Credentials)

When enabled, webhooks send notifications to configured endpoints for events:

- `pr.created`
- `pr.submitted`
- `pr.approved`
- `pr.rejected`
- `file.uploaded`

## Deprecation Notice

API versions are maintained for 6 months after deprecation notice.

## Support

For API support and issues, contact: api-support@example.com
