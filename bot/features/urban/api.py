"""
Urban Dictionary API Client

This module provides a client for interacting with the Urban Dictionary API.
"""

import aiohttp
import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Union
import asyncio
import re

from bot.core.analytics import analytics
from bot.core.performance_monitor import performance_monitor, timed

class UrbanDictionaryAPIError(Exception):
    """Base exception for Urban Dictionary API errors"""
    pass

class UrbanDictionaryClient:
    """Client for interacting with the Urban Dictionary API"""
    
    def __init__(self):
        """Initialize the Urban Dictionary client"""
        self.base_url = "https://api.urbandictionary.com/v0"
        self.initialized = True
        logging.info("Urban Dictionary client initialized")
    
    @timed(operation_type="urban_api")
    async def define(self, term: str) -> List[Dict[str, Any]]:
        """
        Define a term using Urban Dictionary
        
        Args:
            term: Term to define
            
        Returns:
            List of definition dictionaries
        """
        # Track API usage
        analytics.track_api_call("urban_define", True, 0, 
                                metadata={"term": term})
        
        try:
            timer_id = performance_monitor.start_timer("urban_define_api")
            
            params = {
                "term": term
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/define", params=params) as response:
                    response_time = performance_monitor.stop_timer(timer_id, "api_call")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Track successful API call
                        analytics.track_api_call("urban_define", True, response_time, 
                                               metadata={"result_count": len(data.get("list", []))})
                        
                        return data.get("list", [])
                    else:
                        error_text = await response.text()
                        
                        # Track failed API call
                        analytics.track_api_call("urban_define", False, response_time, 
                                               metadata={"error": error_text, "status": response.status})
                        
                        raise UrbanDictionaryAPIError(f"Urban Dictionary API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            # Track network error
            analytics.track_api_call("urban_define", False, 0, 
                                   metadata={"error": str(e), "type": "network"})
            
            raise UrbanDictionaryAPIError(f"Network error: {str(e)}")
        except Exception as e:
            # Track unexpected error
            analytics.track_api_call("urban_define", False, 0, 
                                   metadata={"error": str(e), "type": "unexpected"})
            
            raise UrbanDictionaryAPIError(f"Unexpected error: {str(e)}")
    
    @timed(operation_type="urban_api")
    async def random(self) -> List[Dict[str, Any]]:
        """
        Get random definitions from Urban Dictionary
        
        Returns:
            List of definition dictionaries
        """
        # Track API usage
        analytics.track_api_call("urban_random", True, 0)
        
        try:
            timer_id = performance_monitor.start_timer("urban_random_api")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/random") as response:
                    response_time = performance_monitor.stop_timer(timer_id, "api_call")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Track successful API call
                        analytics.track_api_call("urban_random", True, response_time, 
                                               metadata={"result_count": len(data.get("list", []))})
                        
                        return data.get("list", [])
                    else:
                        error_text = await response.text()
                        
                        # Track failed API call
                        analytics.track_api_call("urban_random", False, response_time, 
                                               metadata={"error": error_text, "status": response.status})
                        
                        raise UrbanDictionaryAPIError(f"Urban Dictionary API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            # Track network error
            analytics.track_api_call("urban_random", False, 0, 
                                   metadata={"error": str(e), "type": "network"})
            
            raise UrbanDictionaryAPIError(f"Network error: {str(e)}")
        except Exception as e:
            # Track unexpected error
            analytics.track_api_call("urban_random", False, 0, 
                                   metadata={"error": str(e), "type": "unexpected"})
            
            raise UrbanDictionaryAPIError(f"Unexpected error: {str(e)}")
    
    def format_definition(self, definition: Dict[str, Any]) -> str:
        """
        Format a definition for display
        
        Args:
            definition: Definition dictionary
            
        Returns:
            Formatted definition string
        """
        # Extract fields
        word = definition.get("word", "Unknown")
        definition_text = definition.get("definition", "No definition available")
        example = definition.get("example", "")
        author = definition.get("author", "Unknown")
        thumbs_up = definition.get("thumbs_up", 0)
        thumbs_down = definition.get("thumbs_down", 0)
        
        # Clean up definition and example
        definition_text = self._clean_text(definition_text)
        example = self._clean_text(example)
        
        # Format the definition
        formatted = f"**{word}**\n\n"
        formatted += f"{definition_text}\n\n"
        
        if example:
            formatted += f"*Example:*\n{example}\n\n"
        
        formatted += f"👍 {thumbs_up} | 👎 {thumbs_down} | by {author}"
        
        return formatted
    
    def _clean_text(self, text: str) -> str:
        """
        Clean up text from Urban Dictionary
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Replace square brackets with bold formatting
        text = re.sub(r'\[(.*?)\]', r'**\1**', text)
        
        # Replace newlines with proper Discord newlines
        text = text.replace("\\r", "").replace("\\n", "\n")
        
        # Truncate if too long
        if len(text) > 1000:
            text = text[:997] + "..."
        
        return text
