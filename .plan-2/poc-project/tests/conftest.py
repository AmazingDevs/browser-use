"""
Pytest configuration for POC browser automation testing framework.

This module provides comprehensive test configuration including:
- Async test support with pytest-asyncio
- Custom markers for test categorization
- Mock fixtures for browser operations
- Test data fixtures and utilities
- Environment setup and teardown
"""

import pytest
import asyncio
import os
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Test environment configuration
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", 
        "unit: mark test as unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test (requires browser)"
    )
    config.addinivalue_line(
        "markers", 
        "performance: mark test as performance test (timing sensitive)"
    )
    config.addinivalue_line(
        "markers", 
        "e2e: mark test as end-to-end test (full workflow)"
    )
    config.addinivalue_line(
        "markers", 
        "slow: mark test as slow running (> 30 seconds)"
    )
    config.addinivalue_line(
        "markers", 
        "browser: mark test as requiring browser automation"
    )
    config.addinivalue_line(
        "markers", 
        "llm: mark test as requiring LLM integration"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration settings."""
    return {
        "browser": {
            "headless": True,
            "viewport_width": 1280,
            "viewport_height": 720,
            "timeout": 30000,
            "slow_mo": 0
        },
        "llm": {
            "provider": "mock",
            "model": "test-model",
            "temperature": 0.0,
            "max_tokens": 1000
        },
        "agent": {
            "max_steps": 10,
            "max_actions_per_step": 5,
            "timeout": 60
        },
        "test_urls": {
            "example": "https://www.saucedemo.com",
            "httpbin": "https://httpbin.org",
            "quotes": "https://quotes.toscrape.com"
        }
    }

@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "test_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        yield output_dir

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    test_env_vars = {
        "OPENAI_API_KEY": "sk-test-key-12345",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "BROWSER_USE_SETUP_LOGGING": "false",
        "BROWSER_USE_TELEMETRY": "false",
        "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD": "1",
        "PYTEST_RUNNING": "true"
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)
    
    yield test_env_vars

@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    mock = Mock()
    mock.generate = AsyncMock(return_value="Mocked LLM response")
    mock.agenerate = AsyncMock(return_value=["Mocked response 1", "Mocked response 2"])
    mock.chat = AsyncMock(return_value="Mocked chat response")
    mock.model_name = "test-model"
    mock.temperature = 0.0
    return mock

@pytest.fixture
def mock_browser_session():
    """Mock browser session for testing without actual browser."""
    session = Mock()
    session.start = AsyncMock()
    session.close = AsyncMock()
    session.new_page = AsyncMock()
    session.get_page = AsyncMock()
    session.current_page = Mock()
    session.pages = []
    return session

@pytest.fixture
def mock_browser_page():
    """Mock browser page for testing page interactions."""
    page = Mock()
    page.url = "https://www.saucedemo.com"
    page.title = AsyncMock(return_value="Test Page")
    page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.select_option = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    page.locator = Mock()
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    page.evaluate = AsyncMock()
    page.is_closed = Mock(return_value=False)
    return page

@pytest.fixture
def mock_agent_output():
    """Mock agent output for testing agent responses."""
    return {
        "task_id": "test-task-123",
        "status": "completed",
        "result": "Test task completed successfully",
        "steps_taken": 5,
        "final_url": "https://www.saucedemo.com/result",
        "extracted_content": {
            "title": "Test Page",
            "data": {"key": "value"},
            "selectors": ["#main", ".content", "h1"]
        },
        "execution_time": 15.5,
        "errors": []
    }

@pytest.fixture
def sample_test_cases():
    """Provide sample test cases for QA generation testing."""
    return [
        {
            "id": "tc_001",
            "title": "Login Functionality Test",
            "description": "Test user login with valid credentials",
            "steps": [
                "Navigate to login page",
                "Enter valid email",
                "Enter valid password", 
                "Click login button"
            ],
            "expected_result": "User successfully logged in and redirected to dashboard",
            "priority": "high",
            "type": "functional"
        },
        {
            "id": "tc_002", 
            "title": "Form Validation Test",
            "description": "Test form validation with invalid inputs",
            "steps": [
                "Navigate to contact form",
                "Enter invalid email format",
                "Submit form"
            ],
            "expected_result": "Error message displayed for invalid email",
            "priority": "medium",
            "type": "validation"
        },
        {
            "id": "tc_003",
            "title": "Page Load Performance Test", 
            "description": "Test page loading performance",
            "steps": [
                "Navigate to homepage",
                "Measure page load time"
            ],
            "expected_result": "Page loads within 3 seconds",
            "priority": "medium",
            "type": "performance"
        }
    ]

@pytest.fixture
def sample_selectors():
    """Provide sample CSS selectors for testing."""
    return {
        "login_form": {
            "email_input": "#email",
            "password_input": "#password", 
            "submit_button": "button[type='submit']",
            "error_message": ".error-message"
        },
        "navigation": {
            "main_menu": "nav.main-menu",
            "home_link": "a[href='/']",
            "about_link": "a[href='/about']"
        },
        "content": {
            "page_title": "h1",
            "main_content": "#main-content",
            "sidebar": ".sidebar"
        }
    }

@pytest.fixture
def test_metrics():
    """Provide test metrics tracking."""
    return {
        "start_time": datetime.now(),
        "memory_usage": 0.0,
        "cpu_usage": 0.0,
        "network_requests": 0,
        "page_loads": 0,
        "actions_performed": 0
    }

@pytest.fixture
def mock_playwright():
    """Mock Playwright for testing without browser dependencies."""
    with patch('playwright.async_api.async_playwright') as mock:
        playwright_mock = AsyncMock()
        browser_mock = AsyncMock()
        context_mock = AsyncMock()
        page_mock = AsyncMock()
        
        # Set up the mock chain
        mock.return_value.__aenter__.return_value = playwright_mock
        playwright_mock.chromium.launch.return_value = browser_mock
        browser_mock.new_context.return_value = context_mock
        context_mock.new_page.return_value = page_mock
        
        # Configure page mock
        page_mock.url = "https://www.saucedemo.com"
        page_mock.goto = AsyncMock()
        page_mock.content = AsyncMock(return_value="<html><body>Test</body></html>")
        page_mock.title = AsyncMock(return_value="Test Page")
        
        yield {
            "playwright": playwright_mock,
            "browser": browser_mock,
            "context": context_mock,
            "page": page_mock
        }

@pytest.fixture
def error_scenarios():
    """Provide common error scenarios for testing."""
    return {
        "timeout_error": {
            "type": "TimeoutError",
            "message": "Operation timed out after 30 seconds",
            "code": "TIMEOUT"
        },
        "element_not_found": {
            "type": "ElementNotFound", 
            "message": "Element with selector '#missing' not found",
            "code": "ELEMENT_NOT_FOUND"
        },
        "network_error": {
            "type": "NetworkError",
            "message": "Failed to connect to server",
            "code": "NETWORK_ERROR"
        },
        "llm_error": {
            "type": "LLMError",
            "message": "LLM API rate limit exceeded",
            "code": "LLM_RATE_LIMIT"
        }
    }

@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """Set up logging for tests."""
    import logging
    logging.getLogger("poc_testing").setLevel(logging.DEBUG)
    yield caplog

@pytest.fixture
def performance_thresholds():
    """Define performance test thresholds."""
    return {
        "page_load_time": 5.0,  # seconds
        "element_find_time": 2.0,  # seconds
        "form_submit_time": 3.0,  # seconds
        "memory_usage": 512,  # MB
        "cpu_usage": 80,  # percentage
        "response_time": 1.0  # seconds
    }

# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data before and after tests."""
    # Pre-test cleanup
    yield
    # Post-test cleanup - could add specific cleanup logic here
    pass

# Custom assertions for POC testing
class POCAssertions:
    """Custom assertions for POC testing."""
    
    @staticmethod
    def assert_valid_test_case(test_case: Dict[str, Any]):
        """Assert that a test case has valid structure."""
        required_fields = ["id", "title", "description", "steps", "expected_result"]
        for field in required_fields:
            assert field in test_case, f"Test case missing required field: {field}"
        
        assert len(test_case["steps"]) > 0, "Test case must have at least one step"
        assert test_case["title"].strip(), "Test case title cannot be empty"
    
    @staticmethod
    def assert_performance_within_threshold(actual: float, threshold: float, metric_name: str):
        """Assert that performance metric is within threshold."""
        assert actual <= threshold, f"{metric_name} {actual} exceeds threshold {threshold}"

@pytest.fixture
def poc_assertions():
    """Provide custom POC assertions."""
    return POCAssertions()

# Async test utilities
class AsyncTestUtils:
    """Utilities for async testing."""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Wait for a condition to become true."""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
                return True
            await asyncio.sleep(interval)
        return False
    
    @staticmethod
    async def measure_execution_time(coro):
        """Measure execution time of a coroutine."""
        import time
        start_time = time.time()
        result = await coro
        execution_time = time.time() - start_time
        return result, execution_time

@pytest.fixture
def async_utils():
    """Provide async test utilities."""
    return AsyncTestUtils()