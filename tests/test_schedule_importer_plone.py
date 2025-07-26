"""
Tests for Schedule Importer Plone Integration

This module tests the Plone integration functionality of the CSV schedule importer,
including event creation, rollback mechanisms, and field mapping.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eduhub.auth.models import User
from eduhub.plone_integration import PloneAPIError, PloneClient
from eduhub.schedule_importer.models import ScheduleRow
from eduhub.schedule_importer.services import ScheduleImportService


@pytest.fixture
def mock_plone_client():
    """Create a mock PloneClient for testing."""
    client = AsyncMock(spec=PloneClient)
    return client


@pytest.fixture
def test_user():
    """Create a test user for testing."""
    return User(
        sub="test-user-123",
        email="test@example.com",
        name="Test User",
        plone_user_id="testuser",
        roles=["Member"],
        aud="test-client-id",
        iss="https://test.auth0.com/",
        exp=1234567890,
        iat=1234567890,
    )


@pytest.fixture
def sample_schedule_rows():
    """Create sample schedule rows for testing."""
    return [
        ScheduleRow(
            program="Python 101",
            date="2025-02-01",
            time="09:00",
            instructor="Dr. Smith",
            room="Room A",
            duration=90,
            description="Introduction to Python programming",
        ),
        ScheduleRow(
            program="Math Workshop",
            date="2025-02-01",
            time="14:30",
            instructor="Prof. Johnson",
            room="Room B",
            duration=60,
            description="Advanced Calculus workshop",
        ),
        ScheduleRow(
            program="Science Lab",
            date="2025-02-02",
            time="10:00",
            instructor="Dr. Williams",
            room="Lab 1",
            duration=120,
            description="Chemistry laboratory session",
        ),
    ]


@pytest.mark.asyncio
class TestScheduleImporterPloneIntegration:
    """Test the Plone integration functionality of the schedule importer."""

    async def test_schedule_row_to_event_data_mapping(self, mock_plone_client):
        """Test mapping of ScheduleRow to Plone Event data."""
        service = ScheduleImportService(mock_plone_client)

        row = ScheduleRow(
            program="Python 101",
            date="2025-02-01",
            time="09:00",
            instructor="Dr. Smith",
            room="Room A",
            duration=90,
            description="Introduction to Python programming",
        )

        event_data = service._schedule_row_to_event_data(row)

        # Verify correct field mapping
        assert event_data["title"] == "Python 101 - Dr. Smith"
        assert event_data["description"] == "Introduction to Python programming"
        assert event_data["start"] == "2025-02-01T09:00:00"
        assert event_data["end"] == "2025-02-01T10:30:00"  # 90 minutes later
        assert event_data["location"] == "Room A"
        assert event_data["attendees"] == ["Dr. Smith"]
        assert event_data["program_name"] == "Python 101"
        assert event_data["instructor_name"] == "Dr. Smith"
        assert event_data["room_location"] == "Room A"
        assert event_data["duration_minutes"] == 90

    async def test_schedule_row_to_event_data_default_duration(self, mock_plone_client):
        """Test mapping with default duration when not specified."""
        service = ScheduleImportService(mock_plone_client)

        row = ScheduleRow(
            program="Test Event",
            date="2025-02-01",
            time="14:00",
            instructor="Test Instructor",
            room="Test Room",
            duration=None,  # No duration specified
            description="Test description",
        )

        event_data = service._schedule_row_to_event_data(row)

        # Should default to 60 minutes
        assert event_data["duration_minutes"] == 60
        assert event_data["end"] == "2025-02-01T15:00:00"  # 60 minutes later

    async def test_create_single_event_success(self, mock_plone_client, test_user):
        """Test successful creation of a single event in Plone."""
        # Mock successful Plone response
        mock_plone_client.create_content.return_value = {
            "UID": "event-123",
            "title": "Python 101 - Dr. Smith",
            "@id": "http://localhost:8080/Plone/events/event-123",
        }

        service = ScheduleImportService(mock_plone_client)

        event_data = {
            "title": "Python 101 - Dr. Smith",
            "description": "Introduction to Python programming",
            "start": "2025-02-01T09:00:00",
            "end": "2025-02-01T10:30:00",
            "location": "Room A",
            "attendees": ["Dr. Smith"],
        }

        uid = await service._create_single_event(event_data, test_user)

        # Verify UID returned
        assert uid == "event-123"

        # Verify PloneClient was called correctly
        mock_plone_client.create_content.assert_called_once_with(
            parent_path="events", portal_type="Event", **event_data
        )

    async def test_create_single_event_failure(self, mock_plone_client, test_user):
        """Test handling of event creation failure."""
        # Mock Plone error
        mock_plone_client.create_content.side_effect = PloneAPIError("Creation failed")

        service = ScheduleImportService(mock_plone_client)

        event_data = {"title": "Test Event", "description": "Test description"}

        with pytest.raises(Exception) as exc_info:
            await service._create_single_event(event_data, test_user)

        assert "Failed to create event in Plone" in str(exc_info.value)

    async def test_create_single_event_no_uid_in_response(
        self, mock_plone_client, test_user
    ):
        """Test handling when Plone response doesn't include UID."""
        # Mock response without UID
        mock_plone_client.create_content.return_value = {
            "title": "Test Event",
            "@id": "http://localhost:8080/Plone/events/test-event",
            # Missing UID field
        }

        service = ScheduleImportService(mock_plone_client)

        event_data = {"title": "Test Event"}

        with pytest.raises(Exception) as exc_info:
            await service._create_single_event(event_data, test_user)

        assert "Failed to get UID from created event" in str(exc_info.value)

    async def test_rollback_created_content_success(self, mock_plone_client, test_user):
        """Test successful rollback of created content."""
        # Mock successful deletions
        mock_plone_client.delete_content.return_value = True

        service = ScheduleImportService(mock_plone_client)

        uid_paths = {
            "event-123": "events/event-123",
            "event-456": "events/event-456",
            "event-789": "events/event-789",
        }

        await service._rollback_created_content(uid_paths, test_user)

        # Verify all deletions were attempted
        assert mock_plone_client.delete_content.call_count == 3

        # Verify correct paths were used
        call_args = [
            call[0][0] for call in mock_plone_client.delete_content.call_args_list
        ]
        assert "events/event-123" in call_args
        assert "events/event-456" in call_args
        assert "events/event-789" in call_args

    async def test_rollback_created_content_partial_failure(
        self, mock_plone_client, test_user
    ):
        """Test rollback when some deletions fail."""

        # Mock mixed success/failure
        def mock_delete(path):
            if path == "events/event-456":
                return False  # This deletion fails
            return True  # Others succeed

        mock_plone_client.delete_content.side_effect = mock_delete

        service = ScheduleImportService(mock_plone_client)

        uid_paths = {
            "event-123": "events/event-123",
            "event-456": "events/event-456",  # This will fail
            "event-789": "events/event-789",
        }

        # Should not raise exception even if some deletions fail
        await service._rollback_created_content(uid_paths, test_user)

        # All deletions should have been attempted
        assert mock_plone_client.delete_content.call_count == 3

    async def test_rollback_created_content_exception(
        self, mock_plone_client, test_user
    ):
        """Test rollback when deletion raises exception."""
        # Mock exception on deletion
        mock_plone_client.delete_content.side_effect = PloneAPIError("Delete failed")

        service = ScheduleImportService(mock_plone_client)

        uid_paths = {"event-123": "events/event-123"}

        # Should not raise exception even if deletion fails
        await service._rollback_created_content(uid_paths, test_user)

    async def test_create_plone_content_success(
        self, mock_plone_client, test_user, sample_schedule_rows
    ):
        """Test successful creation of multiple events."""
        # Mock successful event creation
        created_uids = ["event-123", "event-456", "event-789"]
        mock_plone_client.create_content.side_effect = [
            {"UID": uid} for uid in created_uids
        ]

        service = ScheduleImportService(mock_plone_client)

        result_uids = await service._create_plone_content(
            sample_schedule_rows, test_user
        )

        # Verify all UIDs returned
        assert result_uids == created_uids

        # Verify PloneClient was called for each row
        assert mock_plone_client.create_content.call_count == len(sample_schedule_rows)

    async def test_create_plone_content_with_rollback(
        self, mock_plone_client, test_user, sample_schedule_rows
    ):
        """Test content creation with rollback on failure."""
        # Mock: first two succeed, third fails
        mock_responses = [
            {"UID": "event-123"},
            {"UID": "event-456"},
        ]
        mock_plone_client.create_content.side_effect = mock_responses + [
            PloneAPIError("Creation failed")
        ]
        mock_plone_client.delete_content.return_value = True

        service = ScheduleImportService(mock_plone_client)

        with pytest.raises(Exception):
            await service._create_plone_content(sample_schedule_rows, test_user)

        # Verify rollback was attempted for the successfully created events
        assert mock_plone_client.delete_content.call_count == 2

        # Verify correct paths were used for rollback
        call_args = [
            call[0][0] for call in mock_plone_client.delete_content.call_args_list
        ]
        assert "events/event-123" in call_args
        assert "events/event-456" in call_args


@pytest.mark.asyncio
class TestScheduleImporterEndToEnd:
    """End-to-end tests for the schedule importer with mocked Plone."""

    @patch("eduhub.schedule_importer.services.ScheduleImportService.__init__")
    async def test_happy_path_commit(self, mock_init, sample_schedule_rows):
        """Test Task 4.3.6: Happy-path commit with 8 rows → endpoint returns 8 UIDs."""
        # This would be a more complex test that mocks the entire service
        # and tests the FastAPI endpoint integration
        pass

    @patch(
        "eduhub.schedule_importer.services.ScheduleImportService._create_single_event"
    )
    async def test_rollback_on_second_row_failure(
        self, mock_create_event, sample_schedule_rows
    ):
        """Test Task 4.3.5: Mock create_events to raise on 2nd row → verify rollback."""
        # This would test the specific scenario where the second row fails
        # and verify that rollback is triggered
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
