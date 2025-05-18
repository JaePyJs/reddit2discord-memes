import datetime
import json
from collections import defaultdict

ANALYTICS_FILE = 'analytics.json'

class AnalyticsTracker:
    def __init__(self):
        self.usage = defaultdict(int)
        self.load()

    def log_command(self, command_name, user_id=None):
        key = f'{command_name}'
        self.usage[key] += 1
        self.save()

    def save(self):
        with open(ANALYTICS_FILE, 'w') as f:
            json.dump(self.usage, f)

    def load(self):
        try:
            with open(ANALYTICS_FILE, 'r') as f:
                self.usage = defaultdict(int, json.load(f))
        except Exception:
            self.usage = defaultdict(int)

    def get_report(self):
        lines = [f'{cmd}: {count}' for cmd, count in sorted(self.usage.items(), key=lambda x: -x[1])]
        return '\n'.join(lines) or 'No usage data.'

tracker = AnalyticsTracker()
