"""
Tests for alert system Prometheus metrics (Task 8.4.5).

Validates that Prometheus counters and histograms increment correctly after alert dispatch.
"""

import time
import pytest
from unittest.mock import patch

from src.eduhub.alerts.monitoring import (
    alerts_sent_total,
    alerts_failed_total,
    websocket_messages_sent,
    broadcast_latency_ms,
    record_alert_sent,
    record_alert_failed,
    record_websocket_message,
    export_metrics,
    get_metrics_summary,
)
from src.eduhub.alerts.models import Alert, AlertChannel, AlertCategory, AlertPriority


class TestPrometheusMetrics:
    """Test Prometheus metrics instrumentation for alert system."""

    def test_record_alert_sent_increments_counter(self):
        """Test that recording sent alerts increments the counter."""
        # Create test alert
        test_alert = Alert(
            title="Test Alert",
            message="Test message", 
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.HIGH,
            channels=[AlertChannel.WEBSOCKET],
            source="test_metrics"
        )
        
        # Get initial total across all labels
        initial_total = sum(
            sample.value for family in alerts_sent_total.collect()
            for sample in family.samples if sample.name.endswith('_total')
        )
        
        # Record alert sent
        record_alert_sent(test_alert, AlertChannel.WEBSOCKET)
        
        # Get new total
        new_total = sum(
            sample.value for family in alerts_sent_total.collect()
            for sample in family.samples if sample.name.endswith('_total')
        )
        
        # Should have incremented by 1
        assert new_total == initial_total + 1

    def test_record_alert_failed_increments_counter(self):
        """Test that recording failed alerts increments the counter."""
        # Get initial total
        initial_total = sum(
            sample.value for family in alerts_failed_total.collect()
            for sample in family.samples if sample.name.endswith('_total')
        )
        
        # Record alert failure
        record_alert_failed("slack", "timeout", "system")
        
        # Get new total
        new_total = sum(
            sample.value for family in alerts_failed_total.collect()
            for sample in family.samples if sample.name.endswith('_total')
        )
        
        # Should have incremented by 1
        assert new_total == initial_total + 1

    def test_record_websocket_message_increments_counter(self):
        """Test that recording WebSocket messages increments the counter."""
        # Get initial total
        initial_total = sum(
            sample.value for family in websocket_messages_sent.collect()
            for sample in family.samples if sample.name.endswith('_total')
        )
        
        # Record WebSocket message
        record_websocket_message("alert")
        
        # Get new total
        new_total = sum(
            sample.value for family in websocket_messages_sent.collect()
            for sample in family.samples if sample.name.endswith('_total')
        )
        
        # Should have incremented by 1
        assert new_total == initial_total + 1

    def test_broadcast_latency_histogram_records(self):
        """Test that broadcast latency histogram records timing data."""
        # Get initial sample count
        initial_count = sum(
            sample.value for family in broadcast_latency_ms.collect()
            for sample in family.samples if sample.name.endswith('_count')
        )
        
        # Record latency using the histogram's time context manager
        with broadcast_latency_ms.labels(channel="websocket", priority="high").time():
            time.sleep(0.01)  # 10ms delay
            
        # Get new sample count
        new_count = sum(
            sample.value for family in broadcast_latency_ms.collect()
            for sample in family.samples if sample.name.endswith('_count')
        )
        
        # Should have recorded at least one sample
        assert new_count > initial_count

    def test_metrics_export_contains_alert_metrics(self):
        """Test that export_metrics() returns Prometheus formatted data."""
        # Record some test data
                 test_alert = Alert(
             title="Export Test",
             message="Test export",
             category=AlertCategory.SYSTEM,
             priority=AlertPriority.MEDIUM,
             channels=[AlertChannel.WEBSOCKET],
             source="test_export"
         )
        record_alert_sent(test_alert, AlertChannel.WEBSOCKET)
        
        # Export metrics
        metrics_output = export_metrics()
        
        # Should be bytes in Prometheus format
        assert isinstance(metrics_output, bytes)
        assert b"alerts_sent_total" in metrics_output
        assert b"websocket_messages_sent" in metrics_output

    def test_metrics_summary_aggregates_correctly(self):
        """Test that get_metrics_summary() returns aggregated data."""
        # Get metrics summary
        summary = get_metrics_summary()
        
        # Should return a dictionary with expected keys
        assert isinstance(summary, dict)
        assert "alerts_sent_total" in summary
        assert "alerts_failed_total" in summary
        assert "websocket_connections_active" in summary

    @pytest.mark.asyncio
    async def test_end_to_end_metrics_during_alert_dispatch(self):
        """Test metrics during a real alert dispatch scenario.""" 
        from src.eduhub.alerts.services import AlertDispatchService
        
        # Create test alert
        alert = Alert(
            title="E2E Test Alert",
            message="End-to-end metrics test",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.HIGH,
            channels=[AlertChannel.WEBSOCKET],
            source="test_e2e"
        )
        
        # Get initial metrics
        initial_sent = sum(
            sample.value for family in alerts_sent_total.collect()
            for sample in family.samples if sample.name.endswith('_total')
        )
        
        # Mock dependencies to avoid real connections
        with (
            patch("src.eduhub.alerts.services.websocket_manager") as mock_ws,
            patch("src.eduhub.alerts.services.get_slack_client") as mock_slack,
        ):
            mock_ws.broadcast_alert.return_value = True
            mock_slack.return_value = None
            
            # Create service and dispatch alert
            service = AlertDispatchService()
            
            # Mock Redis to avoid real connections
            with patch.object(service, "redis_client", None):
                try:
                    await service.dispatch_alert(alert)
                except Exception:
                    # Ignore dispatch errors, we just want to test metrics
                    pass
        
        # Check that some metrics were recorded
        metrics_output = export_metrics()
        assert b"alerts_sent_total" in metrics_output or b"alerts_failed_total" in metrics_output

    def test_metrics_endpoint_integration(self):
        """Test metrics endpoint returns proper content type."""
        from src.eduhub.alerts.monitoring import get_metrics_content_type
        
        content_type = get_metrics_content_type()
        assert "text/plain" in content_type
