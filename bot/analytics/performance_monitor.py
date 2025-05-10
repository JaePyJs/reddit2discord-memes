import time
import logging
from functools import wraps

PERF_LOG = 'performance.log'

# Decorator to measure and log command execution time
def monitor_performance(command_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.time() - start
                msg = f'{command_name} executed in {elapsed:.3f}s'
                logging.info(msg)
                with open(PERF_LOG, 'a') as f:
                    f.write(msg + '\n')
        return wrapper
    return decorator
