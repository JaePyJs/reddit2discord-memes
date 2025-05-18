import time
import logging
import functools
import asyncio
from functools import wraps
from typing import Dict, Optional, Any, Callable, Union

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

class PerformanceMonitor:
    """Simple performance monitoring system"""

    def __init__(self):
        """Initialize the performance monitoring system"""
        self.active_timers = {}

    def start_timer(self, operation_name: str) -> str:
        """
        Start a timer for an operation

        Args:
            operation_name: Name of the operation

        Returns:
            Timer ID
        """
        timer_id = f"{operation_name}_{time.time()}"
        self.active_timers[timer_id] = {
            "start_time": time.time(),
            "operation_name": operation_name
        }
        return timer_id

    def stop_timer(self, timer_id: str, operation_type: str = "generic") -> float:
        """
        Stop a timer and record the execution time

        Args:
            timer_id: Timer ID returned by start_timer
            operation_type: Type of operation (e.g., "command", "api_call")

        Returns:
            Execution time in seconds
        """
        if timer_id not in self.active_timers:
            logging.warning(f"Timer {timer_id} not found")
            return 0.0

        timer_data = self.active_timers.pop(timer_id)
        execution_time = time.time() - timer_data["start_time"]

        # Log the execution time
        operation_name = timer_data["operation_name"]
        msg = f'{operation_type}:{operation_name} executed in {execution_time:.3f}s'
        logging.info(msg)
        with open(PERF_LOG, 'a') as f:
            f.write(msg + '\n')

        return execution_time

def timed(operation_type: str = "function"):
    """
    Decorator to time function execution

    Args:
        operation_type: Type of operation

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timer_id = performance_monitor.start_timer(func.__name__)
            try:
                result = func(*args, **kwargs)
                performance_monitor.stop_timer(timer_id, operation_type)
                return result
            except Exception as e:
                performance_monitor.stop_timer(timer_id, operation_type)
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            timer_id = performance_monitor.start_timer(func.__name__)
            try:
                result = await func(*args, **kwargs)
                performance_monitor.stop_timer(timer_id, operation_type)
                return result
            except Exception as e:
                performance_monitor.stop_timer(timer_id, operation_type)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator

# Create a singleton instance
performance_monitor = PerformanceMonitor()
