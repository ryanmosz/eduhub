# Workflow Template Management User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Understanding Workflow Templates](#understanding-workflow-templates)
4. [Managing Templates](#managing-templates)
5. [Applying Workflows to Content](#applying-workflows-to-content)
6. [Managing Content Lifecycle](#managing-content-lifecycle)
7. [Role-Based Permissions](#role-based-permissions)
8. [Monitoring and Auditing](#monitoring-and-auditing)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Scenarios](#advanced-scenarios)

## Introduction

The EduHub Workflow Management system enables educational institutions to standardize and automate content lifecycle processes. This guide covers everything from basic template application to advanced permission management and monitoring.

### Key Concepts

- **Workflow Template**: Predefined set of states, transitions, and permissions
- **Content Lifecycle**: The journey content takes from creation to publication
- **Role-Based Permissions**: Access control based on educational roles
- **State Transitions**: Moving content between workflow states
- **Audit Trail**: Complete record of all workflow activities

### Who Should Use This Guide

- **Content Managers**: Apply and manage workflows for educational content
- **Administrators**: Configure templates and manage system-wide settings
- **Editors**: Review and approve content through workflow processes
- **Authors**: Create content and initiate workflow processes

## Getting Started

### Prerequisites

Before using the workflow system, ensure you have:

1. **EduHub Account**: Active account with appropriate permissions
2. **Role Assignment**: One of the following roles:
   - `workflow_manager`: Full workflow management capabilities
   - `administrator`: System-wide administrative access
   - `editor`: Content editing and workflow execution
   - `author`: Content creation and submission

3. **Content Items**: Existing content to apply workflows to
4. **Plone Integration**: Active connection to Plone CMS instance

### Accessing the Workflow System

#### Web Interface
Navigate to the EduHub dashboard and click on "Workflow Management" in the main menu.

#### API Access
Use the REST API endpoints documented in the [API Documentation](../api/workflows-openapi-schema.md).

#### Command Line Interface
```bash
# Install EduHub CLI
pip install eduhub-cli

# Configure authentication
eduhub auth login

# List available templates
eduhub workflows templates list
```

## Understanding Workflow Templates

### Template Categories

#### Educational Templates
Designed for academic content and course materials:

- **Simple Review**: Draft → Review → Published
- **Extended Review**: Draft → Peer Review → Editor Review → Published
- **Course Content**: Planning → Development → Review → Testing → Release

#### Corporate Templates
For institutional documentation and policies:

- **Policy Review**: Draft → Legal Review → Approval → Active
- **Document Management**: Creation → Review → Approval → Distribution

#### Research Templates
For academic research and publications:

- **Research Publication**: Draft → Peer Review → Revision → Publication
- **Grant Proposal**: Preparation → Internal Review → Submission → Follow-up

### Template Structure

Each template consists of:

#### States
- **Initial State**: Where content begins (e.g., "Draft")
- **Intermediate States**: Review and processing states
- **Final States**: Published, approved, or archived states

#### Transitions
- **Trigger Conditions**: What causes state changes
- **Required Roles**: Who can execute transitions
- **Validation Rules**: Conditions that must be met

#### Permissions
- **Role-Based Access**: What each role can do in each state
- **Action Restrictions**: Specific limitations per state
- **Default Permissions**: Fallback permissions for all roles

### Viewing Available Templates

#### Web Interface
1. Navigate to **Workflow Management** → **Templates**
2. Browse templates by category or search by name
3. Click on a template to view detailed information

#### API Call
```bash
curl -X GET "https://api.eduhub.edu/workflows/templates" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Example Response
```json
{
  "templates": [
    {
      "id": "simple_review",
      "name": "Simple Review Workflow",
      "description": "Basic draft → review → published workflow",
      "category": "educational",
      "states": ["draft", "pending", "published"],
      "complexity": "simple"
    }
  ],
  "total_count": 5
}
```

## Managing Templates

### Viewing Template Details

To understand a template before applying it:

#### Web Interface
1. Go to **Templates** → Select template → **View Details**
2. Review the workflow diagram showing states and transitions
3. Check permission matrix for each role

#### API Call
```bash
curl -X GET "https://api.eduhub.edu/workflows/templates/simple_review" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Template Information Includes

- **State Definitions**: All possible states and their purposes
- **Transition Rules**: How content moves between states
- **Permission Matrix**: What each role can do in each state
- **Required Roles**: Which roles must be assigned
- **Validation Requirements**: Conditions for successful application

### Template Validation

Before applying a template, the system validates:

1. **Role Availability**: All required roles exist in your system
2. **Permission Mapping**: All permissions map correctly to Plone
3. **User Assignments**: Required roles have assigned users
4. **Content Compatibility**: Target content supports workflow

## Applying Workflows to Content

### Pre-Application Checklist

Before applying a workflow template:

- [ ] Content item exists and is accessible
- [ ] Required users are available for role assignment
- [ ] Template is appropriate for content type
- [ ] Backup strategy is in place (if needed)

### Step-by-Step Application Process

#### 1. Select Content and Template

**Web Interface:**
1. Navigate to **Content Management**
2. Select the content item
3. Click **Apply Workflow** → Choose template

**API Call:**
```bash
curl -X POST "https://api.eduhub.edu/workflows/apply/simple_review?content_uid=content-123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_assignments": {
      "author": ["user1", "user2"],
      "editor": ["editor1"],
      "administrator": ["admin1"]
    },
    "force": false
  }'
```

#### 2. Configure Role Assignments

Assign users to each required role:

**Author Role:**
- Content creators and writers
- Can edit content in draft state
- Can submit content for review

**Editor Role:**
- Content reviewers and editors
- Can approve/reject submissions
- Can publish approved content

**Administrator Role:**
- Full workflow control
- Can override transitions
- Can modify role assignments

#### 3. Review and Confirm

Before final application:

1. **Validation Results**: Check for any warnings or errors
2. **Permission Preview**: Review what permissions will be applied
3. **Backup Options**: Decide whether to create backup of existing workflow
4. **Impact Assessment**: Understand what will change

#### 4. Monitor Application Progress

Track the application process:

- **Real-time Status**: Progress indicators during application
- **Validation Feedback**: Any issues encountered
- **Success Confirmation**: Final status and next steps

### Example: Applying Simple Review Template

```json
{
  "template_id": "simple_review",
  "content_uid": "course-material-123",
  "role_assignments": {
    "author": ["john.doe", "jane.smith"],
    "editor": ["mary.jones"],
    "administrator": ["admin.user"]
  },
  "configuration": {
    "backup_existing": true,
    "notify_users": true,
    "force_override": false
  }
}
```

Expected workflow:
1. **Draft State**: Authors can edit, submit for review
2. **Review State**: Editor can approve or reject
3. **Published State**: Content is live and read-only

## Managing Content Lifecycle

### Understanding Content States

#### Draft State
- **Purpose**: Content creation and initial editing
- **Who Can Access**: Authors, editors, administrators
- **Available Actions**: Edit, delete, submit for review
- **Restrictions**: Not visible to general users

#### Review/Pending State
- **Purpose**: Content evaluation and approval
- **Who Can Access**: Editors, administrators, original authors (read-only)
- **Available Actions**: Approve, reject, request changes
- **Restrictions**: Content locked from editing

#### Published State
- **Purpose**: Content is live and accessible
- **Who Can Access**: All users (based on content permissions)
- **Available Actions**: Retract, archive, create new version
- **Restrictions**: Cannot be edited directly

### Executing State Transitions

#### Web Interface
1. Open content item
2. Go to **Workflow** tab
3. Select available transition
4. Add comments (if required)
5. Click **Execute Transition**

#### API Call
```bash
curl -X POST "https://api.eduhub.edu/workflows/transition" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_uid": "content-123",
    "transition_id": "submit",
    "comments": "Content is ready for editorial review"
  }'
```

### Common Workflow Scenarios

#### Scenario 1: Standard Content Publication
```
Draft → Submit → Review → Approve → Published
```

1. **Author creates content** (Draft state)
2. **Author submits for review** (→ Pending state)
3. **Editor reviews and approves** (→ Published state)

#### Scenario 2: Content Rejection and Revision
```
Draft → Submit → Review → Reject → Draft → Submit → Approve → Published
```

1. **Author submits content**
2. **Editor rejects with feedback**
3. **Author revises content**
4. **Author resubmits**
5. **Editor approves**

#### Scenario 3: Emergency Content Retraction
```
Published → Retract → Draft → Revise → Republish
```

1. **Administrator retracts published content**
2. **Author makes necessary changes**
3. **Content goes through review process again**

### Monitoring Content Progress

#### Workflow History
View complete history of state changes:

```bash
curl -X GET "https://api.eduhub.edu/workflows/content/content-123/state" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Progress Tracking
- **Current State**: Where content currently resides
- **Next Actions**: Available transitions for current user
- **Timeline**: Duration in each state
- **Bottlenecks**: Identification of delays

## Role-Based Permissions

### Understanding Educational Roles

#### Author
**Typical Users**: Faculty, instructional designers, content creators

**Permissions by State**:
- **Draft**: Edit, delete, submit
- **Review**: View only, respond to feedback
- **Published**: View only

**Responsibilities**:
- Create and edit content
- Ensure content quality
- Respond to reviewer feedback

#### Peer Reviewer
**Typical Users**: Subject matter experts, fellow faculty

**Permissions by State**:
- **Draft**: View only (if assigned)
- **Review**: Approve, reject, comment
- **Published**: View only

**Responsibilities**:
- Evaluate content accuracy
- Provide expert feedback
- Approve/reject based on standards

#### Editor
**Typical Users**: Editorial staff, content managers

**Permissions by State**:
- **Draft**: Edit, delete, submit
- **Review**: Approve, reject, modify, comment
- **Published**: Retract, archive

**Responsibilities**:
- Manage workflow process
- Ensure editorial standards
- Coordinate between authors and reviewers

#### Subject Expert
**Typical Users**: Department heads, specialized faculty

**Permissions by State**:
- **Draft**: View, comment
- **Review**: Approve, reject, provide expert opinion
- **Published**: View, recommend updates

**Responsibilities**:
- Provide domain expertise
- Validate technical accuracy
- Recommend improvements

#### Publisher
**Typical Users**: Publication managers, release coordinators

**Permissions by State**:
- **Review**: View, comment
- **Pre-Publication**: Final approval, formatting
- **Published**: Manage distribution, retract if necessary

**Responsibilities**:
- Final publication approval
- Manage release process
- Handle post-publication issues

#### Administrator
**Typical Users**: System administrators, workflow managers

**Permissions by State**:
- **All States**: Full access to all actions

**Responsibilities**:
- Manage workflow configuration
- Handle exceptional cases
- Maintain system integrity

### Managing Role Assignments

#### Adding Users to Roles

**Web Interface**:
1. Go to **Content** → **Workflow** → **Roles**
2. Select role → **Add Users**
3. Search and select users
4. Set effective dates (if applicable)

**API Call**:
```bash
curl -X POST "https://api.eduhub.edu/workflows/content/content-123/roles" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_assignments": {
      "author": ["new.author@university.edu"],
      "editor": ["senior.editor@university.edu"]
    }
  }'
```

#### Removing Users from Roles

**Process**:
1. Navigate to role assignments
2. Select user to remove
3. Confirm removal
4. System automatically audits the change

**Considerations**:
- **Active Tasks**: Ensure user has no pending actions
- **Historical Record**: User's actions remain in audit trail
- **Replacement**: Assign replacement user if necessary

### Permission Validation

The system automatically validates:

1. **Role Coverage**: All required roles have assigned users
2. **Conflict Resolution**: No conflicting permissions
3. **Escalation Paths**: Clear routes for issue resolution
4. **Backup Coverage**: Multiple users for critical roles

## Monitoring and Auditing

### Audit Trail Features

#### Complete Activity Log
Every workflow action is logged:

- **User Actions**: Who performed what action when
- **State Changes**: All transitions with timestamps
- **Permission Changes**: Role assignment modifications
- **System Events**: Automated actions and validations

#### Audit Log Example
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "operation": "execute_transition",
  "user_id": "john.doe",
  "content_uid": "content-123",
  "transition_id": "submit",
  "from_state": "draft",
  "to_state": "pending",
  "comments": "Ready for editorial review",
  "success": true
}
```

### Monitoring Dashboard

#### Key Metrics
- **Active Workflows**: Number of content items in each state
- **Processing Time**: Average time in each state
- **User Activity**: Most active users and their actions
- **Success Rates**: Percentage of successful transitions

#### Performance Indicators
- **Bottlenecks**: States where content gets stuck
- **Efficiency**: Time from draft to publication
- **Quality**: Rejection rates and reasons
- **User Engagement**: Participation by role

### Generating Reports

#### Web Interface
1. Go to **Reports** → **Workflow Analytics**
2. Select date range and filters
3. Choose report type
4. Generate and download

#### Available Report Types

**Activity Summary**:
- Total actions by time period
- User activity breakdown
- State distribution

**Performance Analysis**:
- Average processing times
- Bottleneck identification
- Efficiency trends

**Audit Report**:
- Complete action history
- User access patterns
- Permission changes

**Compliance Report**:
- Workflow adherence
- Security compliance
- Data retention compliance

### Real-Time Monitoring

#### Dashboard Views
- **Live Activity Feed**: Real-time workflow actions
- **State Distribution**: Current content distribution
- **User Activity**: Who's working on what
- **System Health**: Performance and availability

#### Alerts and Notifications
- **Overdue Reviews**: Content pending too long
- **System Issues**: Performance or connectivity problems
- **Policy Violations**: Unusual activity patterns
- **Capacity Warnings**: High system load

## Troubleshooting

### Common Issues and Solutions

#### Template Application Failures

**Issue**: "Role validation failed"
```
Error: Role 'peer_reviewer' has no assigned users
```

**Solution**:
1. Check available users in your system
2. Assign users to the missing role
3. Retry template application

**Prevention**:
- Always verify role assignments before application
- Maintain user directory synchronization

#### Permission Errors

**Issue**: "User lacks workflow management permissions"
```
Error: User 'john.doe' cannot execute transition 'approve'
```

**Solution**:
1. Verify user's current role assignments
2. Check if user is in correct role for the action
3. Escalate to administrator if needed

**Prevention**:
- Regular permission audits
- Clear role documentation
- User training on workflow roles

#### Content State Issues

**Issue**: "Content stuck in review state"
```
Issue: Content has been in 'pending' state for 30 days
```

**Solution**:
1. Check assigned reviewers' availability
2. Send reminder notifications
3. Escalate to administrator for forced transition
4. Review workflow design for bottlenecks

**Prevention**:
- Set up automated reminders
- Define SLA for each state
- Cross-train multiple users per role

#### Integration Problems

**Issue**: "Plone connection failed"
```
Error: Cannot connect to Plone instance at https://cms.university.edu
```

**Solution**:
1. Check Plone server status
2. Verify network connectivity
3. Validate authentication credentials
4. Check for maintenance windows

**Prevention**:
- Monitor Plone health regularly
- Maintain backup credentials
- Set up automated health checks

### Diagnostic Tools

#### Health Check Endpoint
```bash
curl -X GET "https://api.eduhub.edu/workflows/health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response indicates**:
- Template loading status
- Plone connectivity
- Database health
- Audit logging status

#### Workflow State Validation
```bash
curl -X GET "https://api.eduhub.edu/workflows/content/content-123/validate" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Checks for**:
- Valid current state
- Available transitions
- Role assignment completeness
- Permission consistency

### Getting Help

#### Support Channels

**Self-Service**:
- This user guide
- API documentation
- Video tutorials
- FAQ section

**Community Support**:
- User forums
- Knowledge base
- User groups
- Best practices sharing

**Professional Support**:
- Help desk tickets
- Email support
- Phone support
- On-site training

#### When to Contact Support

**Immediate Support** (Contact right away):
- System outages
- Data corruption
- Security incidents
- Critical workflow failures

**Standard Support** (Within business hours):
- Configuration questions
- User training needs
- Feature requests
- Performance optimization

**Self-Service First** (Try documentation):
- Basic usage questions
- Common error messages
- Standard procedures
- General troubleshooting

## Advanced Scenarios

### Custom Template Creation

For organizations needing specialized workflows:

#### Template Design Process
1. **Requirements Analysis**: Define states, transitions, and roles
2. **Permission Mapping**: Map educational roles to actions
3. **Validation Rules**: Define state transition conditions
4. **Testing Phase**: Pilot with sample content
5. **Deployment**: Roll out to production

#### Example Custom Template: Grant Proposal Workflow
```json
{
  "id": "grant_proposal",
  "name": "Grant Proposal Review",
  "states": [
    {
      "id": "preparation",
      "name": "Preparation",
      "permissions": [
        {"role": "author", "actions": ["edit", "collaborate"]},
        {"role": "administrator", "actions": ["view", "edit"]}
      ]
    },
    {
      "id": "internal_review",
      "name": "Internal Review",
      "permissions": [
        {"role": "peer_reviewer", "actions": ["review", "comment"]},
        {"role": "subject_expert", "actions": ["review", "approve"]}
      ]
    },
    {
      "id": "submission_ready",
      "name": "Ready for Submission",
      "permissions": [
        {"role": "publisher", "actions": ["submit", "finalize"]},
        {"role": "administrator", "actions": ["override", "submit"]}
      ]
    }
  ],
  "transitions": [
    {
      "id": "submit_for_review",
      "from_state": "preparation",
      "to_state": "internal_review",
      "required_role": "author"
    },
    {
      "id": "approve_for_submission",
      "from_state": "internal_review",
      "to_state": "submission_ready",
      "required_role": "subject_expert"
    }
  ]
}
```

### Bulk Operations

For managing multiple content items:

#### Bulk Template Application
```bash
curl -X POST "https://api.eduhub.edu/workflows/bulk-apply" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "simple_review",
    "content_assignments": [
      {
        "content_uid": "content-1",
        "role_assignments": {
          "author": ["user1"],
          "editor": ["editor1"]
        }
      },
      {
        "content_uid": "content-2",
        "role_assignments": {
          "author": ["user2"],
          "editor": ["editor1"]
        }
      }
    ],
    "max_concurrent": 5
  }'
```

#### Bulk State Transitions
For moving multiple items through the same transition:

```python
# Python example
from eduhub_client import WorkflowClient

client = WorkflowClient(token="your_token")

# Get all content in 'pending' state
pending_content = client.content.list(state="pending")

# Bulk approve content
results = client.transitions.bulk_execute(
    transition_id="approve",
    content_uids=[item.uid for item in pending_content],
    comments="Batch approval for course materials"
)
```

### Integration with External Systems

#### Learning Management System (LMS) Integration
```python
# Example: Automatically publish approved content to LMS
def on_content_published(content_uid, workflow_data):
    # Get content details
    content = cms.get_content(content_uid)

    # Create LMS course module
    lms_module = lms.create_module(
        course_id=content.course_id,
        title=content.title,
        content=content.body,
        visibility="published"
    )

    # Update content with LMS reference
    cms.update_metadata(content_uid, {
        "lms_module_id": lms_module.id,
        "published_url": lms_module.url
    })
```

#### Quality Assurance Integration
```python
# Example: Automated quality checks before publication
def pre_publication_qa(content_uid):
    qa_results = {
        "spell_check": spell_checker.check(content_uid),
        "link_validation": link_validator.check(content_uid),
        "accessibility": accessibility_checker.check(content_uid),
        "style_guide": style_checker.check(content_uid)
    }

    if all(result.passed for result in qa_results.values()):
        # Automatically proceed to publication
        workflow.execute_transition(
            content_uid=content_uid,
            transition_id="qa_approved",
            comments="Automated QA checks passed"
        )
    else:
        # Send back for revision
        workflow.execute_transition(
            content_uid=content_uid,
            transition_id="qa_failed",
            comments=f"QA Issues: {qa_results}"
        )
```

### Performance Optimization

#### Large-Scale Deployments

For institutions managing thousands of content items:

**Database Optimization**:
- Index workflow state fields
- Archive old audit logs
- Optimize permission queries

**Caching Strategy**:
- Cache template definitions
- Cache user role assignments
- Cache permission matrices

**Load Balancing**:
- Distribute API requests
- Separate read/write operations
- Queue background tasks

#### Monitoring Performance
```bash
# Check workflow performance metrics
curl -X GET "https://api.eduhub.edu/workflows/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Key Metrics to Monitor**:
- Average transition time
- Template application success rate
- User response times
- System resource usage

### Security Best Practices

#### Access Control
- **Principle of Least Privilege**: Grant minimum necessary permissions
- **Regular Audits**: Review user assignments quarterly
- **Role Segregation**: Separate authoring and approval roles
- **Emergency Procedures**: Define break-glass processes

#### Data Protection
- **Audit Log Integrity**: Protect logs from modification
- **Sensitive Content**: Additional approval for confidential material
- **Retention Policies**: Define data retention periods
- **Backup Procedures**: Regular backup of workflow configurations

#### Compliance Considerations
- **Educational Standards**: Ensure workflows meet institutional requirements
- **Regulatory Compliance**: Address FERPA, GDPR, and other regulations
- **Documentation**: Maintain procedure documentation
- **Training Records**: Track user training completion

---

## Conclusion

This user guide provides comprehensive coverage of the EduHub Workflow Management system. For additional support:

- **Quick Start**: Begin with simple templates and basic scenarios
- **Gradual Adoption**: Roll out workflows incrementally across departments
- **User Training**: Ensure all stakeholders understand their roles
- **Continuous Improvement**: Regularly review and optimize workflows

The workflow system is designed to grow with your institution's needs. Start with built-in templates and gradually customize as your requirements evolve.

### Next Steps

1. **Identify Use Cases**: Determine which content needs workflow management
2. **Select Templates**: Choose appropriate templates for your content types
3. **Assign Roles**: Map institutional roles to workflow permissions
4. **Pilot Program**: Start with a small group of content and users
5. **Scale Gradually**: Expand to additional content and user groups
6. **Monitor and Optimize**: Use analytics to improve processes

For technical support or additional training, contact the EduHub support team.
