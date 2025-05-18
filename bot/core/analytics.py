import datetime
import json
import logging
from collections import defaultdict
from typing import Dict, Optional, Any

ANALYTICS_FILE = 'analytics.json'

class AnalyticsTracker:
    def __init__(self):
        self.usage = defaultdict(int)
        self.load()

    def log_command(self, command_name, user_id=None):
        key = f'{command_name}'
        self.usage[key] += 1
        self.save()

    def track_command(self, command_name: str, user_id: str, guild_id: Optional[str] = None,
                     channel_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Simplified track_command for compatibility with new API modules"""
        self.log_command(command_name, user_id)

    def track_feature(self, feature_name: str, user_id: str, guild_id: Optional[str] = None,
                     channel_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Simplified track_feature for compatibility with new API modules"""
        self.log_command(feature_name, user_id)

    def track_error(self, error_type: str, metadata: Optional[Dict] = None):
        """Simplified track_error for compatibility with new API modules"""
        self.log_command(f"error_{error_type}")

    def track_api_call(self, api_name: str, success: bool, response_time: float,
                      metadata: Optional[Dict] = None):
        """Simplified track_api_call for compatibility with new API modules"""
        status = "success" if success else "failure"
        self.log_command(f"{api_name}_{status}")

    def save(self):
        try:
            with open(ANALYTICS_FILE, 'w') as f:
                json.dump(self.usage, f)
        except Exception as e:
            logging.error(f"Error saving analytics: {e}")

    def load(self):
        try:
            with open(ANALYTICS_FILE, 'r') as f:
                self.usage = defaultdict(int, json.load(f))
        except Exception:
            self.usage = defaultdict(int)

    def get_report(self):
        lines = [f'{cmd}: {count}' for cmd, count in sorted(self.usage.items(), key=lambda x: -x[1])]
        return '\n'.join(lines) or 'No usage data.'

# Create a singleton instance
analytics = AnalyticsTracker()
tracker = analytics  # For backward compatibility
