"""
Built-in workflow templates for educational content management.

This module provides pre-defined workflow templates that cover common
educational use cases, from simple review processes to complex multi-stage
approval workflows.
"""

from typing import Any, Dict, List, Union

from .models import (
    EducationRole,
    StateType,
    WorkflowAction,
    WorkflowPermission,
    WorkflowState,
    WorkflowTemplate,
    WorkflowTransition,
)


def create_simple_review_template() -> WorkflowTemplate:
    """
    Create a basic 3-state workflow for simple educational content.

    Flow: Draft -> Review -> Published

    Perfect for:
    - Course materials and assignments
    - Simple educational resources
    - Documents that need basic quality control
    - Content with 1-2 reviewers maximum

    Roles involved:
    - Author: Creates and edits content
    - Editor: Reviews and approves content
    - Administrator: Full management rights
    """

    # Define states
    draft_state = WorkflowState(
        id="draft",
        title="Draft",
        description="Content is being created or edited by the author. Authors have full editing rights and can submit for review when ready.",
        state_type=StateType.DRAFT,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.SUBMIT,
                },
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.DELETE,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=True,
        is_final=False,
        ui_metadata={
            "color": "#94a3b8",
            "icon": "edit",
            "description_short": "Being written",
        },
    )

    review_state = WorkflowState(
        id="review",
        title="Under Review",
        description="Content is being reviewed by qualified reviewers. Authors cannot edit during review but can view progress. Reviewers can approve, reject, or request revisions.",
        state_type=StateType.REVIEW,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.EDITOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.REVIEW,
                    WorkflowAction.APPROVE,
                    WorkflowAction.REJECT,
                },
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.REVIEW,
                    WorkflowAction.APPROVE,
                    WorkflowAction.REJECT,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=False,
        is_final=False,
        ui_metadata={
            "color": "#fbbf24",
            "icon": "clock",
            "description_short": "Under review",
        },
    )

    published_state = WorkflowState(
        id="published",
        title="Published",
        description="Content is approved and publicly available. Only administrators can make changes or retract published content.",
        state_type=StateType.PUBLISHED,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.EDITOR, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.VIEWER, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.RETRACT,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=False,
        is_final=True,
        ui_metadata={
            "color": "#10b981",
            "icon": "check-circle",
            "description_short": "Live",
        },
    )

    # Define transitions
    transitions = [
        WorkflowTransition(
            id="submit_for_review",
            title="Submit for Review",
            from_state="draft",
            to_state="review",
            required_role=EducationRole.AUTHOR,
            conditions={"require_comments": False, "min_content_length": 50},
        ),
        WorkflowTransition(
            id="approve_content",
            title="Approve and Publish",
            from_state="review",
            to_state="published",
            required_role=EducationRole.EDITOR,
            conditions={"require_comments": True},
        ),
        WorkflowTransition(
            id="reject_to_draft",
            title="Reject - Return to Draft",
            from_state="review",
            to_state="draft",
            required_role=EducationRole.EDITOR,
            conditions={"require_comments": True, "require_feedback": True},
        ),
    ]

    # Default permissions applied across all states
    default_permissions = {
        EducationRole.ADMINISTRATOR: {
            WorkflowAction.VIEW,
            WorkflowAction.EDIT,
            WorkflowAction.DELETE,
            WorkflowAction.MANAGE_WORKFLOW,
            WorkflowAction.ASSIGN_ROLES,
        },
        EducationRole.VIEWER: {WorkflowAction.VIEW},
    }

    return WorkflowTemplate(
        id="simple_review",
        name="Simple Review Workflow",
        description="A basic 3-state workflow designed for educational content that requires author creation, reviewer approval, and publication. Perfect for course materials, assignments, and educational resources that need quality control but don't require complex multi-stage review processes.",
        version="1.0.0",
        category="educational",
        states=[draft_state, review_state, published_state],
        transitions=transitions,
        default_permissions=default_permissions,
        metadata={
            "complexity": "simple",
            "recommended_for": [
                "course_materials",
                "assignments",
                "educational_resources",
                "simple_documents",
            ],
            "typical_duration": "2-5 days",
            "min_participants": 2,
            "max_participants": 10,
            "tags": ["basic", "educational", "review"],
        },
    )


def create_extended_review_template() -> WorkflowTemplate:
    """
    Create a comprehensive 5-state workflow for complex educational content.

    Flow: Draft -> Peer Review -> Editorial Review -> Approved -> Published -> (Archived)

    Perfect for:
    - Research papers and academic content
    - Complex curriculum materials
    - Multi-contributor educational resources
    - Content requiring subject matter expert validation

    Roles involved:
    - Author: Creates and edits content
    - Peer Reviewer: First-stage technical review
    - Subject Expert: Domain expertise validation
    - Editor: Final editorial review and approval
    - Publisher: Publication management
    - Administrator: Full management rights
    """

    # Define states
    draft_state = WorkflowState(
        id="draft",
        title="Draft",
        description="Content is being created or edited by the author. Authors can collaborate and make changes before submitting for peer review.",
        state_type=StateType.DRAFT,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.SUBMIT,
                },
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.DELETE,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=True,
        is_final=False,
        ui_metadata={
            "color": "#94a3b8",
            "icon": "edit",
            "description_short": "In development",
        },
    )

    peer_review_state = WorkflowState(
        id="peer_review",
        title="Peer Review",
        description="Content is being reviewed by peers for technical accuracy and initial feedback. Multiple peer reviewers can provide input simultaneously.",
        state_type=StateType.REVIEW,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.PEER_REVIEWER,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.REVIEW,
                    WorkflowAction.APPROVE,
                    WorkflowAction.REJECT,
                },
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.REVIEW,
                    WorkflowAction.APPROVE,
                    WorkflowAction.REJECT,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=False,
        is_final=False,
        ui_metadata={
            "color": "#f59e0b",
            "icon": "users",
            "description_short": "Peer review",
        },
    )

    editorial_review_state = WorkflowState(
        id="editorial_review",
        title="Editorial Review",
        description="Content is being reviewed by subject matter experts and editors for final quality assurance and editorial standards.",
        state_type=StateType.REVIEW,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.SUBJECT_EXPERT,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.REVIEW,
                    WorkflowAction.APPROVE,
                    WorkflowAction.REJECT,
                },
            ),
            WorkflowPermission(
                role=EducationRole.EDITOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.REVIEW,
                    WorkflowAction.APPROVE,
                    WorkflowAction.REJECT,
                },
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.REVIEW,
                    WorkflowAction.APPROVE,
                    WorkflowAction.REJECT,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=False,
        is_final=False,
        ui_metadata={
            "color": "#d97706",
            "icon": "check-circle",
            "description_short": "Editorial review",
        },
    )

    approved_state = WorkflowState(
        id="approved",
        title="Approved",
        description="Content has passed all review stages and is approved for publication. Awaiting final publication scheduling.",
        state_type=StateType.APPROVED,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.PUBLISHER,
                actions={WorkflowAction.VIEW, WorkflowAction.PUBLISH},
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.PUBLISH,
                    WorkflowAction.RETRACT,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=False,
        is_final=False,
        ui_metadata={
            "color": "#059669",
            "icon": "check-badge",
            "description_short": "Ready to publish",
        },
    )

    published_state = WorkflowState(
        id="published",
        title="Published",
        description="Content is live and publicly available. Changes require special approval and versioning.",
        state_type=StateType.PUBLISHED,
        permissions=[
            WorkflowPermission(
                role=EducationRole.AUTHOR, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.VIEWER, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.PUBLISHER,
                actions={WorkflowAction.VIEW, WorkflowAction.RETRACT},
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={
                    WorkflowAction.VIEW,
                    WorkflowAction.EDIT,
                    WorkflowAction.RETRACT,
                    WorkflowAction.MANAGE_WORKFLOW,
                },
            ),
        ],
        is_initial=False,
        is_final=False,
        ui_metadata={"color": "#10b981", "icon": "globe", "description_short": "Live"},
    )

    archived_state = WorkflowState(
        id="archived",
        title="Archived",
        description="Content is no longer active but preserved for historical reference. Read-only access only.",
        state_type=StateType.ARCHIVED,
        permissions=[
            WorkflowPermission(
                role=EducationRole.VIEWER, actions={WorkflowAction.VIEW}
            ),
            WorkflowPermission(
                role=EducationRole.ADMINISTRATOR,
                actions={WorkflowAction.VIEW, WorkflowAction.MANAGE_WORKFLOW},
            ),
        ],
        is_initial=False,
        is_final=True,
        ui_metadata={
            "color": "#6b7280",
            "icon": "archive",
            "description_short": "Archived",
        },
    )

    # Define transitions
    transitions = [
        WorkflowTransition(
            id="submit_for_peer_review",
            title="Submit for Peer Review",
            from_state="draft",
            to_state="peer_review",
            required_role=EducationRole.AUTHOR,
            conditions={"require_comments": False, "min_content_length": 500},
        ),
        WorkflowTransition(
            id="peer_review_to_editorial",
            title="Forward to Editorial Review",
            from_state="peer_review",
            to_state="editorial_review",
            required_role=EducationRole.PEER_REVIEWER,
            conditions={"require_comments": True, "min_peer_reviews": 2},
        ),
        WorkflowTransition(
            id="peer_review_reject",
            title="Reject - Return to Draft",
            from_state="peer_review",
            to_state="draft",
            required_role=EducationRole.PEER_REVIEWER,
            conditions={"require_comments": True, "require_feedback": True},
        ),
        WorkflowTransition(
            id="editorial_approve",
            title="Editorial Approval",
            from_state="editorial_review",
            to_state="approved",
            required_role=EducationRole.EDITOR,
            conditions={
                "require_comments": True,
                "require_subject_expert_approval": True,
            },
        ),
        WorkflowTransition(
            id="editorial_reject",
            title="Editorial Rejection",
            from_state="editorial_review",
            to_state="draft",
            required_role=EducationRole.EDITOR,
            conditions={"require_comments": True, "require_detailed_feedback": True},
        ),
        WorkflowTransition(
            id="publish_content",
            title="Publish Content",
            from_state="approved",
            to_state="published",
            required_role=EducationRole.PUBLISHER,
            conditions={"require_publication_checklist": True},
        ),
        WorkflowTransition(
            id="archive_content",
            title="Archive Content",
            from_state="published",
            to_state="archived",
            required_role=EducationRole.ADMINISTRATOR,
            conditions={"require_archive_reason": True},
        ),
    ]

    # Default permissions applied across all states
    default_permissions = {
        EducationRole.ADMINISTRATOR: {
            WorkflowAction.VIEW,
            WorkflowAction.EDIT,
            WorkflowAction.DELETE,
            WorkflowAction.MANAGE_WORKFLOW,
            WorkflowAction.ASSIGN_ROLES,
        },
        EducationRole.VIEWER: {WorkflowAction.VIEW},
    }

    return WorkflowTemplate(
        id="extended_review",
        name="Extended Review Workflow",
        description="A comprehensive 6-state workflow for complex educational content requiring multiple review stages, subject matter expert validation, and careful publication management. Designed for academic papers, research content, and high-quality educational materials.",
        version="1.0.0",
        category="educational",
        states=[
            draft_state,
            peer_review_state,
            editorial_review_state,
            approved_state,
            published_state,
            archived_state,
        ],
        transitions=transitions,
        default_permissions=default_permissions,
        metadata={
            "complexity": "advanced",
            "recommended_for": [
                "research_papers",
                "academic_content",
                "complex_curriculum",
                "multi_contributor_resources",
                "high_quality_materials",
            ],
            "typical_duration": "2-8 weeks",
            "min_participants": 4,
            "max_participants": 50,
            "tags": ["advanced", "research", "academic", "multi-stage"],
        },
    )


# Registry of all available templates
AVAILABLE_TEMPLATES: dict[str, WorkflowTemplate] = {
    "simple_review": create_simple_review_template(),
    "extended_review": create_extended_review_template(),
}


def get_template(template_id: str) -> WorkflowTemplate:
    """
    Get a workflow template by ID.

    Args:
        template_id: Unique identifier for the template

    Returns:
        WorkflowTemplate instance

    Raises:
        KeyError: If template_id is not found
    """
    if template_id not in AVAILABLE_TEMPLATES:
        available = ", ".join(AVAILABLE_TEMPLATES.keys())
        raise KeyError(
            f"Template '{template_id}' not found. Available templates: {available}"
        )

    return AVAILABLE_TEMPLATES[template_id]


def list_templates() -> list[dict[str, Union[str, int]]]:
    """
    Get a summary of all available workflow templates.

    Returns:
        List of template metadata dictionaries
    """
    templates = []
    for template_id, template in AVAILABLE_TEMPLATES.items():
        templates.append(
            {
                "id": template_id,
                "name": template.name,
                "description": template.description,
                "complexity": (
                    template.metadata.get("complexity", "unknown")
                    if template.metadata
                    else "unknown"
                ),
                "category": template.category,
                "states_count": len(template.states),
                "transitions_count": len(template.transitions),
            }
        )
    return templates


def get_template_by_complexity(complexity: str) -> list[WorkflowTemplate]:
    """
    Get templates filtered by complexity level.

    Args:
        complexity: Complexity level ("simple", "advanced", etc.)

    Returns:
        List of matching workflow templates
    """
    matching_templates = []
    for template in AVAILABLE_TEMPLATES.values():
        if template.metadata and template.metadata.get("complexity") == complexity:
            matching_templates.append(template)

    return matching_templates


def validate_all_templates() -> bool:
    """
    Validate all built-in templates for consistency.

    Returns:
        True if all templates are valid, False otherwise
    """
    try:
        for template_id, template in AVAILABLE_TEMPLATES.items():
            # The template creation already validates through Pydantic
            # This is just to ensure we can access all templates without errors
            assert template.id == template_id
            assert len(template.states) >= 2
            assert len(template.transitions) >= 1
            assert any(state.is_initial for state in template.states)
            assert any(state.is_final for state in template.states)

        return True
    except Exception as e:
        print(f"Template validation failed: {e}")
        return False
