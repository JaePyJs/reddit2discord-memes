"""
Test script for API integrations.

This script tests the functionality of the API integrations:
- Google Maps API
- News API
- Currency API

Usage:
python -m tests.test_api_integrations
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("api-tester")

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

async def test_maps_api():
    """Test Google Maps API functionality"""
    print("\n===== GOOGLE MAPS API TEST =====")
    
    try:
        from bot.features.maps.api import MapsClient
        
        # Initialize Maps client
        maps_client = MapsClient()
        
        if not maps_client.initialized:
            print("❌ Google Maps client failed to initialize")
            print("   Make sure GOOGLE_MAPS_API_KEY is set in your .env file")
            return False
        
        print("✅ Google Maps client initialized successfully")
        
        # Test geocoding
        print("\nTesting geocoding...")
        location = "New York, NY"
        geocode_result = await maps_client.geocode(location)
        
        if geocode_result["status"] == "OK" and geocode_result["results"]:
            result = geocode_result["results"][0]
            print(f"✅ Successfully geocoded '{location}'")
            print(f"   Formatted address: {result['formatted_address']}")
            print(f"   Coordinates: {result['geometry']['location']['lat']}, {result['geometry']['location']['lng']}")
            return True
        else:
            print(f"❌ Failed to geocode '{location}'")
            print(f"   Status: {geocode_result['status']}")
            return False
        
    except Exception as e:
        print(f"❌ Error during Google Maps API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_news_api():
    """Test News API functionality"""
    print("\n===== NEWS API TEST =====")
    
    try:
        from bot.features.news.api import NewsClient
        
        # Initialize News client
        news_client = NewsClient()
        
        if not news_client.initialized:
            print("❌ News client failed to initialize")
            print("   Make sure NEWS_API_KEY is set in your .env file")
            return False
        
        print("✅ News client initialized successfully")
        
        # Test top headlines
        print("\nTesting top headlines...")
        headlines_result = await news_client.get_top_headlines(country="us", page_size=3)
        
        if headlines_result["status"] == "ok" and headlines_result["articles"]:
            print(f"✅ Successfully retrieved top headlines")
            print(f"   Total results: {headlines_result['totalResults']}")
            print(f"   First article: {headlines_result['articles'][0]['title']}")
            return True
        else:
            print(f"❌ Failed to retrieve top headlines")
            print(f"   Status: {headlines_result['status']}")
            return False
        
    except Exception as e:
        print(f"❌ Error during News API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_currency_api():
    """Test Currency API functionality"""
    print("\n===== CURRENCY API TEST =====")
    
    try:
        from bot.features.currency.api import CurrencyClient
        
        # Initialize Currency client
        currency_client = CurrencyClient()
        
        if not currency_client.initialized:
            print("❌ Currency client failed to initialize")
            print("   Make sure CURRENCY_API_KEY is set in your .env file")
            return False
        
        print("✅ Currency client initialized successfully")
        
        # Test latest rates
        print("\nTesting latest exchange rates...")
        rates_result = await currency_client.get_latest_rates(base_currency="USD")
        
        if rates_result.get("success", False) and rates_result.get("rates"):
            print(f"✅ Successfully retrieved latest exchange rates")
            print(f"   Base currency: {rates_result.get('base', 'USD')}")
            print(f"   EUR rate: {rates_result.get('rates', {}).get('EUR', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to retrieve latest exchange rates")
            print(f"   Error: {rates_result.get('error', {}).get('info', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error during Currency API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_tests():
    """Run all API tests"""
    maps_result = await test_maps_api()
    news_result = await test_news_api()
    currency_result = await test_currency_api()
    
    print("\n===== TEST SUMMARY =====")
    print(f"Google Maps API: {'✅ PASSED' if maps_result else '❌ FAILED'}")
    print(f"News API: {'✅ PASSED' if news_result else '❌ FAILED'}")
    print(f"Currency API: {'✅ PASSED' if currency_result else '❌ FAILED'}")
    
    if maps_result and news_result and currency_result:
        print("\n✅ All API tests passed!")
        return True
    else:
        print("\n❌ Some API tests failed. Check the logs for details.")
        return False

if __name__ == "__main__":
    asyncio.run(run_tests())
