"""
Tenor GIF API Client

This module provides a client for interacting with the Tenor GIF API.
"""

import aiohttp
import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Union
import asyncio
import random

from bot.core.config import TENOR_API_KEY
from bot.core.analytics import analytics
from bot.core.performance_monitor import performance_monitor, timed

class TenorAPIError(Exception):
    """Base exception for Tenor API errors"""
    pass

class TenorClient:
    """Client for interacting with the Tenor GIF API"""
    
    def __init__(self):
        """Initialize the Tenor client"""
        self.api_key = TENOR_API_KEY
        self.base_url = "https://tenor.googleapis.com/v2"
        self.initialized = bool(self.api_key)
        
        if not self.initialized:
            logging.error("Tenor API key not found. Set TENOR_API_KEY in .env file.")
        else:
            logging.info("Tenor client initialized")
    
    @timed(operation_type="tenor_api")
    async def search_gifs(self, query: str, limit: int = 10, 
                         content_filter: str = "off") -> List[Dict[str, Any]]:
        """
        Search for GIFs
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            content_filter: Content filter level (off, low, medium, high)
            
        Returns:
            List of GIF data dictionaries
        """
        if not self.initialized:
            raise TenorAPIError("Tenor client not initialized. Set TENOR_API_KEY in .env file.")
        
        # Track API usage
        analytics.track_api_call("tenor_search", True, 0, 
                                metadata={"query": query, "limit": limit})
        
        try:
            timer_id = performance_monitor.start_timer("tenor_search_api")
            
            params = {
                "key": self.api_key,
                "q": query,
                "limit": limit,
                "contentfilter": content_filter,
                "media_filter": "minimal"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params=params) as response:
                    response_time = performance_monitor.stop_timer(timer_id, "api_call")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Track successful API call
                        analytics.track_api_call("tenor_search", True, response_time, 
                                               metadata={"result_count": len(data.get("results", []))})
                        
                        return data.get("results", [])
                    else:
                        error_text = await response.text()
                        
                        # Track failed API call
                        analytics.track_api_call("tenor_search", False, response_time, 
                                               metadata={"error": error_text, "status": response.status})
                        
                        raise TenorAPIError(f"Tenor API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            # Track network error
            analytics.track_api_call("tenor_search", False, 0, 
                                   metadata={"error": str(e), "type": "network"})
            
            raise TenorAPIError(f"Network error: {str(e)}")
        except Exception as e:
            # Track unexpected error
            analytics.track_api_call("tenor_search", False, 0, 
                                   metadata={"error": str(e), "type": "unexpected"})
            
            raise TenorAPIError(f"Unexpected error: {str(e)}")
    
    @timed(operation_type="tenor_api")
    async def get_random_gif(self, query: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        Get a random GIF for a query
        
        Args:
            query: Search query
            limit: Maximum number of results to search from
            
        Returns:
            Random GIF data dictionary or None if no results
        """
        results = await self.search_gifs(query, limit)
        
        if not results:
            return None
        
        return random.choice(results)
    
    @timed(operation_type="tenor_api")
    async def get_trending_gifs(self, limit: int = 10, 
                              content_filter: str = "off") -> List[Dict[str, Any]]:
        """
        Get trending GIFs
        
        Args:
            limit: Maximum number of results to return
            content_filter: Content filter level (off, low, medium, high)
            
        Returns:
            List of GIF data dictionaries
        """
        if not self.initialized:
            raise TenorAPIError("Tenor client not initialized. Set TENOR_API_KEY in .env file.")
        
        # Track API usage
        analytics.track_api_call("tenor_trending", True, 0, 
                                metadata={"limit": limit})
        
        try:
            timer_id = performance_monitor.start_timer("tenor_trending_api")
            
            params = {
                "key": self.api_key,
                "limit": limit,
                "contentfilter": content_filter,
                "media_filter": "minimal"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/trending", params=params) as response:
                    response_time = performance_monitor.stop_timer(timer_id, "api_call")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Track successful API call
                        analytics.track_api_call("tenor_trending", True, response_time, 
                                               metadata={"result_count": len(data.get("results", []))})
                        
                        return data.get("results", [])
                    else:
                        error_text = await response.text()
                        
                        # Track failed API call
                        analytics.track_api_call("tenor_trending", False, response_time, 
                                               metadata={"error": error_text, "status": response.status})
                        
                        raise TenorAPIError(f"Tenor API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            # Track network error
            analytics.track_api_call("tenor_trending", False, 0, 
                                   metadata={"error": str(e), "type": "network"})
            
            raise TenorAPIError(f"Network error: {str(e)}")
        except Exception as e:
            # Track unexpected error
            analytics.track_api_call("tenor_trending", False, 0, 
                                   metadata={"error": str(e), "type": "unexpected"})
            
            raise TenorAPIError(f"Unexpected error: {str(e)}")
    
    def extract_gif_url(self, gif_data: Dict[str, Any], format_type: str = "gif") -> Optional[str]:
        """
        Extract GIF URL from Tenor API response
        
        Args:
            gif_data: GIF data dictionary from Tenor API
            format_type: Format type (gif, mediumgif, tinygif, mp4, etc.)
            
        Returns:
            GIF URL or None if not found
        """
        try:
            media_formats = gif_data.get("media_formats", {})
            
            if format_type in media_formats:
                return media_formats[format_type]["url"]
            
            # Fallback to other formats if requested format not found
            for fallback_format in ["gif", "mediumgif", "tinygif", "mp4", "webm"]:
                if fallback_format in media_formats:
                    return media_formats[fallback_format]["url"]
            
            return None
        except Exception as e:
            logging.error(f"Error extracting GIF URL: {e}")
            return None
