# Testing Framework

This directory contains tests for the Discord bot. The tests are organized by feature and type.

## Test Types

- **Unit Tests**: Test individual functions and methods in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete workflows

## Running Tests

### Running All Tests

To run all tests, use pytest:

```bash
# From the project root
pytest tests/
```

### Running Specific Tests

To run a specific test file:

```bash
# From the project root
pytest tests/test_api_integrations.py
```

To run tests for a specific feature:

```bash
# From the project root
pytest tests/features/
```

### Running with Coverage

To run tests with coverage reporting:

```bash
# From the project root
pytest --cov=bot tests/
```

To generate an HTML coverage report:

```bash
# From the project root
pytest --cov=bot --cov-report=html tests/
```

## Test Files

### API Integration Tests

- `test_api_integrations.py`: Tests for API clients (Google Maps, News, Currency)
- `test_spotify_integration.py`: Tests for Spotify API integration
- `test_spotify_fixed.py`: Tests for fixed Spotify URL parsing
- `test_spotify_basic.py`: Basic tests for Spotify functionality

### Command Tests

- `test_commands.py`: Tests for Discord commands
- `test_meme_command.py`: Tests for meme creation commands

### Feature Tests

- `features/test_weather_api.py`: Tests for OpenWeatherMap API

### Utility Tests

- `test_effects.py`: Tests for meme effects
- `simple_test.py`: Simple test for meme effects
- `test_mongodb.py`: Tests for MongoDB integration

## Writing Tests

### Unit Tests

Unit tests should:
- Test a single function or method
- Mock external dependencies
- Be fast and isolated

Example:

```python
def test_get_currency_symbol():
    """Test the get_currency_symbol method"""
    currency_commands = CurrencyCommands(MagicMock())
    assert currency_commands.get_currency_symbol("USD") == "$"
    assert currency_commands.get_currency_symbol("EUR") == "€"
    assert currency_commands.get_currency_symbol("UNKNOWN") == "UNKNOWN"
```

### Integration Tests

Integration tests should:
- Test interactions between components
- Mock external APIs
- Verify correct data flow

Example:

```python
async def test_news_command():
    """Test the news command with mocked API"""
    # Mock the News API client
    with patch('bot.features.news.api.NewsClient') as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_top_headlines.return_value = {
            "status": "ok",
            "articles": [...]
        }
        
        # Create the command instance
        news_commands = NewsCommands(MagicMock())
        
        # Test the command
        interaction = MockInteraction()
        await news_commands.news_command(interaction, "business", "us")
        
        # Verify the API was called correctly
        mock_client.get_top_headlines.assert_called_once_with(
            country="us",
            category="business",
            query=None,
            page_size=5
        )
```

### End-to-End Tests

End-to-end tests should:
- Test complete workflows
- Use minimal mocking
- Verify user-visible outcomes

Example:

```python
async def test_convert_currency_workflow():
    """Test the complete currency conversion workflow"""
    # Set up the bot with real components
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
    await bot.add_cog(CurrencyCommands(bot))
    
    # Create a mock interaction
    interaction = MockInteraction()
    
    # Execute the command
    cog = bot.get_cog("CurrencyCommands")
    await cog.convert_command(interaction, 100, "USD", "EUR")
    
    # Verify the response
    args, kwargs = interaction.followup.send.call_args
    embed = kwargs.get("embed")
    assert "USD" in embed.description
    assert "EUR" in embed.description
```

## Mocking

### Mock Interactions

For testing Discord commands, use the `MockInteraction` class:

```python
class MockInteraction:
    """Mock Discord Interaction for testing commands"""
    
    def __init__(self):
        self.response = AsyncMock()
        self.followup = AsyncMock()
        self.guild = MagicMock()
        self.guild.name = "Test Guild"
        self.user = MagicMock()
        self.user.id = 123456789
```

### Mock API Clients

For testing API integrations, mock the API clients:

```python
with patch('bot.features.maps.api.MapsClient') as mock_client_class:
    mock_client = mock_client_class.return_value
    mock_client.geocode.return_value = {
        "status": "OK",
        "results": [...]
    }
    
    # Test code that uses the client
```

## Continuous Integration

Tests are automatically run in the CI/CD pipeline using GitHub Actions. See `.github/workflows/ci-cd.yml` for details.

## Test Coverage

The goal is to maintain at least 80% test coverage for the codebase. Coverage reports are generated during CI runs and can be viewed in the GitHub Actions workflow summary.
