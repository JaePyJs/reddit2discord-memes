"""
Weather Commands

This module provides Discord commands for getting weather information using the OpenWeatherMap API.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta

from bot.features.weather.api import WeatherClient, WeatherAPIError
from bot.core.analytics import analytics
from bot.core.performance_monitor import timed

class WeatherCommands(commands.Cog):
    """Commands for getting weather information using the OpenWeatherMap API"""
    
    def __init__(self, bot):
        """
        Initialize the Weather commands
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.weather_client = WeatherClient()
        
        # Log initialization
        if self.weather_client.initialized:
            logging.info("Weather commands initialized")
        else:
            logging.warning("Weather commands initialized but API client not initialized")
    
    @app_commands.command(name="weather", description="Get current weather for a location")
    @app_commands.describe(
        location="City name or location",
        units="Units of measurement (metric, imperial, standard)"
    )
    @app_commands.choices(units=[
        app_commands.Choice(name="Metric (°C, m/s)", value="metric"),
        app_commands.Choice(name="Imperial (°F, mph)", value="imperial"),
        app_commands.Choice(name="Standard (K, m/s)", value="standard")
    ])
    @timed(operation_type="command")
    async def weather_command(self, interaction: discord.Interaction, 
                            location: str, units: str = "metric"):
        """
        Get current weather for a location
        
        Args:
            interaction: Discord interaction
            location: City name or location
            units: Units of measurement
        """
        # Track command usage
        analytics.track_command("weather", str(interaction.user.id), 
                              str(interaction.guild_id) if interaction.guild else None,
                              str(interaction.channel_id),
                              {"location": location, "units": units})
        
        # Defer response to allow time for API call
        await interaction.response.defer()
        
        try:
            if not self.weather_client.initialized:
                await interaction.followup.send(
                    "⚠️ OpenWeatherMap API is not configured. Please set OPENWEATHERMAP_API_KEY in the .env file.",
                    ephemeral=True
                )
                return
            
            # Get current weather
            weather_data = await self.weather_client.get_current_weather(location, units)
            
            # Create embed
            embed = discord.Embed(
                title=f"Weather for {weather_data['name']}, {weather_data.get('sys', {}).get('country', '')}",
                description=f"**{weather_data['weather'][0]['description'].capitalize()}**",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Add weather icon
            icon_code = weather_data['weather'][0]['icon']
            embed.set_thumbnail(url=self.weather_client.get_weather_icon_url(icon_code))
            
            # Add temperature information
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            temp_min = weather_data['main']['temp_min']
            temp_max = weather_data['main']['temp_max']
            
            embed.add_field(
                name="Temperature",
                value=f"Current: {self.weather_client.format_temperature(temp, units)}\n"
                      f"Feels like: {self.weather_client.format_temperature(feels_like, units)}\n"
                      f"Min: {self.weather_client.format_temperature(temp_min, units)}\n"
                      f"Max: {self.weather_client.format_temperature(temp_max, units)}",
                inline=True
            )
            
            # Add other weather information
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main']['pressure']
            wind_speed = weather_data['wind']['speed']
            wind_deg = weather_data.get('wind', {}).get('deg', 0)
            
            embed.add_field(
                name="Conditions",
                value=f"Humidity: {humidity}%\n"
                      f"Pressure: {pressure} hPa\n"
                      f"Wind: {self.weather_client.format_wind_speed(wind_speed, units)}\n"
                      f"Wind Direction: {self._get_wind_direction(wind_deg)}",
                inline=True
            )
            
            # Add sunrise and sunset
            sunrise = weather_data.get('sys', {}).get('sunrise', 0)
            sunset = weather_data.get('sys', {}).get('sunset', 0)
            
            if sunrise and sunset:
                embed.add_field(
                    name="Sun",
                    value=f"Sunrise: {self.weather_client.format_datetime(sunrise, '%H:%M')}\n"
                          f"Sunset: {self.weather_client.format_datetime(sunset, '%H:%M')}",
                    inline=False
                )
            
            # Add footer
            embed.set_footer(text="Powered by OpenWeatherMap")
            
            # Send the weather information
            await interaction.followup.send(embed=embed)
            
        except WeatherAPIError as e:
            logging.error(f"Weather API error: {e}")
            await interaction.followup.send(
                f"Error getting weather information: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Unexpected error in weather command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred",
                ephemeral=True
            )
    
    @app_commands.command(name="forecast", description="Get weather forecast for a location")
    @app_commands.describe(
        location="City name or location",
        days="Number of days to forecast (1-5)",
        units="Units of measurement (metric, imperial, standard)"
    )
    @app_commands.choices(units=[
        app_commands.Choice(name="Metric (°C, m/s)", value="metric"),
        app_commands.Choice(name="Imperial (°F, mph)", value="imperial"),
        app_commands.Choice(name="Standard (K, m/s)", value="standard")
    ])
    @timed(operation_type="command")
    async def forecast_command(self, interaction: discord.Interaction, 
                             location: str, days: int = 3, units: str = "metric"):
        """
        Get weather forecast for a location
        
        Args:
            interaction: Discord interaction
            location: City name or location
            days: Number of days to forecast
            units: Units of measurement
        """
        # Track command usage
        analytics.track_command("forecast", str(interaction.user.id), 
                              str(interaction.guild_id) if interaction.guild else None,
                              str(interaction.channel_id),
                              {"location": location, "days": days, "units": units})
        
        # Validate days
        if days < 1:
            days = 1
        elif days > 5:
            days = 5
        
        # Defer response to allow time for API call
        await interaction.response.defer()
        
        try:
            if not self.weather_client.initialized:
                await interaction.followup.send(
                    "⚠️ OpenWeatherMap API is not configured. Please set OPENWEATHERMAP_API_KEY in the .env file.",
                    ephemeral=True
                )
                return
            
            # Get forecast
            forecast_data = await self.weather_client.get_forecast(location, days, units)
            
            # Create embed
            embed = discord.Embed(
                title=f"{days}-Day Forecast for {forecast_data['city']['name']}, {forecast_data['city']['country']}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Group forecast by day
            daily_forecasts = self._group_forecast_by_day(forecast_data['list'])
            
            # Add forecast for each day
            for i, (day, forecasts) in enumerate(daily_forecasts.items()):
                if i >= days:
                    break
                
                # Get average values for the day
                avg_temp = sum(f['main']['temp'] for f in forecasts) / len(forecasts)
                min_temp = min(f['main']['temp_min'] for f in forecasts)
                max_temp = max(f['main']['temp_max'] for f in forecasts)
                
                # Get the most common weather condition
                conditions = {}
                for f in forecasts:
                    condition = f['weather'][0]['description']
                    conditions[condition] = conditions.get(condition, 0) + 1
                main_condition = max(conditions.items(), key=lambda x: x[1])[0]
                
                # Get icon for the main condition (use noon forecast if available)
                noon_forecast = next((f for f in forecasts if '12:00' in f['dt_txt']), forecasts[0])
                icon_code = noon_forecast['weather'][0]['icon']
                
                # Format the day
                day_date = datetime.strptime(day, '%Y-%m-%d')
                day_name = day_date.strftime('%A')
                
                # Add field for this day
                embed.add_field(
                    name=f"{day_name} ({day})",
                    value=f"**{main_condition.capitalize()}**\n"
                          f"Avg: {self.weather_client.format_temperature(avg_temp, units)}\n"
                          f"Min: {self.weather_client.format_temperature(min_temp, units)}\n"
                          f"Max: {self.weather_client.format_temperature(max_temp, units)}",
                    inline=True
                )
                
                # Add thumbnail for the first day
                if i == 0:
                    embed.set_thumbnail(url=self.weather_client.get_weather_icon_url(icon_code))
            
            # Add footer
            embed.set_footer(text="Powered by OpenWeatherMap")
            
            # Send the forecast
            await interaction.followup.send(embed=embed)
            
        except WeatherAPIError as e:
            logging.error(f"Weather API error: {e}")
            await interaction.followup.send(
                f"Error getting forecast: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Unexpected error in forecast command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred",
                ephemeral=True
            )
    
    def _group_forecast_by_day(self, forecast_list):
        """
        Group forecast data by day
        
        Args:
            forecast_list: List of forecast data points
            
        Returns:
            Dictionary mapping days to forecast data points
        """
        daily_forecasts = {}
        
        for forecast in forecast_list:
            # Extract date from datetime string
            date_str = forecast['dt_txt'].split(' ')[0]
            
            if date_str not in daily_forecasts:
                daily_forecasts[date_str] = []
                
            daily_forecasts[date_str].append(forecast)
        
        return daily_forecasts
    
    def _get_wind_direction(self, degrees):
        """
        Convert wind direction in degrees to cardinal direction
        
        Args:
            degrees: Wind direction in degrees
            
        Returns:
            Cardinal direction string
        """
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        
        index = round(degrees / 22.5) % 16
        return directions[index]

async def setup(bot):
    """
    Set up the Weather commands
    
    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(WeatherCommands(bot))
    logging.info("Weather commands cog registered")
