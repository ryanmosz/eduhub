# Workflow Templates API

Comprehensive role-based workflow management for educational content in Plone CMS instances.

## Overview

The Workflow Templates system allows you to define, validate, and apply sophisticated workflow patterns to manage educational content lifecycle. From simple review processes to complex multi-stage academic approval workflows, the system provides flexible, role-based state management.

## Quick Start

### 1. Available Built-in Templates

```bash
GET /workflows/templates
```

**Response:**
```json
[
  {
    "id": "simple_review",
    "name": "Simple Review Workflow",
    "description": "A basic 3-state workflow for educational content",
    "complexity": "simple",
    "category": "educational",
    "states_count": 3,
    "transitions_count": 3
  },
  {
    "id": "extended_review",
    "name": "Extended Review Workflow",
    "description": "A comprehensive 6-state workflow for complex educational content",
    "complexity": "advanced",
    "category": "educational",
    "states_count": 6,
    "transitions_count": 7
  }
]
```

### 2. Get Specific Template

```bash
GET /workflows/templates/simple_review
```

### 3. Apply Template to Content

```bash
POST /workflows/content/{content_id}/apply
{
  "template_id": "simple_review",
  "initial_roles": {
    "author": ["user123"],
    "editor": ["reviewer456"]
  }
}
```

## Schema Definition

### Core Components

#### WorkflowAction Enum
Standard actions available in educational workflows:

```typescript
enum WorkflowAction {
  // Content permissions
  VIEW = "view"
  EDIT = "edit"
  DELETE = "delete"

  // Workflow permissions
  SUBMIT = "submit"
  REVIEW = "review"
  APPROVE = "approve"
  PUBLISH = "publish"
  REJECT = "reject"
  RETRACT = "retract"

  // Administrative permissions
  MANAGE_WORKFLOW = "manage_workflow"
  ASSIGN_ROLES = "assign_roles"
}
```

#### EducationRole Enum
Predefined roles for educational content management:

```typescript
enum EducationRole {
  AUTHOR = "author"
  PEER_REVIEWER = "peer_reviewer"
  EDITOR = "editor"
  SUBJECT_EXPERT = "subject_expert"
  PUBLISHER = "publisher"
  ADMINISTRATOR = "administrator"
  VIEWER = "viewer"
}
```

#### StateType Enum
Semantic categorization of workflow states:

```typescript
enum StateType {
  DRAFT = "draft"          // Initial creation state
  REVIEW = "review"        // Under review
  REVISION = "revision"    // Needs changes
  APPROVED = "approved"    // Approved but not published
  PUBLISHED = "published"  // Live/public
  ARCHIVED = "archived"    // No longer active
  REJECTED = "rejected"    // Permanently rejected
}
```

### Data Models

#### WorkflowPermission
Defines what a role can do in a specific state:

```json
{
  "role": "author",
  "actions": ["view", "edit", "submit"]
}
```

#### WorkflowState
Represents a single state in the workflow:

```json
{
  "id": "draft",
  "title": "Draft",
  "description": "Content is being created or edited",
  "state_type": "draft",
  "permissions": [
    {
      "role": "author",
      "actions": ["view", "edit", "submit"]
    }
  ],
  "is_initial": true,
  "is_final": false,
  "ui_metadata": {
    "color": "#94a3b8",
    "icon": "edit",
    "description_short": "Being written"
  }
}
```

#### WorkflowTransition
Defines how content moves between states:

```json
{
  "id": "submit_for_review",
  "title": "Submit for Review",
  "from_state": "draft",
  "to_state": "review",
  "required_role": "author",
  "conditions": {
    "require_comments": false,
    "min_content_length": 50
  }
}
```

#### WorkflowTemplate
Complete workflow definition:

```json
{
  "id": "simple_review",
  "name": "Simple Review Workflow",
  "description": "A basic 3-state workflow for educational content",
  "version": "1.0.0",
  "category": "educational",
  "states": [...],
  "transitions": [...],
  "default_permissions": {
    "administrator": ["view", "edit", "delete", "manage_workflow"],
    "viewer": ["view"]
  },
  "metadata": {
    "complexity": "simple",
    "recommended_for": ["course_materials", "assignments"],
    "typical_duration": "2-5 days"
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Built-in Templates

### Simple Review Workflow

**Flow:** Draft → Review → Published

Perfect for basic educational content requiring minimal oversight.

#### States:
- **Draft**: Author creates/edits content
- **Review**: Editor reviews and approves
- **Published**: Content is live

#### Transitions:
- **Submit for Review**: Draft → Review (Author)
- **Approve and Publish**: Review → Published (Editor)
- **Reject**: Review → Draft (Editor)

#### Roles:
- **Author**: Creates content, submits for review
- **Editor**: Reviews, approves/rejects content
- **Administrator**: Full management access

#### Recommended for:
- Course materials and assignments
- Simple educational resources
- Documents needing basic quality control
- Small teams (2-10 people)

### Extended Review Workflow

**Flow:** Draft → Peer Review → Editorial Review → Approved → Published → Archived

Comprehensive workflow for complex academic content.

#### States:
- **Draft**: Initial content creation
- **Peer Review**: Technical accuracy review by peers
- **Editorial Review**: Subject expert and editorial validation
- **Approved**: Ready for publication
- **Published**: Live content
- **Archived**: Historical preservation

#### Transitions:
- **Submit for Peer Review**: Draft → Peer Review (Author)
- **Forward to Editorial**: Peer Review → Editorial Review (Peer Reviewer)
- **Editorial Approval**: Editorial Review → Approved (Editor)
- **Publish Content**: Approved → Published (Publisher)
- **Archive Content**: Published → Archived (Administrator)
- **Reject Paths**: Multiple rejection routes back to Draft

#### Roles:
- **Author**: Content creator
- **Peer Reviewer**: Technical validation
- **Subject Expert**: Domain expertise validation
- **Editor**: Final editorial approval
- **Publisher**: Publication management
- **Administrator**: Full system access

#### Recommended for:
- Research papers and academic content
- Complex curriculum materials
- Multi-contributor resources
- High-quality educational materials
- Large teams (4-50 people)

## JSON Examples

### Complete Simple Review Template

```json
{
  "id": "simple_review",
  "name": "Simple Review Workflow",
  "description": "A basic 3-state workflow designed for educational content that requires author creation, reviewer approval, and publication.",
  "version": "1.0.0",
  "category": "educational",
  "states": [
    {
      "id": "draft",
      "title": "Draft",
      "description": "Content is being created or edited by the author.",
      "state_type": "draft",
      "permissions": [
        {
          "role": "author",
          "actions": ["view", "edit", "submit"]
        },
        {
          "role": "administrator",
          "actions": ["view", "edit", "delete", "manage_workflow"]
        }
      ],
      "is_initial": true,
      "is_final": false,
      "ui_metadata": {
        "color": "#94a3b8",
        "icon": "edit",
        "description_short": "Being written"
      }
    },
    {
      "id": "review",
      "title": "Under Review",
      "description": "Content is being reviewed by qualified reviewers.",
      "state_type": "review",
      "permissions": [
        {
          "role": "author",
          "actions": ["view"]
        },
        {
          "role": "editor",
          "actions": ["view", "review", "approve", "reject"]
        },
        {
          "role": "administrator",
          "actions": ["view", "edit", "review", "approve", "reject", "manage_workflow"]
        }
      ],
      "is_initial": false,
      "is_final": false,
      "ui_metadata": {
        "color": "#fbbf24",
        "icon": "clock",
        "description_short": "Under review"
      }
    },
    {
      "id": "published",
      "title": "Published",
      "description": "Content is approved and publicly available.",
      "state_type": "published",
      "permissions": [
        {
          "role": "author",
          "actions": ["view"]
        },
        {
          "role": "editor",
          "actions": ["view"]
        },
        {
          "role": "viewer",
          "actions": ["view"]
        },
        {
          "role": "administrator",
          "actions": ["view", "edit", "retract", "manage_workflow"]
        }
      ],
      "is_initial": false,
      "is_final": true,
      "ui_metadata": {
        "color": "#10b981",
        "icon": "check-circle",
        "description_short": "Live"
      }
    }
  ],
  "transitions": [
    {
      "id": "submit_for_review",
      "title": "Submit for Review",
      "from_state": "draft",
      "to_state": "review",
      "required_role": "author",
      "conditions": {
        "require_comments": false,
        "min_content_length": 50
      }
    },
    {
      "id": "approve_content",
      "title": "Approve and Publish",
      "from_state": "review",
      "to_state": "published",
      "required_role": "editor",
      "conditions": {
        "require_comments": true
      }
    },
    {
      "id": "reject_to_draft",
      "title": "Reject - Return to Draft",
      "from_state": "review",
      "to_state": "draft",
      "required_role": "editor",
      "conditions": {
        "require_comments": true,
        "require_feedback": true
      }
    }
  ],
  "default_permissions": {
    "administrator": ["view", "edit", "delete", "manage_workflow", "assign_roles"],
    "viewer": ["view"]
  },
  "metadata": {
    "complexity": "simple",
    "recommended_for": [
      "course_materials",
      "assignments",
      "educational_resources"
    ],
    "typical_duration": "2-5 days",
    "min_participants": 2,
    "max_participants": 10,
    "tags": ["basic", "educational", "review"]
  }
}
```

### Invalid Template Example (for testing)

```json
{
  "id": "invalid_example",
  "name": "",
  "version": "not_semantic",
  "states": [
    {
      "id": "x",
      "title": "",
      "state_type": "draft",
      "permissions": [
        {
          "role": "invalid_role",
          "actions": ["invalid_action"]
        }
      ],
      "is_initial": true,
      "is_final": true
    }
  ],
  "transitions": [
    {
      "id": "invalid_transition",
      "from_state": "nonexistent",
      "to_state": "x",
      "required_role": "author"
    }
  ]
}
```

This will trigger validation errors for:
- Invalid semantic version
- Empty workflow name
- State ID too short
- Invalid role and action names
- Missing transitions
- State marked as both initial and final

## Usage Examples

### Python (Pydantic)

```python
from eduhub.workflows.models import WorkflowTemplate
from eduhub.workflows.templates import get_template

# Load built-in template
template = get_template("simple_review")

# Check what an author can do in draft state
actions = template.get_available_actions("draft", "author")
print(actions)  # {VIEW, EDIT, SUBMIT}

# Get transitions from draft state
transitions = template.get_transitions_from_state("draft")
print([t.title for t in transitions])  # ["Submit for Review"]

# Load from JSON
with open("custom_workflow.json") as f:
    data = json.load(f)
    custom_workflow = WorkflowTemplate(**data)
```

### JavaScript (Frontend)

```javascript
// Fetch available templates
const response = await fetch('/api/workflows/templates');
const templates = await response.json();

// Apply template to content
await fetch(`/api/workflows/content/${contentId}/apply`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    template_id: 'simple_review',
    initial_roles: {
      author: ['user123'],
      editor: ['reviewer456']
    }
  })
});

// Get workflow state for content
const stateResponse = await fetch(`/api/workflows/content/${contentId}/state`);
const workflowState = await stateResponse.json();
```

### cURL Examples

```bash
# List templates
curl -X GET http://localhost:8000/api/workflows/templates

# Get specific template
curl -X GET http://localhost:8000/api/workflows/templates/simple_review

# Apply template
curl -X POST http://localhost:8000/api/workflows/content/123/apply \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "simple_review",
    "initial_roles": {
      "author": ["user123"],
      "editor": ["reviewer456"]
    }
  }'

# Execute transition
curl -X POST http://localhost:8000/api/workflows/content/123/transition \
  -H "Content-Type: application/json" \
  -d '{
    "transition_id": "submit_for_review",
    "user_role": "author",
    "comments": "Ready for review"
  }'
```

## Validation Rules

### Template Validation
- Must have exactly one initial state
- Must have at least one final state
- All transitions must reference existing states
- Final states cannot have outgoing transitions
- All non-final states must be reachable from initial state
- Workflow must not contain cycles that prevent reaching final states

### Field Validation
- **State IDs**: Alphanumeric with underscores/hyphens, minimum 2 characters
- **Names**: Minimum 3 characters, descriptive
- **Versions**: Semantic versioning (x.y.z)
- **Roles**: Must be from EducationRole enum
- **Actions**: Must be from WorkflowAction enum

### Schema Constraints
- Minimum 2 states per workflow
- Minimum 1 transition per workflow
- State permissions list can be empty (inherits default permissions)
- Transition conditions are optional
- UI metadata is optional but recommended

## Error Responses

### Template Not Found (404)
```json
{
  "error": "template_not_found",
  "message": "Template 'nonexistent' not found",
  "available_templates": ["simple_review", "extended_review"]
}
```

### Invalid Template Definition (422)
```json
{
  "error": "validation_error",
  "message": "Workflow validation failed",
  "details": [
    {
      "field": "states.0.id",
      "error": "State ID must be at least 2 characters"
    },
    {
      "field": "version",
      "error": "Version must follow semantic versioning (x.y.z)"
    }
  ]
}
```

### Permission Denied (403)
```json
{
  "error": "permission_denied",
  "message": "User does not have required role 'editor' to execute transition 'approve_content'"
}
```

## Common Patterns

### Custom Template Creation

1. **Start with a built-in template** as a base
2. **Define your states** with clear purposes and permissions
3. **Map transitions** ensuring all states are reachable
4. **Test validation** with the Pydantic models
5. **Document role assignments** for your team

### Role Assignment Strategy

- **Keep roles minimal** - only assign what's needed
- **Use default permissions** for common actions
- **Group related permissions** in logical roles
- **Plan for role changes** over content lifecycle

### Performance Considerations

- **Template caching** - built-in templates are cached in memory
- **Permission checking** - O(1) lookup for role actions
- **State validation** - graph algorithms for reachability
- **Transition execution** - atomic operations with rollback

## Integration with Plone CMS

### Plone Workflow Mapping
The templates integrate with Plone's workflow system:

- **States** map to Plone workflow states
- **Transitions** become Plone workflow transitions
- **Permissions** control Plone object permissions
- **Roles** assign to Plone users/groups

### Content Type Support
Templates can be applied to any Plone content type:
- Documents and Pages
- News Items and Events
- Collections and Folders
- Custom educational content types

### Metadata Preservation
- Original Plone workflows are backed up
- Template application is reversible
- Audit trails maintain change history
- Version control integrates with workflow states

This workflow system provides the foundation for sophisticated educational content management while remaining flexible enough to adapt to various institutional needs.
