# POC Testing Framework

Comprehensive testing framework for the browser automation POC project.

## Overview

This testing framework provides complete test coverage for the POC including:

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Browser automation and workflow testing
- **Performance Tests**: Timing, memory, and load testing
- **End-to-End Tests**: Complete user journey validation

## Directory Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── pytest.ini                 # Pytest settings and markers
├── requirements.txt            # Testing dependencies
├── README.md                   # This file
├── unit/                       # Unit tests
│   ├── test_exploratory_qa_generator.py
│   └── test_test_models.py
├── integration/                # Integration tests
│   └── test_browser_integration.py
├── performance/                # Performance tests
│   └── test_performance.py
├── fixtures/                   # Test data and fixtures
│   └── sample_test_data.py
├── utils/                      # Test utilities
│   └── test_helpers.py
├── logs/                       # Test execution logs
└── reports/                    # Test reports and coverage
```

## Quick Start

### 1. Install Dependencies

```bash
# Install test requirements
pip install -r tests/requirements.txt

# Install browser dependencies (if using Playwright)
playwright install chromium --with-deps
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                 # Unit tests only
pytest -m integration          # Integration tests only
pytest -m performance          # Performance tests only

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run tests in parallel
pytest -n auto

# Run with detailed output
pytest -v --tb=long
```

### 3. Environment Setup

Create a `.env` file for test configuration:

```bash
# Test environment variables
PYTEST_RUNNING=true
TEST_ENV=development
BROWSER_HEADLESS=true
TEST_TIMEOUT=300

# Mock LLM settings
TEST_LLM_PROVIDER=mock
TEST_LLM_MODEL=test-model

# Browser settings
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
SELENIUM_HEADLESS=true
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests for individual components:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific unit test file
pytest tests/unit/test_exploratory_qa_generator.py -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing
```

**What's tested:**

- Agent initialization and configuration
- Test case generation logic
- Selector extraction algorithms
- Data model validation
- Error handling patterns
- Hook system functionality

### Integration Tests (`tests/integration/`)

Tests requiring browser automation and external services:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run browser integration tests
pytest tests/integration/test_browser_integration.py -v

# Run with specific browser
pytest tests/integration/ --browser=chromium
```

**What's tested:**

- Complete browser automation workflows
- Page navigation and interaction
- Form filling and submission
- Data extraction processes
- Error recovery scenarios
- Multi-step test execution

### Performance Tests (`tests/performance/`)

Timing, memory, and load testing:

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run specific performance categories
pytest -m performance --durations=0

# Run load testing scenarios
pytest tests/performance/ -k "load" -v
```

**What's tested:**

- Execution timing thresholds
- Memory usage monitoring
- Concurrent operation performance
- Load testing scenarios
- Resource utilization
- Performance regression detection

## Test Configuration

### Pytest Markers

Use markers to categorize and filter tests:

```python
@pytest.mark.unit
def test_basic_functionality():
    pass

@pytest.mark.integration
@pytest.mark.browser
async def test_browser_automation():
    pass

@pytest.mark.performance
@pytest.mark.slow
def test_load_scenario():
    pass
```

Available markers:

- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests
- `performance`: Performance tests
- `e2e`: End-to-end tests
- `slow`: Slow running tests (> 30 seconds)
- `browser`: Browser automation required
- `llm`: LLM integration required
- `smoke`: Basic functionality tests
- `regression`: Regression tests

### Test Fixtures

Common fixtures available in `conftest.py`:

```python
def test_with_mock_browser(mock_browser_page):
    # Use mock browser page
    pass

def test_with_sample_data(sample_test_cases):
    # Use sample test case data
    pass

def test_performance(performance_thresholds):
    # Use performance thresholds
    pass
```

### Environment Configuration

Configure test behavior via environment variables:

```bash
# Headless browser mode
export BROWSER_HEADLESS=true

# Test timeout
export TEST_TIMEOUT=300

# Log level
export LOG_LEVEL=DEBUG

# Test data directory
export TEST_DATA_DIR=/path/to/test/data
```

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestQAGenerator:
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.generate = AsyncMock(return_value="test response")
        return llm

    @pytest.mark.asyncio
    async def test_generate_test_cases(self, mock_llm):
        generator = QAGenerator(llm=mock_llm)
        result = await generator.generate_test_cases("test content", "test url")

        assert len(result) > 0
        assert result[0]["title"] is not None
        mock_llm.generate.assert_called_once()
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.browser
class TestBrowserIntegration:
    @pytest.mark.asyncio
    async def test_login_workflow(self, browser_session):
        page = browser_session.current_page

        await page.goto("https://www.saucedemo.com/login")
        await page.fill("#email", "test@example.com")
        await page.fill("#password", "password")
        await page.click("#login-btn")

        assert "dashboard" in page.url
```

### Performance Test Example

```python
@pytest.mark.performance
class TestPerformance:
    @pytest.mark.asyncio
    async def test_execution_time(self, performance_thresholds):
        start_time = time.time()

        # Execute operation
        result = await some_operation()

        duration = time.time() - start_time
        assert duration < performance_thresholds["response_time"]
```

## Test Data Management

### Using Sample Data

```python
def test_with_sample_data(sample_test_cases, sample_selectors):
    # Use predefined test cases
    login_test = next(tc for tc in sample_test_cases if "login" in tc["id"])

    # Use predefined selectors
    auth_selectors = sample_selectors["authentication"]

    assert login_test["priority"] == "high"
    assert auth_selectors["email_input"] == "#email"
```

### Creating Custom Test Data

```python
def test_with_custom_data():
    test_case = {
        "id": "custom_test_001",
        "title": "Custom Test",
        "steps": [
            {"action": "navigate", "url": "https://www.saucedemo.com"},
            {"action": "click", "selector": "#button"}
        ]
    }

    # Use custom test case
    assert len(test_case["steps"]) == 2
```

## Debugging Tests

### Running Specific Tests

```bash
# Run single test
pytest tests/unit/test_qa_generator.py::TestQAGenerator::test_generate_test_cases -v

# Run tests matching pattern
pytest -k "login" -v

# Run failed tests from last run
pytest --lf

# Run until first failure
pytest -x
```

### Debug Mode

```bash
# Run with Python debugger
pytest --pdb

# Run with pudb debugger
pytest --pudb

# Capture output
pytest -s -v
```

### Logging

Test logs are automatically captured:

```bash
# View test logs
tail -f tests/logs/pytest.log

# Run with live logging
pytest --log-cli-level=DEBUG -s
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
          playwright install chromium --with-deps

      - name: Run unit tests
        run: pytest tests/unit/ --cov=src --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration/ -x

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Reports

### HTML Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Generate HTML test report
pytest --html=tests/reports/report.html
```

### JSON Reports

```bash
# Generate JSON report
pytest --json-report --json-report-file=tests/reports/report.json
```

### Allure Reports

```bash
# Generate Allure report
pytest --alluredir=tests/reports/allure-results
allure serve tests/reports/allure-results
```

## Best Practices

### Test Organization

1. **Group related tests** in classes
2. **Use descriptive test names** that explain what is being tested
3. **Keep tests independent** - no test should depend on another
4. **Use fixtures** for common setup and teardown
5. **Mock external dependencies** in unit tests

### Test Data

1. **Use factories** for generating test data
2. **Keep test data small** and focused
3. **Clean up** temporary data after tests
4. **Use realistic data** that matches production scenarios

### Performance

1. **Run unit tests frequently** (they should be fast)
2. **Run integration tests** before commits
3. **Run performance tests** periodically
4. **Use parallel execution** for large test suites

### Maintenance

1. **Review test failures** promptly
2. **Update tests** when requirements change
3. **Remove obsolete tests** regularly
4. **Document complex test scenarios**

## Troubleshooting

### Common Issues

**Browser tests fail:**

```bash
# Install browser dependencies
playwright install chromium --with-deps

# Check browser configuration
pytest tests/integration/ --headed --slowmo=1000
```

**Import errors:**

```bash
# Check PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Install in development mode
pip install -e .
```

**Async test issues:**

```bash
# Check asyncio mode in pytest.ini
# Ensure pytest-asyncio is installed
pip install pytest-asyncio
```

**Performance test inconsistency:**

```bash
# Run with consistent environment
pytest tests/performance/ --benchmark-only
```

### Getting Help

1. Check test logs in `tests/logs/`
2. Run with verbose output: `pytest -v -s`
3. Use debugger: `pytest --pdb`
4. Check configuration: `pytest --collect-only`

## Contributing

When adding new tests:

1. **Follow naming conventions**: `test_*.py` for files, `test_*` for functions
2. **Add appropriate markers**: `@pytest.mark.unit`, etc.
3. **Include docstrings**: Explain what the test validates
4. **Update test data**: Add to `fixtures/sample_test_data.py` if needed
5. **Document complex scenarios**: Add comments for non-obvious test logic
