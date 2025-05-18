"""
Comprehensive test runner for the Discord bot.

This script runs all the tests for the Discord bot, including:
- Core features (music, Reddit, AI chat, Tenor GIFs, weather, Urban Dictionary)
- Temporarily disabled API integrations (Google Maps, News, Currency)
- Bot setup and configuration

Usage:
python -m tests.run_tests [options]

Options:
--all: Run all tests
--core: Run only core feature tests
--disabled: Run only temporarily disabled API tests
--setup: Run only bot setup tests
--feature=<feature>: Run tests for a specific feature (music, reddit, ai, tenor, weather, urban)
--api=<api>: Run tests for a specific API (maps, news, currency)
"""

import os
import sys
import unittest
import argparse

# Add parent directory to path so we can import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests(test_modules):
    """Run the specified test modules"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module in test_modules:
        try:
            # Import the module
            __import__(module)
            # Add the tests from the module to the suite
            suite.addTests(loader.loadTestsFromName(module))
        except ImportError as e:
            print(f"Error importing {module}: {e}")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description="Run tests for the Discord bot")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--core", action="store_true", help="Run only core feature tests")
    parser.add_argument("--disabled", action="store_true", help="Run only temporarily disabled API tests")
    parser.add_argument("--setup", action="store_true", help="Run only bot setup tests")
    parser.add_argument("--feature", choices=["music", "reddit", "ai", "tenor", "weather", "urban"],
                        help="Run tests for a specific feature")
    parser.add_argument("--api", choices=["maps", "news", "currency"],
                        help="Run tests for a specific API")

    args = parser.parse_args()

    # Define test modules
    core_tests = [
        "tests.features.test_music",
        "tests.features.test_reddit",
        "tests.features.test_ai",
        "tests.features.test_tenor",
        "tests.features.test_weather",
        "tests.features.test_urban"
    ]

    disabled_api_tests = [
        "tests.features.test_disabled_apis"
    ]

    setup_tests = [
        "tests.test_bot_setup",
        "tests.test_api_clients"
    ]

    # Determine which tests to run
    if args.all:
        # Skip disabled API tests for now since they're temporarily disabled
        test_modules = core_tests + setup_tests
    elif args.core:
        test_modules = core_tests
    elif args.disabled:
        test_modules = disabled_api_tests
    elif args.setup:
        test_modules = setup_tests
    elif args.feature:
        feature_map = {
            "music": ["tests.features.test_music"],
            "reddit": ["tests.features.test_reddit"],
            "ai": ["tests.features.test_ai"],
            "tenor": ["tests.features.test_tenor"],
            "weather": ["tests.features.test_weather"],
            "urban": ["tests.features.test_urban"]
        }
        test_modules = feature_map.get(args.feature, [])
    elif args.api:
        # For disabled APIs, we run the specific test from the test_disabled_apis module
        test_modules = ["tests.features.test_disabled_apis"]
    else:
        # Default to running core tests
        test_modules = core_tests

    # Run the tests
    result = run_tests(test_modules)

    # Return non-zero exit code if tests failed
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    main()
