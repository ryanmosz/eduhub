"""
Pydantic models for workflow template definitions.

Workflow concepts in Plone:
- States: Discrete workflow states (draft, review, published, etc.)
- Transitions: Actions that move content between states
- Permissions: What roles can do in each state (view, edit, review, etc.)
- Roles: User groups with specific capabilities (author, reviewer, manager, etc.)

Educational workflow patterns:
- Simple Review: Draft -> Review -> Published -> Archived
- Extended Review: Draft -> Peer Review -> Editorial Review -> Published -> Archived
- Collaborative: Draft -> Review -> Revision -> Final Review -> Published
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class WorkflowAction(str, Enum):
    """Standard workflow actions/permissions in educational contexts."""

    # Content permissions
    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"

    # Workflow permissions
    SUBMIT = "submit"
    REVIEW = "review"
    APPROVE = "approve"
    PUBLISH = "publish"
    REJECT = "reject"
    RETRACT = "retract"

    # Administrative permissions
    MANAGE_WORKFLOW = "manage_workflow"
    ASSIGN_ROLES = "assign_roles"


class EducationRole(str, Enum):
    """Standard roles in educational content workflows."""

    AUTHOR = "author"
    PEER_REVIEWER = "peer_reviewer"
    EDITOR = "editor"
    SUBJECT_EXPERT = "subject_expert"
    PUBLISHER = "publisher"
    ADMINISTRATOR = "administrator"
    VIEWER = "viewer"


class StateType(str, Enum):
    """Types of workflow states for UI and logic purposes."""

    DRAFT = "draft"  # Initial creation state
    REVIEW = "review"  # Under review
    REVISION = "revision"  # Needs changes
    APPROVED = "approved"  # Approved but not published
    PUBLISHED = "published"  # Live/public
    ARCHIVED = "archived"  # No longer active
    REJECTED = "rejected"  # Permanently rejected


class WorkflowPermission(BaseModel):
    """Permission mapping for a specific role in a workflow state."""

    role: EducationRole = Field(
        ...,
        description="The role this permission applies to",
        examples=[EducationRole.AUTHOR, EducationRole.PEER_REVIEWER],
    )

    actions: set[WorkflowAction] = Field(
        default_factory=set,
        description="Set of actions this role can perform in this state",
        examples=[{WorkflowAction.VIEW, WorkflowAction.EDIT}],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"role": "author", "actions": ["view", "edit", "submit"]},
                {
                    "role": "peer_reviewer",
                    "actions": ["view", "review", "approve", "reject"],
                },
            ]
        }
    }


class WorkflowTransition(BaseModel):
    """Defines a transition between workflow states."""

    id: str = Field(
        ...,
        description="Unique identifier for this transition",
        examples=["submit_for_review", "approve_content", "publish_content"],
    )

    title: str = Field(
        ...,
        description="Human-readable title for this transition",
        examples=["Submit for Review", "Approve Content", "Publish Content"],
    )

    from_state: str = Field(
        ...,
        description="Source state ID for this transition",
        examples=["draft", "review", "approved"],
    )

    to_state: str = Field(
        ...,
        description="Target state ID for this transition",
        examples=["review", "approved", "published"],
    )

    required_role: EducationRole = Field(
        ...,
        description="Role required to execute this transition",
        examples=[EducationRole.AUTHOR, EducationRole.PEER_REVIEWER],
    )

    conditions: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional conditions that must be met for transition",
        examples=[{"min_reviewers": 2, "require_comments": True}],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "submit_for_review",
                    "title": "Submit for Review",
                    "from_state": "draft",
                    "to_state": "review",
                    "required_role": "author",
                    "conditions": {"require_comments": False},
                }
            ]
        }
    }


class WorkflowState(BaseModel):
    """Represents a single state in a workflow."""

    id: str = Field(
        ...,
        description="Unique identifier for this state",
        examples=["draft", "review", "published", "archived"],
    )

    title: str = Field(
        ...,
        description="Human-readable title for this state",
        examples=["Draft", "Under Review", "Published", "Archived"],
    )

    description: Optional[str] = Field(
        default=None,
        description="Detailed description of what this state represents",
        examples=["Content is being created or edited by the author"],
    )

    state_type: StateType = Field(
        ...,
        description="Semantic type of this state for UI and logic purposes",
        examples=[StateType.DRAFT, StateType.REVIEW, StateType.PUBLISHED],
    )

    permissions: list[WorkflowPermission] = Field(
        default_factory=list,
        description="List of role-based permissions for this state",
    )

    is_initial: bool = Field(
        default=False, description="Whether this is the initial state for new content"
    )

    is_final: bool = Field(
        default=False,
        description="Whether this is a terminal state (no outgoing transitions)",
    )

    ui_metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="UI hints like colors, icons, etc.",
        examples=[{"color": "#ffa500", "icon": "edit"}],
    )

    @field_validator("id")
    @classmethod
    def validate_state_id(cls, v: str) -> str:
        """Ensure state ID follows naming conventions."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("State ID must be alphanumeric with underscores/hyphens")
        if len(v) < 2:
            raise ValueError("State ID must be at least 2 characters")
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "draft",
                    "title": "Draft",
                    "description": "Content is being created or edited",
                    "state_type": "draft",
                    "permissions": [
                        {"role": "author", "actions": ["view", "edit", "submit"]}
                    ],
                    "is_initial": True,
                    "is_final": False,
                    "ui_metadata": {"color": "#94a3b8", "icon": "edit"},
                }
            ]
        }
    }


class WorkflowTemplate(BaseModel):
    """Complete workflow template definition."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this template",
        examples=["simple_review", "extended_review", "collaborative_review"],
    )

    name: str = Field(
        ...,
        description="Human-readable name for this template",
        examples=["Simple Review Workflow", "Extended Review Workflow"],
    )

    description: str = Field(
        ..., description="Detailed description of the workflow purpose and use cases"
    )

    version: str = Field(
        default="1.0.0",
        description="Semantic version of this template",
        examples=["1.0.0", "2.1.3"],
    )

    category: str = Field(
        default="educational",
        description="Category or domain this workflow is designed for",
        examples=["educational", "corporate", "research", "publishing"],
    )

    states: list[WorkflowState] = Field(
        ..., description="List of all states in this workflow", min_length=2
    )

    transitions: list[WorkflowTransition] = Field(
        ..., description="List of all possible transitions between states", min_length=1
    )

    default_permissions: dict[EducationRole, set[WorkflowAction]] = Field(
        default_factory=dict,
        description="Default permissions applied across all states",
    )

    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional metadata like complexity, recommended usage, etc.",
        examples=[{"complexity": "simple", "recommended_for": ["course_materials"]}],
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this template was created"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is descriptive."""
        if len(v.strip()) < 3:
            raise ValueError("Workflow name must be at least 3 characters")
        return v.strip()

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Ensure version follows semantic versioning."""
        parts = v.split(".")
        if len(parts) != 3:
            raise ValueError("Version must follow semantic versioning (x.y.z)")
        if not all(part.isdigit() for part in parts):
            raise ValueError("Version parts must be integers")
        return v

    @model_validator(mode="after")
    def validate_workflow_integrity(self) -> "WorkflowTemplate":
        """Validate the entire workflow for consistency."""
        state_ids = {state.id for state in self.states}

        # Validate exactly one initial state
        initial_states = [s for s in self.states if s.is_initial]
        if len(initial_states) != 1:
            raise ValueError("Workflow must have exactly one initial state")

        # Validate at least one final state
        final_states = [s for s in self.states if s.is_final]
        if not final_states:
            raise ValueError("Workflow must have at least one final state")

        # Validate all transition states exist
        for transition in self.transitions:
            if transition.from_state not in state_ids:
                raise ValueError(
                    f"Transition references unknown from_state: {transition.from_state}"
                )
            if transition.to_state not in state_ids:
                raise ValueError(
                    f"Transition references unknown to_state: {transition.to_state}"
                )

        # Validate no final states have outgoing transitions
        final_state_ids = {s.id for s in final_states}
        for transition in self.transitions:
            if transition.from_state in final_state_ids:
                raise ValueError(
                    f"Final state {transition.from_state} cannot have outgoing transitions"
                )

        # Validate all non-final states are reachable
        initial_state_id = initial_states[0].id
        reachable_states = self._find_reachable_states(initial_state_id)
        non_final_state_ids = state_ids - final_state_ids

        unreachable = non_final_state_ids - reachable_states
        if unreachable:
            raise ValueError(f"Unreachable states detected: {unreachable}")

        return self

    def _find_reachable_states(self, start_state: str) -> set[str]:
        """Find all states reachable from the start state."""
        visited = set()
        to_visit = {start_state}

        # Build transition map
        transition_map: dict[str, list[str]] = {}
        for transition in self.transitions:
            if transition.from_state not in transition_map:
                transition_map[transition.from_state] = []
            transition_map[transition.from_state].append(transition.to_state)

        # BFS to find reachable states
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue

            visited.add(current)

            # Add connected states
            if current in transition_map:
                for next_state in transition_map[current]:
                    if next_state not in visited:
                        to_visit.add(next_state)

        return visited

    def get_state(self, state_id: str) -> Optional[WorkflowState]:
        """Get a state by ID."""
        for state in self.states:
            if state.id == state_id:
                return state
        return None

    def get_transitions_from_state(self, state_id: str) -> list[WorkflowTransition]:
        """Get all transitions from a given state."""
        return [t for t in self.transitions if t.from_state == state_id]

    def get_available_actions(
        self, state_id: str, role: EducationRole
    ) -> set[WorkflowAction]:
        """Get available actions for a role in a specific state."""
        state = self.get_state(state_id)
        if not state:
            return set()

        actions = set()

        # Add default permissions
        if role in self.default_permissions:
            actions.update(self.default_permissions[role])

        # Add state-specific permissions
        for permission in state.permissions:
            if permission.role == role:
                actions.update(permission.actions)

        return actions

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "simple_review",
                    "name": "Simple Review Workflow",
                    "description": "A basic 3-state workflow for educational content review",
                    "version": "1.0.0",
                    "category": "educational",
                    "states": [
                        {
                            "id": "draft",
                            "title": "Draft",
                            "state_type": "draft",
                            "is_initial": True,
                            "permissions": [
                                {"role": "author", "actions": ["view", "edit"]}
                            ],
                        }
                    ],
                    "transitions": [
                        {
                            "id": "submit",
                            "title": "Submit for Review",
                            "from_state": "draft",
                            "to_state": "review",
                            "required_role": "author",
                        }
                    ],
                    "metadata": {"complexity": "simple"},
                }
            ]
        }
    }


class WorkflowError(Exception):
    """Base exception for workflow-related errors."""

    pass


class InvalidWorkflowError(WorkflowError):
    """Raised when a workflow definition is invalid."""

    pass


class WorkflowValidationError(WorkflowError):
    """Raised when workflow validation fails."""

    pass
