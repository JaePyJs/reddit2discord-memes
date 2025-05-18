"""
Tests for the performance monitor module.
"""

import unittest
import os
import sys
import time
import tempfile
import asyncio
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bot.core.performance_monitor import PerformanceMonitor, timed, monitor_performance

class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for the PerformanceMonitor class"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary file for the performance log
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()

        # Create a patch for the PERF_LOG constant
        self.file_patcher = patch('bot.core.performance_monitor.PERF_LOG', self.temp_file.name)
        self.file_mock = self.file_patcher.start()

        # Create a patch for the logging module
        self.logging_patcher = patch('bot.core.performance_monitor.logging')
        self.logging_mock = self.logging_patcher.start()

        # Create the performance monitor
        self.monitor = PerformanceMonitor()

    def tearDown(self):
        """Clean up after tests"""
        # Stop the patchers
        self.file_patcher.stop()
        self.logging_patcher.stop()

        # Remove the temporary file
        os.unlink(self.temp_file.name)

    def test_start_and_stop_timer(self):
        """Test starting and stopping a timer"""
        # Start a timer
        timer_id = self.monitor.start_timer('test_operation')

        # Check that the timer was started
        self.assertIn(timer_id, self.monitor.active_timers)
        self.assertEqual(self.monitor.active_timers[timer_id]['operation_name'], 'test_operation')

        # Sleep for a short time
        time.sleep(0.1)

        # Stop the timer
        execution_time = self.monitor.stop_timer(timer_id)

        # Check that the timer was stopped
        self.assertNotIn(timer_id, self.monitor.active_timers)

        # Check that the execution time is reasonable
        self.assertGreaterEqual(execution_time, 0.1)
        self.assertLess(execution_time, 0.2)

        # Check that the execution time was logged
        self.logging_mock.info.assert_called_with(f'generic:test_operation executed in {execution_time:.3f}s')

    def test_stop_nonexistent_timer(self):
        """Test stopping a nonexistent timer"""
        # Stop a nonexistent timer
        execution_time = self.monitor.stop_timer('nonexistent_timer')

        # Check that the execution time is 0
        self.assertEqual(execution_time, 0.0)

        # Check that a warning was logged
        self.logging_mock.warning.assert_called_with('Timer nonexistent_timer not found')

    def test_timed_decorator_sync(self):
        """Test the timed decorator with a synchronous function"""
        # Create a mock performance monitor
        mock_monitor = MagicMock()
        mock_monitor.start_timer.return_value = 'test_timer'
        mock_monitor.stop_timer.return_value = 0.1

        # Create a patch for the performance_monitor instance
        with patch('bot.core.performance_monitor.performance_monitor', mock_monitor):
            # Define a test function
            @timed('test_operation')
            def test_function():
                return 'test_result'

            # Call the function
            result = test_function()

            # Check that the result is correct
            self.assertEqual(result, 'test_result')

            # Check that the timer was started and stopped
            mock_monitor.start_timer.assert_called_once_with('test_function')
            mock_monitor.stop_timer.assert_called_once_with('test_timer', 'test_operation')

    def test_timed_decorator_async(self):
        """Test the timed decorator with an asynchronous function"""
        # Create a mock performance monitor
        mock_monitor = MagicMock()
        mock_monitor.start_timer.return_value = 'test_timer'
        mock_monitor.stop_timer.return_value = 0.1

        # Create a patch for the performance_monitor instance
        with patch('bot.core.performance_monitor.performance_monitor', mock_monitor):
            # Define a test function
            @timed('test_operation')
            async def test_function():
                return 'test_result'

            # Call the function
            result = asyncio.run(test_function())

            # Check that the result is correct
            self.assertEqual(result, 'test_result')

            # Check that the timer was started and stopped
            mock_monitor.start_timer.assert_called_once_with('test_function')
            mock_monitor.stop_timer.assert_called_once_with('test_timer', 'test_operation')

    def test_monitor_performance_decorator(self):
        """Test the monitor_performance decorator"""
        # Create a patch for the logging module
        with patch('bot.core.performance_monitor.logging') as logging_mock:
            # Define a test function
            @monitor_performance('test_command')
            async def test_function():
                return 'test_result'

            # Call the function
            result = asyncio.run(test_function())

            # Check that the result is correct
            self.assertEqual(result, 'test_result')

            # Check that the execution time was logged
            # We can't check the exact message, but we can check that info was called
            self.assertTrue(logging_mock.info.called)

if __name__ == '__main__':
    unittest.main()
