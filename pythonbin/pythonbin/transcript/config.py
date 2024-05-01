from dataclasses import dataclass


@dataclass
class Config:
    idle_timeout: int = 600  # Idle timeout in seconds (10 minutes)
    polling_interval: int = 1  # Polling interval in seconds for fallback
    notification_interval: int = 60  # Notification interval in seconds
    activity_trigger_threshold: int = (
        5  # Threshold of new entries to trigger notification
    )
