"""
Conflict detection for schedule imports.

Identifies scheduling conflicts such as double-bookings of rooms
or instructors, and overlapping time slots.
"""

from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Dict, List, Set, Tuple

from .models import ConflictError, ScheduleRow


class ConflictDetector:
    """Detects scheduling conflicts in schedule data."""

    def __init__(self):
        self.conflicts: list[ConflictError] = []

    def detect_conflicts(self, rows: list[ScheduleRow]) -> list[ConflictError]:
        """
        Detect all types of conflicts in the schedule data.

        Returns:
            List of ConflictError objects describing conflicts found
        """
        self.conflicts = []

        # Create indexed data for efficient conflict detection
        indexed_rows = [(i, row) for i, row in enumerate(rows)]

        # Detect different types of conflicts
        self._detect_room_conflicts(indexed_rows)
        self._detect_instructor_conflicts(indexed_rows)
        self._detect_duplicate_entries(indexed_rows)

        return self.conflicts

    def _detect_room_conflicts(
        self, indexed_rows: list[tuple[int, ScheduleRow]]
    ) -> None:
        """Detect room double-booking conflicts."""
        room_schedules = defaultdict(list)

        # Group by room
        for idx, row in indexed_rows:
            room_schedules[row.room.lower().strip()].append((idx, row))

        # Check for overlaps within each room
        for room, room_rows in room_schedules.items():
            if len(room_rows) > 1:
                self._check_time_overlaps(room_rows, "room", room)

    def _detect_instructor_conflicts(
        self, indexed_rows: list[tuple[int, ScheduleRow]]
    ) -> None:
        """Detect instructor double-booking conflicts."""
        instructor_schedules = defaultdict(list)

        # Group by instructor
        for idx, row in indexed_rows:
            instructor_schedules[row.instructor.lower().strip()].append((idx, row))

        # Check for overlaps within each instructor's schedule
        for instructor, instructor_rows in instructor_schedules.items():
            if len(instructor_rows) > 1:
                self._check_time_overlaps(instructor_rows, "instructor", instructor)

    def _detect_duplicate_entries(
        self, indexed_rows: list[tuple[int, ScheduleRow]]
    ) -> None:
        """Detect exact duplicate entries."""
        seen_entries = {}

        for idx, row in indexed_rows:
            # Create a signature for the entry
            signature = (
                row.program.lower().strip(),
                row.date,
                row.time,
                row.instructor.lower().strip(),
                row.room.lower().strip(),
            )

            if signature in seen_entries:
                original_idx = seen_entries[signature]
                self.conflicts.append(
                    ConflictError(
                        row_numbers=[
                            original_idx + 2,
                            idx + 2,
                        ],  # +2 for 1-based + header
                        conflict_type="duplicate",
                        message=f"Duplicate entry found: {row.program} on {row.date} at {row.time}",
                    )
                )
            else:
                seen_entries[signature] = idx

    def _check_time_overlaps(
        self,
        entries: list[tuple[int, ScheduleRow]],
        conflict_type: str,
        resource_name: str,
    ) -> None:
        """Check for time overlaps in a list of entries."""
        # Sort entries by date and time
        entries.sort(key=lambda x: (x[1].date, x[1].time))

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                idx1, row1 = entries[i]
                idx2, row2 = entries[j]

                # Only check same date
                if row1.date != row2.date:
                    continue

                if self._times_overlap(row1, row2):
                    self.conflicts.append(
                        ConflictError(
                            row_numbers=[idx1 + 2, idx2 + 2],  # +2 for 1-based + header
                            conflict_type=conflict_type,
                            message=(
                                f"{conflict_type.title()} '{resource_name}' is double-booked: "
                                f"{row1.program} ({row1.time}) conflicts with "
                                f"{row2.program} ({row2.time}) on {row1.date}"
                            ),
                        )
                    )

    def _times_overlap(self, row1: ScheduleRow, row2: ScheduleRow) -> bool:
        """Check if two schedule entries have overlapping times."""
        try:
            # Parse times
            time1 = datetime.strptime(row1.time, "%H:%M").time()
            time2 = datetime.strptime(row2.time, "%H:%M").time()

            # Calculate end times
            duration1 = timedelta(minutes=row1.duration or 60)
            duration2 = timedelta(minutes=row2.duration or 60)

            # Convert to datetime objects for easier calculation
            base_date = datetime.strptime(row1.date, "%Y-%m-%d").date()
            start1 = datetime.combine(base_date, time1)
            end1 = start1 + duration1
            start2 = datetime.combine(base_date, time2)
            end2 = start2 + duration2

            # Check for overlap
            return start1 < end2 and start2 < end1

        except ValueError:
            # If we can't parse times, assume no overlap
            return False
