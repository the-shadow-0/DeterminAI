import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict

class DeterminAILogger:
    def __init__(self, name: str = "DeterminAI"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log(self, level: int, event: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": logging.getLevelName(level),
            "event": event,
            **kwargs
        }
        self.logger.log(level, json.dumps(log_entry))

    def info(self, event: str, **kwargs):
        self._log(logging.INFO, event, **kwargs)

    def error(self, event: str, **kwargs):
        self._log(logging.ERROR, event, **kwargs)

    def debug(self, event: str, **kwargs):
        self._log(logging.DEBUG, event, **kwargs)

    def warn(self, event: str, **kwargs):
        self._log(logging.WARNING, event, **kwargs)
        
    def metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Dedicated hook for structured metric telemetry."""
        tags = tags or {}
        self.info(f"Metric: {metric_name}", metric_value=value, metric_tags=tags)

# Global singleton
logger = DeterminAILogger()
