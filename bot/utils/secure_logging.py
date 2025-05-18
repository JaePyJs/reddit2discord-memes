"""
Secure Logging Utilities

This module provides utilities for secure logging that masks sensitive information.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union

# Patterns for sensitive information
SENSITIVE_PATTERNS = {
    'discord_token': r'(DISCORD_TOKEN=)[a-zA-Z0-9_\.\-]+',
    'openrouter_api_key': r'(OPENROUTER_API_KEY=|sk-or-v1-)[a-zA-Z0-9_\.\-]+',
    'spotify_client_id': r'(SPOTIFY_CLIENT_ID=)[a-zA-Z0-9_\.\-]+',
    'spotify_client_secret': r'(SPOTIFY_CLIENT_SECRET=)[a-zA-Z0-9_\.\-]+',
    'tenor_api_key': r'(TENOR_API_KEY=)[a-zA-Z0-9_\.\-]+',
    'openweathermap_api_key': r'(OPENWEATHERMAP_API_KEY=)[a-zA-Z0-9_\.\-]+',
    'generic_api_key': r'(api_key=|apikey=|key=)[\'"][a-zA-Z0-9_\.\-]+[\'"]',
    'generic_token': r'(token=|access_token=|auth_token=)[\'"][a-zA-Z0-9_\.\-]+[\'"]',
    'generic_password': r'(password=|passwd=|pwd=)[\'"][a-zA-Z0-9_\.\-]+[\'"]',
    'generic_secret': r'(secret=|client_secret=)[\'"][a-zA-Z0-9_\.\-]+[\'"]',
    'bearer_token': r'(Bearer\s+)[a-zA-Z0-9_\.\-]+'
}

def mask_sensitive_info(text: str) -> str:
    """
    Mask sensitive information in a string
    
    Args:
        text: String that might contain sensitive information
        
    Returns:
        String with sensitive information masked
    """
    if not text:
        return text
        
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
    
    # Apply each pattern
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        # Different replacement strategies based on pattern type
        if pattern_name in ['discord_token', 'openrouter_api_key', 'spotify_client_id', 
                           'spotify_client_secret', 'tenor_api_key', 'openweathermap_api_key']:
            # For environment variables, keep the variable name
            text = re.sub(pattern, r'\1[REDACTED]', text)
        elif pattern_name == 'bearer_token':
            # For Bearer tokens, keep the 'Bearer ' prefix
            text = re.sub(pattern, r'\1[REDACTED]', text)
        else:
            # For generic patterns, show first and last few characters
            matches = re.finditer(pattern, text)
            for match in matches:
                full_match = match.group(0)
                prefix = match.group(1)
                value = full_match[len(prefix):]
                
                # Remove quotes if present
                if value.startswith('"') or value.startswith("'"):
                    quote = value[0]
                    value = value[1:-1]
                    masked_value = f"{value[:3]}...{value[-3:]}" if len(value) > 8 else "[REDACTED]"
                    replacement = f'{prefix}{quote}{masked_value}{quote}'
                else:
                    masked_value = f"{value[:3]}...{value[-3:]}" if len(value) > 8 else "[REDACTED]"
                    replacement = f'{prefix}{masked_value}'
                
                text = text.replace(full_match, replacement)
    
    return text

class SecureLogger:
    """Logger that masks sensitive information"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize the secure logger
        
        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Add a handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log a debug message with sensitive information masked"""
        self.logger.debug(mask_sensitive_info(msg), *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log an info message with sensitive information masked"""
        self.logger.info(mask_sensitive_info(msg), *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log a warning message with sensitive information masked"""
        self.logger.warning(mask_sensitive_info(msg), *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log an error message with sensitive information masked"""
        self.logger.error(mask_sensitive_info(msg), *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log a critical message with sensitive information masked"""
        self.logger.critical(mask_sensitive_info(msg), *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log an exception message with sensitive information masked"""
        self.logger.exception(mask_sensitive_info(msg), *args, **kwargs)

# Create a function to get a secure logger
def get_secure_logger(name: str, level: int = logging.INFO) -> SecureLogger:
    """
    Get a secure logger that masks sensitive information
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        SecureLogger instance
    """
    return SecureLogger(name, level)
