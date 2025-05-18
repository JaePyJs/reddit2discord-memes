"""
Tests for the analytics module.
"""

import unittest
import os
import sys
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the bot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from bot.core.analytics import AnalyticsTracker

class TestAnalytics(unittest.TestCase):
    """Test cases for the AnalyticsTracker class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary file for the analytics data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        
        # Create a patch for the ANALYTICS_FILE constant
        self.file_patcher = patch('bot.core.analytics.ANALYTICS_FILE', self.temp_file.name)
        self.file_mock = self.file_patcher.start()
        
        # Create the analytics tracker
        self.tracker = AnalyticsTracker()
    
    def tearDown(self):
        """Clean up after tests"""
        # Stop the patcher
        self.file_patcher.stop()
        
        # Remove the temporary file
        os.unlink(self.temp_file.name)
    
    def test_log_command(self):
        """Test logging a command"""
        # Log a command
        self.tracker.log_command('test_command', 'user123')
        
        # Check that the command was logged
        self.assertEqual(self.tracker.usage['test_command'], 1)
        
        # Log the same command again
        self.tracker.log_command('test_command', 'user123')
        
        # Check that the count was incremented
        self.assertEqual(self.tracker.usage['test_command'], 2)
    
    def test_track_command(self):
        """Test tracking a command"""
        # Track a command
        self.tracker.track_command('test_command', 'user123', 'guild123', 'channel123', {'param': 'value'})
        
        # Check that the command was logged
        self.assertEqual(self.tracker.usage['test_command'], 1)
    
    def test_track_feature(self):
        """Test tracking a feature"""
        # Track a feature
        self.tracker.track_feature('test_feature', 'user123', 'guild123', 'channel123', {'param': 'value'})
        
        # Check that the feature was logged
        self.assertEqual(self.tracker.usage['test_feature'], 1)
    
    def test_track_error(self):
        """Test tracking an error"""
        # Track an error
        self.tracker.track_error('test_error', {'param': 'value'})
        
        # Check that the error was logged
        self.assertEqual(self.tracker.usage['error_test_error'], 1)
    
    def test_track_api_call(self):
        """Test tracking an API call"""
        # Track a successful API call
        self.tracker.track_api_call('test_api', True, 0.5, {'param': 'value'})
        
        # Check that the API call was logged
        self.assertEqual(self.tracker.usage['test_api_success'], 1)
        
        # Track a failed API call
        self.tracker.track_api_call('test_api', False, 0.5, {'param': 'value'})
        
        # Check that the API call was logged
        self.assertEqual(self.tracker.usage['test_api_failure'], 1)
    
    def test_save_and_load(self):
        """Test saving and loading analytics data"""
        # Log some commands
        self.tracker.log_command('test_command1', 'user123')
        self.tracker.log_command('test_command2', 'user123')
        self.tracker.log_command('test_command1', 'user123')
        
        # Save the data
        self.tracker.save()
        
        # Create a new tracker (which will load the data)
        new_tracker = AnalyticsTracker()
        
        # Check that the data was loaded correctly
        self.assertEqual(new_tracker.usage['test_command1'], 2)
        self.assertEqual(new_tracker.usage['test_command2'], 1)
    
    def test_get_report(self):
        """Test getting a report of analytics data"""
        # Log some commands
        self.tracker.log_command('test_command1', 'user123')
        self.tracker.log_command('test_command2', 'user123')
        self.tracker.log_command('test_command1', 'user123')
        
        # Get the report
        report = self.tracker.get_report()
        
        # Check that the report contains the expected data
        self.assertIn('test_command1: 2', report)
        self.assertIn('test_command2: 1', report)

if __name__ == '__main__':
    unittest.main()
