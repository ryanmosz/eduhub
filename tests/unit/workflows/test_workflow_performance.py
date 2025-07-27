"""
Performance benchmarks for workflow template operations.

Tests permission application performance, bulk operations,
and scalability metrics to ensure the system meets performance targets.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.eduhub.workflows.models import EducationRole, WorkflowTemplate
from src.eduhub.workflows.permissions import map_eduhub_to_plone_roles, role_mapper
from src.eduhub.workflows.services import WorkflowServicesManager
from src.eduhub.workflows.templates import get_template


class TestWorkflowPerformance:
    """Performance benchmarks for workflow operations."""

    @pytest.fixture
    def mock_plone_client(self):
        """Create fast mock PloneClient for performance testing."""
        client = AsyncMock()

        # Mock responses with minimal data
        client.get_content_by_uid.return_value = {"uid": "test", "title": "Test"}
        client.get_workflow_info.return_value = {
            "state": "draft",
            "workflow_id": "test_workflow",
            "transitions": [],
            "history": [],
        }
        client.create_workflow = AsyncMock()
        client.assign_workflow_to_content = AsyncMock()
        client.assign_local_roles = AsyncMock()
        client.update_content_metadata = AsyncMock()
        client.set_workflow_state = AsyncMock()

        return client

    @pytest.fixture
    def workflow_service(self, mock_plone_client):
        """Create WorkflowServicesManager with mocked client."""
        return WorkflowServicesManager(mock_plone_client)

    @pytest.fixture
    def simple_template(self):
        """Get simple template for testing."""
        return get_template("simple_review")

    @pytest.fixture
    def role_assignments(self):
        """Standard role assignments for testing."""
        return {
            EducationRole.AUTHOR: ["user1", "user2", "user3"],
            EducationRole.EDITOR: ["editor1", "editor2"],
            EducationRole.ADMINISTRATOR: ["admin1"],
        }

    def generate_content_items(self, count: int) -> list[str]:
        """Generate test content item UIDs."""
        return [f"content-{i:06d}" for i in range(count)]

    def generate_bulk_assignments(
        self,
        content_items: list[str],
        base_role_assignments: dict[EducationRole, list[str]],
    ) -> list[dict[str, Any]]:
        """Generate bulk assignment data for content items."""
        return [
            {
                "content_uid": uid,
                "role_assignments": base_role_assignments.copy(),
                "force": False,
            }
            for uid in content_items
        ]


class TestPermissionMappingPerformance:
    """Test performance of role and permission mapping operations."""

    def test_role_mapping_performance(self, benchmark):
        """Benchmark role mapping operations."""
        role_assignments = {
            EducationRole.AUTHOR: [f"user{i}" for i in range(100)],
            EducationRole.EDITOR: [f"editor{i}" for i in range(50)],
            EducationRole.ADMINISTRATOR: [f"admin{i}" for i in range(10)],
        }

        def map_roles():
            return map_eduhub_to_plone_roles(role_assignments)

        result = benchmark.pedantic(map_roles, rounds=100)

        # Verify result structure
        assert len(result) == 3
        assert "Author" in result
        assert len(result["Author"]) == 100

    def test_permission_matrix_performance(self, benchmark, simple_template):
        """Benchmark permission matrix building."""

        def build_matrix():
            return role_mapper.build_permission_matrix(simple_template)

        result = benchmark.pedantic(build_matrix, rounds=50)

        # Verify result structure
        assert len(result) == len(simple_template.states)
        assert "draft" in result

    def test_template_validation_performance(self, benchmark, simple_template):
        """Benchmark template validation."""

        def validate_template():
            return role_mapper.validate_template_roles(simple_template)

        result = benchmark.pedantic(validate_template, rounds=100)

        # Verify validation passed
        assert result.is_valid

    def test_role_hierarchy_performance(self, benchmark):
        """Benchmark role hierarchy calculations."""

        def get_hierarchy():
            return role_mapper.get_role_hierarchy()

        result = benchmark.pedantic(get_hierarchy, rounds=200)

        # Verify hierarchy structure
        assert "Manager" in result
        assert result["Manager"] > result["Author"]


class TestSingleTemplateApplicationPerformance:
    """Test performance of single template application operations."""

    @pytest.mark.asyncio
    async def test_single_application_performance(
        self, benchmark, workflow_service, simple_template, role_assignments
    ):
        """Benchmark single template application."""
        content_uid = "test-content-001"
        user_id = "test-user"

        async def apply_template():
            return await workflow_service.validate_and_apply_template(
                content_uid,
                simple_template,
                role_assignments,
                user_id,
                force=True,
                validate_roles=False,
            )

        # Run benchmark with async function
        result = await benchmark.pedantic(apply_template, rounds=5)

        # Verify application succeeded
        assert result["success"] is True
        assert result["template_id"] == simple_template.id

    @pytest.mark.asyncio
    async def test_validation_only_performance(
        self, benchmark, workflow_service, simple_template
    ):
        """Benchmark template validation without application."""
        content_uids = [f"content-{i}" for i in range(10)]
        user_id = "test-user"

        async def validate_template():
            return await workflow_service.validate_template_for_content(
                simple_template, content_uids, user_id
            )

        result = await benchmark.pedantic(validate_template, rounds=10)

        # Verify validation structure
        assert result["template_id"] == simple_template.id
        assert len(result["content_validations"]) == 10


class TestBulkOperationPerformance:
    """Test performance of bulk workflow operations."""

    @pytest.mark.asyncio
    async def test_bulk_application_100_items(
        self, benchmark, workflow_service, simple_template, role_assignments
    ):
        """Benchmark bulk application for 100 items."""
        content_items = self.generate_content_items(100)
        bulk_assignments = self.generate_bulk_assignments(
            content_items, role_assignments
        )
        user_id = "test-user"

        async def bulk_apply():
            return await workflow_service.bulk_apply_template(
                simple_template, bulk_assignments, user_id, max_concurrent=10
            )

        result = await benchmark.pedantic(bulk_apply, rounds=3, warmup_rounds=1)

        # Verify bulk operation results
        assert result["total_items"] == 100
        assert result["successful_count"] + result["failed_count"] == 100
        assert result["template_id"] == simple_template.id

    @pytest.mark.asyncio
    async def test_bulk_application_1000_items(
        self, benchmark, workflow_service, simple_template, role_assignments
    ):
        """Benchmark bulk application for 1000 items (target requirement)."""
        content_items = self.generate_content_items(1000)
        bulk_assignments = self.generate_bulk_assignments(
            content_items, role_assignments
        )
        user_id = "test-user"

        async def bulk_apply():
            return await workflow_service.bulk_apply_template(
                simple_template, bulk_assignments, user_id, max_concurrent=20
            )

        result = await benchmark.pedantic(bulk_apply, rounds=1, warmup_rounds=0)

        # Verify bulk operation results
        assert result["total_items"] == 1000
        assert result["successful_count"] + result["failed_count"] == 1000
        assert result["template_id"] == simple_template.id

        # Performance target: ≤ 500ms average apply time per item
        # With 1000 items and concurrent processing, should complete reasonably fast
        print(
            f"Bulk application completed in {benchmark.stats.mean:.3f}s for 1000 items"
        )
        print(f"Average per item: {(benchmark.stats.mean / 1000) * 1000:.3f}ms")

    def generate_content_items(self, count: int) -> list[str]:
        """Generate test content item UIDs."""
        return [f"content-{i:06d}" for i in range(count)]

    def generate_bulk_assignments(
        self,
        content_items: list[str],
        base_role_assignments: dict[EducationRole, list[str]],
    ) -> list[dict[str, Any]]:
        """Generate bulk assignment data for content items."""
        return [
            {
                "content_uid": uid,
                "role_assignments": base_role_assignments.copy(),
                "force": False,
            }
            for uid in content_items
        ]


class TestConcurrencyPerformance:
    """Test performance under different concurrency levels."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("concurrent_level", [1, 5, 10, 20, 50])
    async def test_concurrency_scaling(
        self,
        benchmark,
        workflow_service,
        simple_template,
        role_assignments,
        concurrent_level,
    ):
        """Test how performance scales with concurrency level."""
        content_items = self.generate_content_items(100)
        bulk_assignments = self.generate_bulk_assignments(
            content_items, role_assignments
        )
        user_id = "test-user"

        async def bulk_apply():
            return await workflow_service.bulk_apply_template(
                simple_template,
                bulk_assignments,
                user_id,
                max_concurrent=concurrent_level,
            )

        result = await benchmark.pedantic(bulk_apply, rounds=2, warmup_rounds=1)

        # Store results for analysis
        result["concurrency_level"] = concurrent_level
        result["items_per_second"] = 100 / benchmark.stats.mean

        print(
            f"Concurrency {concurrent_level}: {result['items_per_second']:.2f} items/sec"
        )

        assert result["total_items"] == 100

    def generate_content_items(self, count: int) -> list[str]:
        """Generate test content item UIDs."""
        return [f"content-{i:06d}" for i in range(count)]

    def generate_bulk_assignments(
        self,
        content_items: list[str],
        base_role_assignments: dict[EducationRole, list[str]],
    ) -> list[dict[str, Any]]:
        """Generate bulk assignment data for content items."""
        return [
            {
                "content_uid": uid,
                "role_assignments": base_role_assignments.copy(),
                "force": False,
            }
            for uid in content_items
        ]


class TestMemoryPerformance:
    """Test memory usage patterns for large operations."""

    @pytest.mark.asyncio
    async def test_memory_usage_large_dataset(
        self, workflow_service, simple_template, role_assignments
    ):
        """Test memory usage with large datasets."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Generate large dataset
        content_items = [f"content-{i:06d}" for i in range(5000)]
        bulk_assignments = [
            {
                "content_uid": uid,
                "role_assignments": role_assignments.copy(),
                "force": False,
            }
            for uid in content_items
        ]

        peak_memory = process.memory_info().rss

        # Process the dataset
        result = await workflow_service.bulk_apply_template(
            simple_template, bulk_assignments, "test-user", max_concurrent=25
        )

        final_memory = process.memory_info().rss

        # Calculate memory usage
        peak_usage = (peak_memory - initial_memory) / 1024 / 1024  # MB
        final_usage = (final_memory - initial_memory) / 1024 / 1024  # MB

        print(f"Memory usage - Peak: {peak_usage:.2f}MB, Final: {final_usage:.2f}MB")

        # Verify operation completed
        assert result["total_items"] == 5000

        # Memory should not grow excessively (target: < 100MB for 5000 items)
        assert peak_usage < 100, f"Memory usage too high: {peak_usage:.2f}MB"


class TestErrorHandlingPerformance:
    """Test performance when handling various error conditions."""

    @pytest.mark.asyncio
    async def test_validation_error_performance(self, benchmark, workflow_service):
        """Benchmark performance when validation errors occur."""
        # Create invalid template by modifying a valid one
        template = get_template("simple_review")

        # Create invalid role assignments
        invalid_assignments = {
            EducationRole.AUTHOR: [],  # Empty user list should cause validation error
        }

        async def apply_with_error():
            try:
                await workflow_service.validate_and_apply_template(
                    "test-content", template, invalid_assignments, "test-user"
                )
                return {"success": False, "error": "Should have failed"}
            except Exception as e:
                return {"success": True, "error": str(e)}

        result = await benchmark.pedantic(apply_with_error, rounds=10)

        # Verify error was handled efficiently
        assert result["success"] is True
        assert "validation" in result["error"].lower()


# Integration test for overall system performance
class TestSystemIntegrationPerformance:
    """Test overall system performance with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_workflow_scenario(
        self, benchmark, workflow_service, role_assignments
    ):
        """Test a realistic workflow scenario with multiple operations."""
        simple_template = get_template("simple_review")
        extended_template = get_template("extended_review")

        async def realistic_scenario():
            # Validate both templates
            simple_validation = await workflow_service.validate_template_for_content(
                simple_template, ["content-1", "content-2"], "user-1"
            )

            extended_validation = await workflow_service.validate_template_for_content(
                extended_template, ["content-3", "content-4"], "user-1"
            )

            # Apply simple template to 2 items
            simple_assignments = [
                {"content_uid": "content-1", "role_assignments": role_assignments},
                {"content_uid": "content-2", "role_assignments": role_assignments},
            ]
            simple_result = await workflow_service.bulk_apply_template(
                simple_template, simple_assignments, "user-1", max_concurrent=2
            )

            # Apply extended template to 2 items
            extended_assignments = [
                {"content_uid": "content-3", "role_assignments": role_assignments},
                {"content_uid": "content-4", "role_assignments": role_assignments},
            ]
            extended_result = await workflow_service.bulk_apply_template(
                extended_template, extended_assignments, "user-1", max_concurrent=2
            )

            return {
                "simple_validation": simple_validation["overall_valid"],
                "extended_validation": extended_validation["overall_valid"],
                "simple_applications": simple_result["successful_count"],
                "extended_applications": extended_result["successful_count"],
            }

        result = await benchmark.pedantic(realistic_scenario, rounds=3)

        # Verify all operations succeeded
        assert result["simple_validation"] is True
        assert result["extended_validation"] is True
        assert result["simple_applications"] == 2
        assert result["extended_applications"] == 2
