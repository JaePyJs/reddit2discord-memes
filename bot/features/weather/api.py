"""
OpenWeatherMap API Client

This module provides a client for interacting with the OpenWeatherMap API.
"""

import aiohttp
import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Union
import asyncio
from datetime import datetime, timedelta

from bot.core.config import OPENWEATHERMAP_API_KEY
from bot.core.analytics import analytics
from bot.core.performance_monitor import performance_monitor, timed

class WeatherAPIError(Exception):
    """Base exception for OpenWeatherMap API errors"""
    pass

class WeatherClient:
    """Client for interacting with the OpenWeatherMap API"""
    
    def __init__(self):
        """Initialize the OpenWeatherMap client"""
        self.api_key = OPENWEATHERMAP_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.initialized = bool(self.api_key)
        
        if not self.initialized:
            logging.error("OpenWeatherMap API key not found. Set OPENWEATHERMAP_API_KEY in .env file.")
        else:
            logging.info("OpenWeatherMap client initialized")
    
    @timed(operation_type="weather_api")
    async def get_current_weather(self, location: str, units: str = "metric") -> Dict[str, Any]:
        """
        Get current weather for a location
        
        Args:
            location: Location name or coordinates
            units: Units of measurement (metric, imperial, standard)
            
        Returns:
            Weather data dictionary
        """
        if not self.initialized:
            raise WeatherAPIError("OpenWeatherMap client not initialized. Set OPENWEATHERMAP_API_KEY in .env file.")
        
        # Track API usage
        analytics.track_api_call("weather_current", True, 0, 
                                metadata={"location": location, "units": units})
        
        try:
            timer_id = performance_monitor.start_timer("weather_current_api")
            
            params = {
                "q": location,
                "appid": self.api_key,
                "units": units
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/weather", params=params) as response:
                    response_time = performance_monitor.stop_timer(timer_id, "api_call")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Track successful API call
                        analytics.track_api_call("weather_current", True, response_time)
                        
                        return data
                    else:
                        error_text = await response.text()
                        
                        # Track failed API call
                        analytics.track_api_call("weather_current", False, response_time, 
                                               metadata={"error": error_text, "status": response.status})
                        
                        raise WeatherAPIError(f"OpenWeatherMap API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            # Track network error
            analytics.track_api_call("weather_current", False, 0, 
                                   metadata={"error": str(e), "type": "network"})
            
            raise WeatherAPIError(f"Network error: {str(e)}")
        except Exception as e:
            # Track unexpected error
            analytics.track_api_call("weather_current", False, 0, 
                                   metadata={"error": str(e), "type": "unexpected"})
            
            raise WeatherAPIError(f"Unexpected error: {str(e)}")
    
    @timed(operation_type="weather_api")
    async def get_forecast(self, location: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
        """
        Get weather forecast for a location
        
        Args:
            location: Location name or coordinates
            days: Number of days to forecast (max 5)
            units: Units of measurement (metric, imperial, standard)
            
        Returns:
            Forecast data dictionary
        """
        if not self.initialized:
            raise WeatherAPIError("OpenWeatherMap client not initialized. Set OPENWEATHERMAP_API_KEY in .env file.")
        
        # Track API usage
        analytics.track_api_call("weather_forecast", True, 0, 
                                metadata={"location": location, "days": days, "units": units})
        
        try:
            timer_id = performance_monitor.start_timer("weather_forecast_api")
            
            params = {
                "q": location,
                "appid": self.api_key,
                "units": units,
                "cnt": min(days * 8, 40)  # 8 forecasts per day, max 40 (5 days)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/forecast", params=params) as response:
                    response_time = performance_monitor.stop_timer(timer_id, "api_call")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Track successful API call
                        analytics.track_api_call("weather_forecast", True, response_time)
                        
                        return data
                    else:
                        error_text = await response.text()
                        
                        # Track failed API call
                        analytics.track_api_call("weather_forecast", False, response_time, 
                                               metadata={"error": error_text, "status": response.status})
                        
                        raise WeatherAPIError(f"OpenWeatherMap API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            # Track network error
            analytics.track_api_call("weather_forecast", False, 0, 
                                   metadata={"error": str(e), "type": "network"})
            
            raise WeatherAPIError(f"Network error: {str(e)}")
        except Exception as e:
            # Track unexpected error
            analytics.track_api_call("weather_forecast", False, 0, 
                                   metadata={"error": str(e), "type": "unexpected"})
            
            raise WeatherAPIError(f"Unexpected error: {str(e)}")
    
    def get_weather_icon_url(self, icon_code: str) -> str:
        """
        Get weather icon URL
        
        Args:
            icon_code: Weather icon code
            
        Returns:
            Weather icon URL
        """
        return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
    
    def format_temperature(self, temp: float, units: str = "metric") -> str:
        """
        Format temperature with appropriate unit
        
        Args:
            temp: Temperature value
            units: Units of measurement (metric, imperial, standard)
            
        Returns:
            Formatted temperature string
        """
        if units == "metric":
            return f"{temp:.1f}°C"
        elif units == "imperial":
            return f"{temp:.1f}°F"
        else:
            return f"{temp:.1f}K"
    
    def format_wind_speed(self, speed: float, units: str = "metric") -> str:
        """
        Format wind speed with appropriate unit
        
        Args:
            speed: Wind speed value
            units: Units of measurement (metric, imperial, standard)
            
        Returns:
            Formatted wind speed string
        """
        if units == "metric":
            return f"{speed:.1f} m/s"
        elif units == "imperial":
            return f"{speed:.1f} mph"
        else:
            return f"{speed:.1f} m/s"
    
    def format_datetime(self, timestamp: int, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format Unix timestamp to datetime string
        
        Args:
            timestamp: Unix timestamp
            format_str: Datetime format string
            
        Returns:
            Formatted datetime string
        """
        return datetime.fromtimestamp(timestamp).strftime(format_str)
