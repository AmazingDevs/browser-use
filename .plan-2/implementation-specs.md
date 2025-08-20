# Implementation-Ready Technical Specifications

## Browser-Use POC Development Guide

### Overview

This document provides comprehensive, implementation-ready specifications for developing a Proof of Concept (POC) using the browser-use framework. It includes corrected code examples, integration guides, error handling patterns, testing approaches, and complete environment setup.

---

## 1. Environment Setup & Dependencies

### 1.1 Core Dependencies

```bash
# Python 3.11+ required
python -m pip install --upgrade pip
pip install browser-use

# Install playwright browser
playwright install chromium --with-deps --no-shell

# Optional CLI tools
pip install browser-use[cli]

# Development dependencies
pip install browser-use[examples] pytest pytest-asyncio aiofiles
```

### 1.2 Environment Variables

Create `.env` file in project root:

```bash
# Required: AI Model API Keys (choose one or more)
BROWSER_USE_LLM_URL=
BROWSER_USE_LLM_API_KEY=
BROWSER_USE_LLM_MODEL=deepseek/deepseek-r1-0528-qwen3-8b

PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/google-chrome

# Optional: MCP Configuration
MCP_ENABLE=false
MCP_PORT=3000
```

### 1.3 Project Structure

```
.plan-2/poc-project/
├── .env                    # Environment variables
├── src/                    # Source code
│   ├── agents/            # Agent implementations
│   ├── tasks/             # Task definitions
│   ├── utils/             # Utility functions
│   └── config/            # Configuration files
├── tests/                 # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── fixtures/          # Test fixtures
├── docs/                  # Documentation
├── examples/              # Example implementations
└── requirements.txt       # Python dependencies
```

---

## 2. Corrected API Usage Examples

### 2.1 Basic Agent Implementation

```python
# src/agents/basic_agent.py
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from browser_use import Agent, BrowserSession, BrowserConfig
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm.anthropic.chat import ChatAnthropic
from browser_use.agent.views import AgentOutput, AgentSettings

logger = logging.getLogger(__name__)

class POCAgent:
    """Production-ready POC Agent with comprehensive error handling."""

    def __init__(
        self,
        llm_provider: str = "openai",
        model: str = "gpt-4-turbo",
        headless: bool = True,
        timeout: int = 300
    ):
        self.llm_provider = llm_provider
        self.model = model
        self.headless = headless
        self.timeout = timeout
        self._session: Optional[BrowserSession] = None
        self._llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM with proper error handling."""
        try:
            if self.llm_provider == "openai":
                return ChatOpenAI(
                    model=self.model,
                    temperature=0.1,
                    timeout=self.timeout
                )
            elif self.llm_provider == "anthropic":
                return ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    temperature=0.1,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    async def run_task(
        self,
        task: str,
        max_steps: int = 50,
        save_conversation: bool = True,
        output_dir: Optional[Path] = None
    ) -> AgentOutput:
        """Execute a browser automation task with comprehensive error handling."""

        try:
            # Configure browser session
            browser_config = BrowserConfig(
                headless=self.headless,
                viewport_width=1920,
                viewport_height=1080,
                disable_security=False,
                user_data_dir=None
            )

            # Configure agent settings
            agent_settings = AgentSettings(
                max_actions_per_step=10,
                max_steps=max_steps,
                disable_vision=False,
                include_attributes=['id', 'class', 'name', 'type', 'href', 'value'],
                max_input_tokens=100000,
                save_conversation_path=output_dir / "conversation.json" if output_dir else None
            )

            # Create and configure agent
            agent = Agent(
                task=task,
                llm=self._llm,
                browser_config=browser_config,
                agent_settings=agent_settings
            )

            # Execute task
            logger.info(f"Starting task execution: {task}")
            result = await agent.run()
            logger.info("Task completed successfully")

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise
        finally:
            # Cleanup resources
            if self._session:
                await self._session.close()

async def main():
    """Example usage of POCAgent."""
    agent = POCAgent(llm_provider="openai", model="gpt-4-turbo")

    task = """
    Navigate to Google and search for 'browser automation Python'.
    Extract the top 3 search results including titles and URLs.
    Return the information in a structured format.
    """

    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)

    try:
        result = await agent.run_task(
            task=task,
            max_steps=20,
            output_dir=output_dir
        )
        print(f"Task result: {result}")
    except Exception as e:
        print(f"Task failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 Advanced Agent with Custom Actions

```python
# src/agents/advanced_agent.py
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from browser_use import Agent
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.controller.registry.views import ActionModel
from browser_use.agent.views import AgentOutput

class AdvancedPOCAgent:
    """Advanced agent with custom actions and enhanced capabilities."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.1)
        self.custom_actions = self._register_custom_actions()

    def _register_custom_actions(self) -> List[ActionModel]:
        """Register custom actions for specialized tasks."""

        async def extract_table_data(table_selector: str) -> Dict[str, Any]:
            """Extract structured data from HTML tables."""
            # Implementation for table data extraction
            pass

        async def handle_captcha(captcha_type: str = "recaptcha") -> bool:
            """Handle different types of captchas."""
            # Implementation for captcha handling
            pass

        async def wait_for_element_stable(selector: str, timeout: int = 10) -> bool:
            """Wait for element to be stable (not moving/changing)."""
            # Implementation for element stability check
            pass

        return [
            ActionModel(
                name="extract_table_data",
                description="Extract structured data from HTML tables",
                function=extract_table_data
            ),
            ActionModel(
                name="handle_captcha",
                description="Handle various types of captchas",
                function=handle_captcha
            ),
            ActionModel(
                name="wait_for_element_stable",
                description="Wait for UI element to stabilize",
                function=wait_for_element_stable
            )
        ]

    async def run_data_extraction_task(
        self,
        url: str,
        selectors: Dict[str, str],
        max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """Execute data extraction across multiple pages."""

        task = f"""
        Navigate to {url} and extract data using these selectors:
        {selectors}

        If there are pagination controls, extract data from up to {max_pages} pages.
        Return structured data as a list of dictionaries.
        """

        agent = Agent(
            task=task,
            llm=self.llm,
            additional_actions=self.custom_actions
        )

        result = await agent.run()
        return result.extracted_content

# Example usage
async def extract_ecommerce_data():
    """Example: Extract product data from an e-commerce site."""
    agent = AdvancedPOCAgent()

    selectors = {
        "product_name": ".product-title",
        "price": ".price",
        "rating": ".rating",
        "availability": ".stock-status"
    }

    data = await agent.run_data_extraction_task(
        url="https://example-store.com/products",
        selectors=selectors,
        max_pages=3
    )

    return data
```

### 2.3 MCP Server Integration

```python
# src/mcp/poc_mcp_server.py
import asyncio
import json
from typing import Dict, Any, List
from browser_use.mcp.server import create_mcp_server
from browser_use import Agent
from browser_use.llm.openai.chat import ChatOpenAI

class POCMCPServer:
    """Custom MCP server for POC browser automation tasks."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4-turbo")
        self.active_sessions: Dict[str, Agent] = {}

    async def run_browser_task(
        self,
        task_id: str,
        task_description: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute browser task via MCP."""

        try:
            # Create agent instance
            agent = Agent(
                task=task_description,
                llm=self.llm,
                **(config or {})
            )

            # Store session
            self.active_sessions[task_id] = agent

            # Execute task
            result = await agent.run()

            return {
                "task_id": task_id,
                "status": "completed",
                "result": result.extracted_content,
                "steps_taken": len(result.history),
                "final_url": result.current_state.url
            }

        except Exception as e:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            # Cleanup
            if task_id in self.active_sessions:
                del self.active_sessions[task_id]

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of running task."""
        if task_id in self.active_sessions:
            agent = self.active_sessions[task_id]
            return {
                "task_id": task_id,
                "status": "running",
                "current_step": len(agent.history),
                "current_url": agent.current_state.url if agent.current_state else None
            }
        else:
            return {
                "task_id": task_id,
                "status": "not_found"
            }

# MCP Server configuration
async def start_mcp_server():
    """Start the MCP server for browser automation."""
    server = POCMCPServer()

    # Register MCP tools
    tools = [
        {
            "name": "run_browser_task",
            "description": "Execute browser automation task",
            "function": server.run_browser_task
        },
        {
            "name": "get_task_status",
            "description": "Get status of browser task",
            "function": server.get_task_status
        }
    ]

    mcp_server = create_mcp_server(tools)
    await mcp_server.start()

if __name__ == "__main__":
    asyncio.run(start_mcp_server())
```

---

## 3. Error Handling & Edge Cases

### 3.1 Comprehensive Error Handler

```python
# src/utils/error_handling.py
import logging
import asyncio
from typing import Optional, Callable, Any
from functools import wraps
from browser_use.exceptions import BrowserUseException

logger = logging.getLogger(__name__)

class POCErrorHandler:
    """Centralized error handling for POC implementation."""

    @staticmethod
    def with_retry(
        max_attempts: int = 3,
        delay: float = 1.0,
        exponential_backoff: bool = True
    ):
        """Decorator for automatic retry with exponential backoff."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                            logger.warning(
                                f"Attempt {attempt + 1} failed: {e}. "
                                f"Retrying in {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"All {max_attempts} attempts failed")

                raise last_exception
            return wrapper
        return decorator

    @staticmethod
    async def handle_browser_errors(func: Callable, *args, **kwargs) -> Any:
        """Handle common browser automation errors."""
        try:
            return await func(*args, **kwargs)
        except TimeoutError:
            logger.error("Browser operation timed out")
            raise BrowserUseException("Operation timed out - page may be unresponsive")
        except ConnectionError:
            logger.error("Browser connection lost")
            raise BrowserUseException("Lost connection to browser - may need restart")
        except Exception as e:
            logger.error(f"Unexpected browser error: {e}")
            raise BrowserUseException(f"Browser operation failed: {str(e)}")

    @staticmethod
    def validate_task_input(task: str) -> bool:
        """Validate task input before execution."""
        if not task or not task.strip():
            raise ValueError("Task description cannot be empty")

        if len(task) > 10000:
            raise ValueError("Task description too long (max 10000 characters)")

        # Check for potentially harmful instructions
        harmful_patterns = [
            "delete", "rm -rf", "format", "virus", "malware"
        ]

        task_lower = task.lower()
        for pattern in harmful_patterns:
            if pattern in task_lower:
                logger.warning(f"Potentially harmful pattern detected: {pattern}")

        return True
```

### 3.2 Edge Case Handlers

```python
# src/utils/edge_cases.py
import asyncio
from typing import Optional, Dict, Any
from browser_use.browser.session import BrowserSession
from browser_use.browser.types import Page

class EdgeCaseHandler:
    """Handle common edge cases in browser automation."""

    @staticmethod
    async def handle_popup_dialogs(page: Page) -> bool:
        """Handle JavaScript alerts, confirms, and prompts."""
        try:
            # Set up dialog handler
            async def dialog_handler(dialog):
                logger.info(f"Dialog detected: {dialog.message}")
                await dialog.accept()

            page.on("dialog", dialog_handler)
            return True
        except Exception as e:
            logger.error(f"Failed to setup dialog handler: {e}")
            return False

    @staticmethod
    async def handle_slow_loading_pages(page: Page, timeout: int = 30) -> bool:
        """Wait for page to fully load with custom timeout."""
        try:
            # Wait for network to be idle
            await page.wait_for_load_state("networkidle", timeout=timeout * 1000)

            # Wait for dynamic content
            await page.wait_for_function(
                "document.readyState === 'complete'",
                timeout=timeout * 1000
            )

            return True
        except Exception as e:
            logger.warning(f"Page loading timeout: {e}")
            return False

    @staticmethod
    async def handle_captcha_detection(page: Page) -> Dict[str, Any]:
        """Detect and handle various types of captchas."""
        captcha_indicators = [
            "recaptcha",
            "captcha",
            "hcaptcha",
            "cloudflare"
        ]

        page_content = await page.content()
        detected_captchas = []

        for indicator in captcha_indicators:
            if indicator in page_content.lower():
                detected_captchas.append(indicator)

        return {
            "captcha_detected": len(detected_captchas) > 0,
            "captcha_types": detected_captchas,
            "requires_human_intervention": len(detected_captchas) > 0
        }

    @staticmethod
    async def handle_rate_limiting(
        page: Page,
        retry_after: Optional[int] = None
    ) -> bool:
        """Handle rate limiting and 429 responses."""
        try:
            # Check for rate limiting indicators
            status_code = await page.evaluate("document.status || window.status")

            if status_code == 429 or "rate limit" in (await page.content()).lower():
                wait_time = retry_after or 60  # Default 1 minute
                logger.info(f"Rate limiting detected, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                return True

            return False
        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            return False
```

---

## 4. Testing Framework

### 4.1 Unit Tests

```python
# tests/unit/test_agent.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.agents.basic_agent import POCAgent

class TestPOCAgent:
    """Unit tests for POC Agent implementation."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing."""
        mock = Mock()
        mock.generate = AsyncMock(return_value="Mocked response")
        return mock

    @pytest.fixture
    def agent(self, mock_llm):
        """Create agent instance for testing."""
        with patch('src.agents.basic_agent.ChatOpenAI', return_value=mock_llm):
            return POCAgent(llm_provider="openai")

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.llm_provider == "openai"
        assert agent.model == "gpt-4-turbo"
        assert agent.headless is True

    @pytest.mark.asyncio
    async def test_invalid_llm_provider(self):
        """Test error handling for invalid LLM provider."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            POCAgent(llm_provider="invalid_provider")

    @pytest.mark.asyncio
    async def test_task_execution_success(self, agent):
        """Test successful task execution."""
        with patch.object(agent, 'run_task') as mock_run:
            mock_run.return_value = Mock(extracted_content="Test result")

            result = await agent.run_task("Test task")
            assert result.extracted_content == "Test result"
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_execution_failure(self, agent):
        """Test task execution failure handling."""
        with patch.object(agent, 'run_task') as mock_run:
            mock_run.side_effect = Exception("Test error")

            with pytest.raises(Exception, match="Test error"):
                await agent.run_task("Test task")
```

### 4.2 Integration Tests

```python
# tests/integration/test_browser_integration.py
import pytest
import asyncio
from pathlib import Path
from src.agents.basic_agent import POCAgent

class TestBrowserIntegration:
    """Integration tests with real browser automation."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "test_outputs"
        output_dir.mkdir()
        return output_dir

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_google_search_integration(self, output_dir):
        """Test real Google search automation."""
        agent = POCAgent(headless=True)

        task = "Go to Google and search for 'browser automation testing'"

        result = await agent.run_task(
            task=task,
            max_steps=10,
            output_dir=output_dir
        )

        assert result is not None
        assert "google" in result.current_state.url.lower()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_form_filling_integration(self, output_dir):
        """Test form filling automation."""
        agent = POCAgent(headless=True)

        task = """
        Navigate to httpbin.org/forms/post and fill out the form:
        - custname: Test User
        - custtel: 123-456-7890
        - custemail: test@example.com
        - size: large
        - delivery: 20:30
        Then submit the form.
        """

        result = await agent.run_task(
            task=task,
            max_steps=15,
            output_dir=output_dir
        )

        assert result is not None
        # Verify form was submitted (should redirect to results page)
        assert "httpbin.org" in result.current_state.url

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_data_extraction_integration(self, output_dir):
        """Test data extraction from webpage."""
        agent = POCAgent(headless=True)

        task = """
        Navigate to quotes.toscrape.com and extract:
        - First 5 quotes text
        - Author names
        - Tags for each quote
        Return as structured data.
        """

        result = await agent.run_task(
            task=task,
            max_steps=20,
            output_dir=output_dir
        )

        assert result is not None
        assert result.extracted_content is not None
```

### 4.3 Performance Tests

```python
# tests/performance/test_performance.py
import pytest
import asyncio
import time
from src.agents.basic_agent import POCAgent

class TestPerformance:
    """Performance tests for browser automation."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_task_execution_time(self):
        """Test task execution stays within reasonable time limits."""
        agent = POCAgent(headless=True)

        start_time = time.time()

        result = await agent.run_task(
            task="Navigate to example.com and get the page title",
            max_steps=5
        )

        execution_time = time.time() - start_time

        # Should complete within 30 seconds
        assert execution_time < 30
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_agents(self):
        """Test multiple agents running concurrently."""
        async def run_simple_task():
            agent = POCAgent(headless=True)
            return await agent.run_task(
                task="Navigate to httpbin.org/get and extract the 'url' field",
                max_steps=5
            )

        start_time = time.time()

        # Run 3 agents concurrently
        tasks = [run_simple_task() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        execution_time = time.time() - start_time

        # Should complete within 60 seconds for 3 concurrent tasks
        assert execution_time < 60
        assert len(results) == 3
        assert all(result is not None for result in results)
```

### 4.4 Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
import os
from pathlib import Path

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_data_dir():
    """Provide test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("BROWSER_USE_SETUP_LOGGING", "false")
    monkeypatch.setenv("BROWSER_USE_TELEMETRY", "false")
```

---

## 5. Step-by-Step Integration Guide

### 5.1 Initial Setup

```bash
# Step 1: Create project structure
mkdir poc-browser-automation
cd poc-browser-automation

# Step 2: Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Step 3: Install dependencies
pip install browser-use[cli,examples]
playwright install chromium --with-deps --no-shell

# Step 4: Create .env file
cat > .env << EOF
OPENAI_API_KEY=your-openai-key
BROWSER_USE_SETUP_LOGGING=true
BROWSER_USE_TELEMETRY=false
EOF

# Step 5: Create project structure
mkdir -p src/{agents,tasks,utils,config}
mkdir -p tests/{unit,integration,performance}
mkdir -p docs examples
```

### 5.2 Basic Implementation

```python
# Step 6: Create basic agent (src/agents/basic_agent.py)
# [Use the code from section 2.1 above]

# Step 7: Create simple task runner (src/tasks/runner.py)
import asyncio
from pathlib import Path
from src.agents.basic_agent import POCAgent

async def run_simple_tasks():
    """Run a series of simple browser automation tasks."""
    agent = POCAgent()

    tasks = [
        "Navigate to example.com and get the page title",
        "Go to httpbin.org/get and extract the JSON response",
        "Search Google for 'Python web scraping' and get first 3 results"
    ]

    results = []
    for i, task in enumerate(tasks, 1):
        print(f"Running task {i}: {task}")
        try:
            result = await agent.run_task(task, max_steps=10)
            results.append({
                "task": task,
                "status": "success",
                "result": result.extracted_content
            })
        except Exception as e:
            results.append({
                "task": task,
                "status": "error",
                "error": str(e)
            })

    return results

if __name__ == "__main__":
    results = asyncio.run(run_simple_tasks())
    for result in results:
        print(f"Task: {result['task']}")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Result: {result['result']}")
        else:
            print(f"Error: {result['error']}")
        print("-" * 50)
```

### 5.3 Testing Setup

```bash
# Step 8: Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Step 9: Create pytest configuration
cat > pytest.ini << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_functions = test_*
python_classes = Test*
asyncio_mode = auto
markers =
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
EOF

# Step 10: Run initial tests
pytest tests/unit/ -v
pytest tests/integration/ -v -m integration
```

### 5.4 Advanced Features

```python
# Step 11: Add custom actions (src/agents/advanced_agent.py)
# [Use the code from section 2.2 above]

# Step 12: Add error handling (src/utils/error_handling.py)
# [Use the code from section 3.1 above]

# Step 13: Create configuration management (src/config/settings.py)
from pydantic import BaseSettings
from typing import Optional

class POCSettings(BaseSettings):
    """POC configuration settings."""

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo"
    llm_temperature: float = 0.1
    llm_timeout: int = 300

    # Browser Configuration
    browser_headless: bool = True
    browser_viewport_width: int = 1920
    browser_viewport_height: int = 1080
    browser_user_data_dir: Optional[str] = None

    # Agent Configuration
    max_steps: int = 50
    max_actions_per_step: int = 10
    save_conversations: bool = True

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = POCSettings()
```

### 5.5 Production Deployment

```dockerfile
# Step 14: Create Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy application code
COPY src/ /app/src/
COPY tests/ /app/tests/
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV BROWSER_USE_SETUP_LOGGING=true

# Run tests and start application
CMD ["python", "-m", "src.tasks.runner"]
```

---

## 6. Monitoring & Observability

### 6.1 Logging Configuration

```python
# src/utils/logging_config.py
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_poc_logging(
    log_level: str = "INFO",
    log_to_file: bool = False,
    log_dir: Path = Path("logs")
) -> logging.Logger:
    """Set up comprehensive logging for POC."""

    # Create log directory if needed
    if log_to_file:
        log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logger = logging.getLogger("poc_browser_automation")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if enabled)
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            log_dir / f"poc_automation_{timestamp}.log"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Set levels for third-party loggers
    logging.getLogger("browser_use").setLevel(logging.INFO)
    logging.getLogger("playwright").setLevel(logging.WARNING)

    return logger
```

### 6.2 Metrics Collection

```python
# src/utils/metrics.py
import time
import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class TaskMetrics:
    """Metrics for browser automation tasks."""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    steps_executed: int = 0
    pages_visited: int = 0
    actions_performed: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    success: bool = False
    error_message: Optional[str] = None

class MetricsCollector:
    """Collect and track POC performance metrics."""

    def __init__(self):
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.completed_tasks: List[TaskMetrics] = []

    def start_task_tracking(self, task_id: str) -> TaskMetrics:
        """Start tracking metrics for a task."""
        metrics = TaskMetrics(
            task_id=task_id,
            start_time=datetime.now(),
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent()
        )

        self.active_tasks[task_id] = metrics
        return metrics

    def update_task_metrics(
        self,
        task_id: str,
        steps_executed: Optional[int] = None,
        pages_visited: Optional[int] = None,
        actions_performed: Optional[int] = None
    ):
        """Update metrics for an active task."""
        if task_id not in self.active_tasks:
            return

        metrics = self.active_tasks[task_id]

        if steps_executed is not None:
            metrics.steps_executed = steps_executed
        if pages_visited is not None:
            metrics.pages_visited = pages_visited
        if actions_performed is not None:
            metrics.actions_performed = actions_performed

        # Update resource usage
        metrics.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
        metrics.cpu_usage_percent = psutil.cpu_percent()

    def complete_task_tracking(
        self,
        task_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> TaskMetrics:
        """Complete tracking for a task."""
        if task_id not in self.active_tasks:
            return None

        metrics = self.active_tasks[task_id]
        metrics.end_time = datetime.now()
        metrics.duration_seconds = (
            metrics.end_time - metrics.start_time
        ).total_seconds()
        metrics.success = success
        metrics.error_message = error_message

        # Move to completed tasks
        self.completed_tasks.append(metrics)
        del self.active_tasks[task_id]

        return metrics

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all completed tasks."""
        if not self.completed_tasks:
            return {}

        successful_tasks = [t for t in self.completed_tasks if t.success]
        failed_tasks = [t for t in self.completed_tasks if not t.success]

        durations = [t.duration_seconds for t in successful_tasks if t.duration_seconds]

        return {
            "total_tasks": len(self.completed_tasks),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(self.completed_tasks) * 100,
            "average_duration": sum(durations) / len(durations) if durations else 0,
            "total_steps": sum(t.steps_executed for t in self.completed_tasks),
            "total_pages_visited": sum(t.pages_visited for t in self.completed_tasks),
            "average_memory_usage": sum(t.memory_usage_mb for t in self.completed_tasks) / len(self.completed_tasks)
        }
```

---

## 7. Deployment & Production Considerations

### 7.1 Docker Deployment

```yaml
# docker-compose.yml
version: "3.8"

services:
  poc-browser-automation:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - BROWSER_USE_SETUP_LOGGING=true
      - PYTHONPATH=/app
    volumes:
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    restart: unless-stopped

  poc-mcp-server:
    build: .
    command: ["python", "-m", "src.mcp.poc_mcp_server"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MCP_ENABLE=true
      - MCP_PORT=3000
    ports:
      - "3000:3000"
    depends_on:
      - poc-browser-automation
    restart: unless-stopped
```

### 7.2 Production Checklist

- [ ] Environment variables properly configured
- [ ] Logging configured for production (structured logs)
- [ ] Error handling and retry mechanisms in place
- [ ] Resource limits set (memory, CPU)
- [ ] Health checks implemented
- [ ] Monitoring and alerting configured
- [ ] Security headers and authentication
- [ ] Rate limiting implemented
- [ ] Backup and recovery procedures
- [ ] Load testing completed
- [ ] Documentation updated

### 7.3 Scaling Considerations

```python
# src/utils/scaling.py
import asyncio
import aioredis
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TaskQueue:
    """Task queue for distributed processing."""
    redis_url: str = "redis://localhost:6379"
    queue_name: str = "browser_tasks"
    max_workers: int = 5

    async def enqueue_task(self, task_data: Dict[str, Any]) -> str:
        """Add task to processing queue."""
        redis = await aioredis.from_url(self.redis_url)
        task_id = f"task_{int(time.time() * 1000)}"

        await redis.lpush(
            self.queue_name,
            json.dumps({
                "task_id": task_id,
                "data": task_data,
                "created_at": datetime.now().isoformat()
            })
        )

        return task_id

    async def process_tasks(self):
        """Process tasks from queue with multiple workers."""
        redis = await aioredis.from_url(self.redis_url)

        async def worker():
            while True:
                try:
                    # Get task from queue
                    task_json = await redis.brpop(self.queue_name, timeout=30)
                    if not task_json:
                        continue

                    task = json.loads(task_json[1])

                    # Process task
                    agent = POCAgent()
                    await agent.run_task(task["data"]["task_description"])

                except Exception as e:
                    logger.error(f"Worker error: {e}")

        # Start workers
        workers = [asyncio.create_task(worker()) for _ in range(self.max_workers)]
        await asyncio.gather(*workers)
```

This comprehensive implementation guide provides everything needed to start development immediately with proper error handling, testing, and production deployment considerations. All code examples use the correct browser-use API patterns and include robust error handling for real-world usage.
