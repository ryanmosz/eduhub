# Workflow Management API Documentation

This document provides comprehensive API documentation for the EduHub Workflow Management system, including OpenAPI schemas, examples, and detailed endpoint descriptions.

## Overview

The Workflow Management API enables educational institutions to manage content lifecycle workflows through predefined templates. The system supports role-based permission management, audit logging, and integration with Plone CMS.

## Base URL

```
https://api.eduhub.edu/workflows
```

## Authentication

All endpoints require authentication via JWT token. Include the token in the Authorization header:

```http
Authorization: Bearer <jwt_token>
```

## OpenAPI Schema

### Core Models

#### WorkflowTemplate

```yaml
WorkflowTemplate:
  type: object
  required:
    - id
    - name
    - description
    - category
    - states
    - transitions
  properties:
    id:
      type: string
      description: Unique template identifier
      example: "simple_review"
    name:
      type: string
      description: Human-readable template name
      example: "Simple Review Workflow"
    description:
      type: string
      description: Template description and purpose
      example: "Basic draft → review → published workflow for educational content"
    category:
      type: string
      enum: ["educational", "corporate", "research"]
      description: Template category
      example: "educational"
    states:
      type: array
      items:
        $ref: '#/components/schemas/WorkflowState'
      description: List of workflow states
    transitions:
      type: array
      items:
        $ref: '#/components/schemas/WorkflowTransition'
      description: List of available transitions
    default_permissions:
      type: object
      description: Default permissions by role
      additionalProperties:
        type: array
        items:
          type: string
    metadata:
      type: object
      description: Additional template metadata
      properties:
        created_by:
          type: string
        created_at:
          type: string
          format: date-time
        version:
          type: string
```

#### WorkflowState

```yaml
WorkflowState:
  type: object
  required:
    - id
    - name
    - permissions
  properties:
    id:
      type: string
      description: State identifier
      example: "draft"
    name:
      type: string
      description: Human-readable state name
      example: "Draft"
    description:
      type: string
      description: State description
      example: "Content is being created or edited"
    permissions:
      type: array
      items:
        $ref: '#/components/schemas/StatePermission'
      description: Permissions for this state
    is_initial:
      type: boolean
      description: Whether this is the initial state
      default: false
    is_final:
      type: boolean
      description: Whether this is a final state
      default: false
```

#### WorkflowTransition

```yaml
WorkflowTransition:
  type: object
  required:
    - id
    - name
    - from_state
    - to_state
    - required_role
  properties:
    id:
      type: string
      description: Transition identifier
      example: "submit"
    name:
      type: string
      description: Human-readable transition name
      example: "Submit for Review"
    description:
      type: string
      description: Transition description
      example: "Submit content for peer review"
    from_state:
      type: string
      description: Source state ID
      example: "draft"
    to_state:
      type: string
      description: Target state ID
      example: "pending"
    required_role:
      type: string
      enum: ["author", "peer_reviewer", "editor", "subject_expert", "publisher", "administrator", "viewer"]
      description: Role required to execute transition
      example: "author"
    conditions:
      type: array
      items:
        type: string
      description: Additional conditions for transition
```

#### StatePermission

```yaml
StatePermission:
  type: object
  required:
    - role
    - actions
  properties:
    role:
      type: string
      enum: ["author", "peer_reviewer", "editor", "subject_expert", "publisher", "administrator", "viewer"]
      description: Role this permission applies to
      example: "author"
    actions:
      type: array
      items:
        type: string
        enum: ["view", "edit", "delete", "submit", "review", "approve", "publish", "reject", "retract", "manage_workflow", "assign_roles"]
      description: Actions allowed for this role
      example: ["view", "edit", "submit"]
```

### Request/Response Models

#### ApplyTemplateRequest

```yaml
ApplyTemplateRequest:
  type: object
  required:
    - role_assignments
  properties:
    role_assignments:
      type: object
      description: Mapping of roles to user/group IDs
      additionalProperties:
        type: array
        items:
          type: string
      example:
        author: ["user1", "user2"]
        editor: ["editor1"]
        administrator: ["admin1"]
    force:
      type: boolean
      description: Force application even if content already has workflow
      default: false
    backup_existing:
      type: boolean
      description: Create backup of existing workflow
      default: true
```

#### ApplyTemplateResponse

```yaml
ApplyTemplateResponse:
  type: object
  properties:
    success:
      type: boolean
      description: Whether operation succeeded
      example: true
    template_id:
      type: string
      description: Applied template ID
      example: "simple_review"
    content_uid:
      type: string
      description: Content UID
      example: "content-123"
    user_id:
      type: string
      description: User who performed operation
      example: "user123"
    validation_results:
      type: object
      description: Validation results
      properties:
        template:
          $ref: '#/components/schemas/ValidationResult'
        roles:
          $ref: '#/components/schemas/ValidationResult'
        content:
          $ref: '#/components/schemas/ValidationResult'
    application_result:
      type: object
      description: Application details
      properties:
        workflow_created:
          type: string
          example: "workflow_789"
        permissions_applied:
          type: integer
          example: 15
        backup_created:
          type: boolean
          example: true
    audit_log:
      $ref: '#/components/schemas/AuditEntry'
    warnings:
      type: array
      items:
        type: string
      description: Warning messages
    applied_at:
      type: string
      format: date-time
      description: Application timestamp
```

#### ExecuteTransitionRequest

```yaml
ExecuteTransitionRequest:
  type: object
  required:
    - content_uid
    - transition_id
  properties:
    content_uid:
      type: string
      description: Content item UID
      example: "content-123"
    transition_id:
      type: string
      description: Transition to execute
      example: "submit"
    comments:
      type: string
      description: Optional comments for the transition
      example: "Ready for review"
      maxLength: 1000
    notify_users:
      type: boolean
      description: Whether to notify relevant users
      default: true
```

#### WorkflowStateResponse

```yaml
WorkflowStateResponse:
  type: object
  properties:
    content_uid:
      type: string
      description: Content item UID
      example: "content-123"
    current_state:
      type: string
      description: Current workflow state
      example: "draft"
    workflow_id:
      type: string
      description: Workflow instance ID
      example: "workflow_789"
    available_transitions:
      type: array
      items:
        $ref: '#/components/schemas/AvailableTransition'
      description: Transitions available to current user
    template_metadata:
      type: object
      description: Applied template information
      properties:
        template_id:
          type: string
          example: "simple_review"
        applied_by:
          type: string
          example: "admin"
        applied_at:
          type: string
          format: date-time
        role_assignments:
          type: object
          additionalProperties:
            type: array
            items:
              type: string
    history:
      type: array
      items:
        $ref: '#/components/schemas/WorkflowHistoryEntry'
      description: Workflow transition history
```

#### AvailableTransition

```yaml
AvailableTransition:
  type: object
  properties:
    id:
      type: string
      example: "submit"
    title:
      type: string
      example: "Submit for Review"
    target_state:
      type: string
      example: "pending"
    requires_comment:
      type: boolean
      default: false
```

#### WorkflowHistoryEntry

```yaml
WorkflowHistoryEntry:
  type: object
  properties:
    timestamp:
      type: string
      format: date-time
    from_state:
      type: string
    to_state:
      type: string
    transition_id:
      type: string
    user_id:
      type: string
    comments:
      type: string
```

#### TemplateListResponse

```yaml
TemplateListResponse:
  type: object
  properties:
    templates:
      type: array
      items:
        $ref: '#/components/schemas/WorkflowTemplateSummary'
      description: Available templates
    total_count:
      type: integer
      description: Total number of templates
      example: 5
    filtered_count:
      type: integer
      description: Number of templates after filtering
      example: 3
    categories:
      type: array
      items:
        type: string
      description: Available categories
      example: ["educational", "corporate", "research"]
```

#### WorkflowTemplateSummary

```yaml
WorkflowTemplateSummary:
  type: object
  properties:
    id:
      type: string
      example: "simple_review"
    name:
      type: string
      example: "Simple Review Workflow"
    description:
      type: string
      example: "Basic draft → review → published workflow"
    category:
      type: string
      example: "educational"
    states:
      type: array
      items:
        type: string
      description: State names
      example: ["draft", "pending", "published"]
    transitions:
      type: array
      items:
        type: string
      description: Transition names
      example: ["submit", "approve", "publish"]
    complexity:
      type: string
      enum: ["simple", "moderate", "complex"]
      example: "simple"
```

#### ValidationResult

```yaml
ValidationResult:
  type: object
  properties:
    is_valid:
      type: boolean
      example: true
    missing_roles:
      type: array
      items:
        type: string
      description: Roles referenced but not found
    invalid_permissions:
      type: array
      items:
        type: string
      description: Invalid permission mappings
    warnings:
      type: array
      items:
        type: string
      description: Validation warnings
    errors:
      type: array
      items:
        type: string
      description: Validation errors
```

#### AuditEntry

```yaml
AuditEntry:
  type: object
  properties:
    timestamp:
      type: string
      format: date-time
    operation:
      type: string
      example: "apply_template"
    user_id:
      type: string
      example: "user123"
    content_uid:
      type: string
      example: "content-123"
    template_id:
      type: string
      example: "simple_review"
    success:
      type: boolean
      example: true
    changes:
      type: array
      items:
        type: object
      description: List of changes made
    metadata:
      type: object
      description: Additional audit metadata
    error:
      type: string
      description: Error message if operation failed
```

#### ErrorResponse

```yaml
ErrorResponse:
  type: object
  properties:
    error:
      type: string
      description: Error message
      example: "Template validation failed"
    error_code:
      type: string
      description: Machine-readable error code
      example: "VALIDATION_ERROR"
    details:
      type: object
      description: Additional error details
    timestamp:
      type: string
      format: date-time
    request_id:
      type: string
      description: Unique request identifier for debugging
```

## API Endpoints

### GET /workflows/templates

List available workflow templates with optional filtering.

**Parameters:**
- `categories` (query, array): Filter by categories
- `complexity` (query, string): Filter by complexity level
- `limit` (query, integer): Maximum results (default: 50)
- `offset` (query, integer): Pagination offset (default: 0)

**Example Request:**
```http
GET /workflows/templates?categories=educational&complexity=simple
Authorization: Bearer <jwt_token>
```

**Example Response:**
```json
{
  "templates": [
    {
      "id": "simple_review",
      "name": "Simple Review Workflow",
      "description": "Basic draft → review → published workflow for educational content",
      "category": "educational",
      "states": ["draft", "pending", "published"],
      "transitions": ["submit", "approve", "publish"],
      "complexity": "simple"
    }
  ],
  "total_count": 5,
  "filtered_count": 1,
  "categories": ["educational", "corporate", "research"]
}
```

### GET /workflows/templates/{template_id}

Get detailed information about a specific workflow template.

**Path Parameters:**
- `template_id` (string, required): Template identifier

**Example Request:**
```http
GET /workflows/templates/simple_review
Authorization: Bearer <jwt_token>
```

**Example Response:**
```json
{
  "template": {
    "id": "simple_review",
    "name": "Simple Review Workflow",
    "description": "Basic draft → review → published workflow for educational content",
    "category": "educational",
    "states": [
      {
        "id": "draft",
        "name": "Draft",
        "description": "Content is being created or edited",
        "permissions": [
          {
            "role": "author",
            "actions": ["view", "edit", "submit"]
          },
          {
            "role": "editor",
            "actions": ["view", "edit", "delete"]
          }
        ],
        "is_initial": true
      }
    ],
    "transitions": [
      {
        "id": "submit",
        "name": "Submit for Review",
        "description": "Submit content for peer review",
        "from_state": "draft",
        "to_state": "pending",
        "required_role": "author"
      }
    ],
    "default_permissions": {
      "administrator": ["view", "edit", "delete", "manage_workflow"],
      "viewer": ["view"]
    }
  }
}
```

### POST /workflows/apply/{template_id}

Apply a workflow template to content.

**Path Parameters:**
- `template_id` (string, required): Template to apply

**Query Parameters:**
- `content_uid` (string, required): Content item UID

**Request Body:** ApplyTemplateRequest

**Example Request:**
```http
POST /workflows/apply/simple_review?content_uid=content-123
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "role_assignments": {
    "author": ["user1", "user2"],
    "editor": ["editor1"],
    "administrator": ["admin1"]
  },
  "force": false,
  "backup_existing": true
}
```

**Example Response:**
```json
{
  "success": true,
  "template_id": "simple_review",
  "content_uid": "content-123",
  "user_id": "current-user",
  "validation_results": {
    "template": {
      "is_valid": true,
      "warnings": ["Template uses privileged role 'administrator' - ensure proper access control"],
      "errors": []
    },
    "roles": {
      "is_valid": true,
      "warnings": [],
      "errors": []
    },
    "content": {
      "is_valid": true,
      "warnings": [],
      "errors": []
    }
  },
  "application_result": {
    "workflow_created": "workflow_789",
    "permissions_applied": 15,
    "backup_created": true
  },
  "audit_log": {
    "timestamp": "2025-01-01T12:00:00Z",
    "operation": "apply_template",
    "user_id": "current-user",
    "content_uid": "content-123",
    "template_id": "simple_review",
    "success": true,
    "changes": [
      {
        "type": "role_added",
        "role": "Author",
        "users": ["user1", "user2"]
      }
    ]
  },
  "warnings": [],
  "applied_at": "2025-01-01T12:00:00Z"
}
```

### POST /workflows/transition

Execute a workflow transition.

**Request Body:** ExecuteTransitionRequest

**Example Request:**
```http
POST /workflows/transition
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content_uid": "content-123",
  "transition_id": "submit",
  "comments": "Content is ready for review",
  "notify_users": true
}
```

**Example Response:**
```json
{
  "success": true,
  "content_uid": "content-123",
  "transition_id": "submit",
  "from_state": "draft",
  "to_state": "pending",
  "executed_at": "2025-01-01T12:00:00Z",
  "executed_by": "current-user",
  "comments": "Content is ready for review",
  "notifications_sent": ["editor1", "reviewer2"]
}
```

### GET /workflows/content/{content_uid}/state

Get the current workflow state of content.

**Path Parameters:**
- `content_uid` (string, required): Content item UID

**Example Request:**
```http
GET /workflows/content/content-123/state
Authorization: Bearer <jwt_token>
```

**Example Response:**
```json
{
  "content_uid": "content-123",
  "current_state": "pending",
  "workflow_id": "workflow_789",
  "available_transitions": [
    {
      "id": "approve",
      "title": "Approve",
      "target_state": "published",
      "requires_comment": false
    },
    {
      "id": "reject",
      "title": "Reject",
      "target_state": "draft",
      "requires_comment": true
    }
  ],
  "template_metadata": {
    "template_id": "simple_review",
    "applied_by": "admin",
    "applied_at": "2025-01-01T10:00:00Z",
    "role_assignments": {
      "Author": ["user1", "user2"],
      "Editor": ["editor1"]
    }
  },
  "history": [
    {
      "timestamp": "2025-01-01T11:00:00Z",
      "from_state": "draft",
      "to_state": "pending",
      "transition_id": "submit",
      "user_id": "user1",
      "comments": "Ready for review"
    }
  ]
}
```

### DELETE /workflows/content/{content_uid}/template

Remove workflow template from content.

**Path Parameters:**
- `content_uid` (string, required): Content item UID

**Query Parameters:**
- `restore_backup` (boolean): Whether to restore original workflow (default: true)

**Example Request:**
```http
DELETE /workflows/content/content-123/template?restore_backup=true
Authorization: Bearer <jwt_token>
```

**Example Response:**
```json
{
  "success": true,
  "content_uid": "content-123",
  "template_removed": "simple_review",
  "backup_restored": true,
  "removed_at": "2025-01-01T12:00:00Z",
  "removed_by": "current-user"
}
```

### GET /workflows/health

Check workflow system health.

**Example Request:**
```http
GET /workflows/health
Authorization: Bearer <jwt_token>
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "checks": {
    "templates_loadable": {
      "status": "ok",
      "details": "All 5 templates loaded successfully"
    },
    "plone_connection": {
      "status": "ok",
      "details": "Plone API responding normally"
    },
    "audit_logging": {
      "status": "ok",
      "details": "Audit log writable"
    }
  },
  "version": "1.0.0"
}
```

## Error Responses

All endpoints may return these common error responses:

### 400 Bad Request
```json
{
  "error": "Invalid role assignments: Role 'author' has no assigned users",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "validation_errors": ["Role 'author' has no assigned users"],
    "field": "role_assignments"
  },
  "timestamp": "2025-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "error_code": "AUTHENTICATION_REQUIRED",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions for workflow management",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "details": {
    "required_roles": ["workflow_manager", "administrator"],
    "user_roles": ["viewer"]
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 404 Not Found
```json
{
  "error": "Template 'nonexistent' not found",
  "error_code": "TEMPLATE_NOT_FOUND",
  "details": {
    "template_id": "nonexistent",
    "available_templates": ["simple_review", "extended_review"]
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 409 Conflict
```json
{
  "error": "Content already has workflow template applied",
  "error_code": "WORKFLOW_EXISTS",
  "details": {
    "existing_template": "simple_review",
    "applied_at": "2025-01-01T10:00:00Z",
    "suggestion": "Use force=true to override"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to connect to Plone instance",
  "error_code": "PLONE_CONNECTION_ERROR",
  "details": {
    "plone_url": "https://plone.example.com",
    "retry_after": 300
  },
  "timestamp": "2025-01-01T12:00:00Z",
  "request_id": "req_123"
}
```

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Template endpoints**: 100 requests per minute per user
- **Application endpoints**: 20 requests per minute per user
- **State queries**: 200 requests per minute per user
- **Health checks**: 500 requests per minute per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## SDKs and Examples

### Python SDK Example

```python
from eduhub_client import WorkflowClient

client = WorkflowClient(
    base_url="https://api.eduhub.edu",
    token="your_jwt_token"
)

# List templates
templates = client.templates.list(categories=["educational"])

# Apply template
result = client.templates.apply(
    template_id="simple_review",
    content_uid="content-123",
    role_assignments={
        "author": ["user1", "user2"],
        "editor": ["editor1"]
    }
)

# Execute transition
transition = client.transitions.execute(
    content_uid="content-123",
    transition_id="submit",
    comments="Ready for review"
)
```

### JavaScript SDK Example

```javascript
import { WorkflowClient } from '@eduhub/workflow-sdk';

const client = new WorkflowClient({
  baseURL: 'https://api.eduhub.edu',
  token: 'your_jwt_token'
});

// List templates
const templates = await client.templates.list({
  categories: ['educational']
});

// Apply template
const result = await client.templates.apply('simple_review', {
  contentUid: 'content-123',
  roleAssignments: {
    author: ['user1', 'user2'],
    editor: ['editor1']
  }
});

// Execute transition
const transition = await client.transitions.execute({
  contentUid: 'content-123',
  transitionId: 'submit',
  comments: 'Ready for review'
});
```

## Webhooks

The system supports webhooks for real-time notifications of workflow events:

### Webhook Events

- `workflow.template.applied`
- `workflow.transition.executed`
- `workflow.template.removed`
- `workflow.permission.changed`

### Webhook Payload Example

```json
{
  "event": "workflow.transition.executed",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": {
    "content_uid": "content-123",
    "workflow_id": "workflow_789",
    "transition_id": "submit",
    "from_state": "draft",
    "to_state": "pending",
    "user_id": "user1",
    "comments": "Ready for review"
  },
  "signature": "sha256=...",
  "delivery_id": "delivery_123"
}
```
