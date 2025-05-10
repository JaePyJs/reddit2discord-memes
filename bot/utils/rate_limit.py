import time
from collections import defaultdict

# Simple in-memory rate limiter (per-user, per-command)
class RateLimiter:
    def __init__(self, cooldown_seconds=5):
        self.cooldown = cooldown_seconds
        self.last_used = defaultdict(lambda: 0)

    def can_run(self, user_id, command):
        key = (user_id, command)
        now = time.time()
        if now - self.last_used[key] >= self.cooldown:
            self.last_used[key] = now
            return True
        return False

# Usage statistics (in-memory, for demonstration)
class UsageStats:
    def __init__(self):
        self.command_counts = defaultdict(int)

    def record(self, command):
        self.command_counts[command] += 1

    def get_stats(self):
        return dict(self.command_counts)

# Example usage:
# limiter = RateLimiter(10)
# stats = UsageStats()
# if limiter.can_run(user_id, 'meme_create'):
#     stats.record('meme_create')
