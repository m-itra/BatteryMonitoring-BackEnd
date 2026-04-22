from dataclasses import dataclass


@dataclass
class BatchIngestResult:
    device_id: str
    processed_samples: int = 0
    duplicate_samples: int = 0
    completed_sessions: int = 0
    completed_cycles: int = 0
