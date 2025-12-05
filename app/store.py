from typing import List, Dict, Any

# In-memory schedules store (shared between main app and scheduler)
SCHEDULES: List[Dict[str, Any]] = []

# Simple send logs to record what was "sent"
SEND_LOGS: List[Dict[str, Any]] = []
