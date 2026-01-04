"""SDK response models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Status:
    """System status."""

    mac_app_running: bool
    phone_connected: bool
    phone_name: str | None
    switch_control_enabled: bool
    screen_locked: bool
    streaming: bool


@dataclass
class Job:
    """Job status and result."""

    id: str
    status: JobStatus
    result: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None
