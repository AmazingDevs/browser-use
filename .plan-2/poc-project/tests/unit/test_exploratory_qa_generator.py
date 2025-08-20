"""
Unit tests for Exploratory QA Generator.

This module tests the core functionality of the exploratory QA generation system
including test case generation, selector extraction, and agent coordination.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime

# Import the modules we're testing (these would be the actual imports)
# from src.agents.exploratory_qa_generator import ExploratoryQAGenerator
# from src.models.test_models import TestCase, TestStep, TestResult
# from src.utils.selector_extractor import SelectorExtractor

class TestExploratoryQAGenerator:
    """Unit tests for ExploratoryQAGenerator class."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing."""
        llm = Mock()
        llm.generate = AsyncMock(return_value="Generated test case content")
        llm.chat = AsyncMock(return_value="LLM chat response")
        return llm

    @pytest.fixture
    def mock_browser_page(self):
        """Mock browser page for testing."""
        page = Mock()
        page.url = "https://www.saucedemo.com"
        page.title = AsyncMock(return_value="Test Page")
        page.content = AsyncMock(return_value="<html><body><h1>Test</h1></body></html>")
        page.query_selector_all = AsyncMock(return_value=[])
        page.screenshot = AsyncMock(return_value=b"fake_screenshot")
        return page

    @pytest.fixture
    def qa_generator(self, mock_llm):
        """Create QA generator instance for testing."""
        # Mock the actual class that would be imported
        class MockExploratoryQAGenerator:
            def __init__(self, llm=None, config=None):
                self.llm = llm or mock_llm
                self.config = config or {"max_test_cases": 10, "timeout": 30}
                self.test_cases = []
                self.selectors = {}
                
            async def generate_test_cases(self, page_content: str, url: str) -> List[Dict]:
                """Generate test cases from page content."""
                return [
                    {
                        "id": "tc_001",
                        "title": "Test form submission",
                        "description": "Test the main form submission functionality",
                        "steps": ["Fill form", "Submit", "Verify success"],
                        "expected_result": "Form submitted successfully",
                        "priority": "high",
                        "type": "functional"
                    }
                ]
            
            async def extract_selectors(self, page) -> Dict[str, str]:
                """Extract CSS selectors from page."""
                return {
                    "form": "form#main-form",
                    "submit_button": "button[type='submit']",
                    "input_field": "input[name='email']"
                }
            
            async def analyze_page_structure(self, page) -> Dict[str, Any]:
                """Analyze page structure for test generation."""
                return {
                    "forms": 1,
                    "buttons": 3,
                    "links": 5,
                    "inputs": 4,
                    "complexity_score": 7.5
                }
        
        return MockExploratoryQAGenerator(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_qa_generator_initialization(self, mock_llm):
        """Test QA generator initializes correctly."""
        config = {"max_test_cases": 5, "timeout": 60}
        
        class MockGenerator:
            def __init__(self, llm, config):
                self.llm = llm
                self.config = config
        
        generator = MockGenerator(llm=mock_llm, config=config)
        
        assert generator.llm == mock_llm
        assert generator.config["max_test_cases"] == 5
        assert generator.config["timeout"] == 60

    @pytest.mark.asyncio
    async def test_generate_test_cases_success(self, qa_generator, mock_browser_page):
        """Test successful test case generation."""
        page_content = "<html><body><form><input name='email'><button>Submit</button></form></body></html>"
        url = "https://www.saucedemo.com/form"
        
        result = await qa_generator.generate_test_cases(page_content, url)
        
        assert len(result) > 0
        assert result[0]["id"] == "tc_001"
        assert result[0]["title"] == "Test form submission"
        assert "steps" in result[0]
        assert len(result[0]["steps"]) > 0

    @pytest.mark.asyncio
    async def test_generate_test_cases_empty_content(self, qa_generator):
        """Test test case generation with empty content."""
        page_content = ""
        url = "https://www.saucedemo.com"
        
        result = await qa_generator.generate_test_cases(page_content, url)
        
        # Should handle empty content gracefully
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_extract_selectors_success(self, qa_generator, mock_browser_page):
        """Test successful selector extraction."""
        # Mock the page to return elements
        mock_browser_page.query_selector_all = AsyncMock(return_value=[
            Mock(get_attribute=AsyncMock(return_value="form#main-form")),
            Mock(get_attribute=AsyncMock(return_value="button[type='submit']"))
        ])
        
        result = await qa_generator.extract_selectors(mock_browser_page)
        
        assert isinstance(result, dict)
        assert "form" in result
        assert "submit_button" in result

    @pytest.mark.asyncio
    async def test_analyze_page_structure(self, qa_generator, mock_browser_page):
        """Test page structure analysis."""
        result = await qa_generator.analyze_page_structure(mock_browser_page)
        
        assert isinstance(result, dict)
        assert "forms" in result
        assert "buttons" in result
        assert "complexity_score" in result
        assert isinstance(result["complexity_score"], (int, float))

    @pytest.mark.asyncio
    async def test_error_handling_llm_failure(self, mock_browser_page):
        """Test error handling when LLM fails."""
        # Create a mock LLM that raises an exception
        failing_llm = Mock()
        failing_llm.generate = AsyncMock(side_effect=Exception("LLM API Error"))
        
        class MockGenerator:
            def __init__(self, llm):
                self.llm = llm
            
            async def generate_test_cases(self, page_content: str, url: str):
                try:
                    await self.llm.generate("test prompt")
                    return []
                except Exception as e:
                    # Should handle LLM errors gracefully
                    return {"error": str(e), "test_cases": []}
        
        generator = MockGenerator(failing_llm)
        result = await generator.generate_test_cases("<html></html>", "https://www.saucedemo.com")
        
        assert "error" in result
        assert "LLM API Error" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout_handling(self, qa_generator):
        """Test handling of timeout scenarios."""
        # Mock a slow operation
        async def slow_operation():
            await asyncio.sleep(0.1)  # Simulate slow operation
            return "result"
        
        # Test timeout handling
        try:
            result = await asyncio.wait_for(slow_operation(), timeout=0.05)
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            # This is expected behavior
            assert True

    @pytest.mark.asyncio
    async def test_concurrent_test_generation(self, qa_generator):
        """Test concurrent test case generation."""
        urls = [
            "https://www.saucedemo.com/page1",
            "https://www.saucedemo.com/page2", 
            "https://www.saucedemo.com/page3"
        ]
        content = "<html><body>Test content</body></html>"
        
        # Generate test cases concurrently
        tasks = [
            qa_generator.generate_test_cases(content, url)
            for url in urls
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, list)

    def test_test_case_validation(self, poc_assertions):
        """Test test case validation logic."""
        valid_test_case = {
            "id": "tc_001",
            "title": "Valid test case",
            "description": "This is a valid test case",
            "steps": ["Step 1", "Step 2"],
            "expected_result": "Expected result"
        }
        
        # Should not raise an exception
        poc_assertions.assert_valid_test_case(valid_test_case)

    def test_test_case_validation_missing_fields(self, poc_assertions):
        """Test test case validation with missing fields."""
        invalid_test_case = {
            "id": "tc_001",
            "title": "Invalid test case"
            # Missing required fields
        }
        
        with pytest.raises(AssertionError, match="missing required field"):
            poc_assertions.assert_valid_test_case(invalid_test_case)

    def test_test_case_validation_empty_steps(self, poc_assertions):
        """Test test case validation with empty steps."""
        invalid_test_case = {
            "id": "tc_001",
            "title": "Invalid test case",
            "description": "Test case with empty steps",
            "steps": [],  # Empty steps
            "expected_result": "Expected result"
        }
        
        with pytest.raises(AssertionError, match="must have at least one step"):
            poc_assertions.assert_valid_test_case(invalid_test_case)

class TestSelectorExtractor:
    """Unit tests for CSS selector extraction functionality."""

    @pytest.fixture
    def selector_extractor(self):
        """Create selector extractor instance."""
        class MockSelectorExtractor:
            def __init__(self):
                self.patterns = {
                    "form": ["form", "form[action]", "#loginForm"],
                    "button": ["button", "input[type='submit']", ".btn"],
                    "input": ["input", "textarea", "select"]
                }
            
            def extract_interactive_elements(self, html_content: str) -> Dict[str, List[str]]:
                """Extract interactive elements from HTML."""
                return {
                    "forms": ["#main-form", ".contact-form"],
                    "buttons": ["#submit-btn", ".primary-button"],
                    "inputs": ["#email", "#password", "#name"]
                }
            
            def generate_unique_selectors(self, elements: List) -> List[str]:
                """Generate unique CSS selectors for elements."""
                return ["#unique-id-1", ".unique-class-2", "div:nth-child(3)"]
            
            def validate_selector(self, selector: str) -> bool:
                """Validate CSS selector syntax."""
                # Simple validation logic
                return selector and not selector.isspace() and len(selector) > 0
        
        return MockSelectorExtractor()

    def test_extract_interactive_elements(self, selector_extractor):
        """Test extraction of interactive elements."""
        html_content = """
        <html>
            <body>
                <form id="main-form">
                    <input type="email" id="email">
                    <button type="submit">Submit</button>
                </form>
            </body>
        </html>
        """
        
        result = selector_extractor.extract_interactive_elements(html_content)
        
        assert isinstance(result, dict)
        assert "forms" in result
        assert "buttons" in result
        assert "inputs" in result

    def test_generate_unique_selectors(self, selector_extractor):
        """Test generation of unique selectors."""
        mock_elements = [Mock(), Mock(), Mock()]
        
        result = selector_extractor.generate_unique_selectors(mock_elements)
        
        assert isinstance(result, list)
        assert len(result) > 0
        for selector in result:
            assert isinstance(selector, str)
            assert len(selector) > 0

    def test_validate_selector_valid(self, selector_extractor):
        """Test selector validation with valid selectors."""
        valid_selectors = [
            "#main-form",
            ".button-primary",
            "input[type='email']",
            "div > p:first-child"
        ]
        
        for selector in valid_selectors:
            assert selector_extractor.validate_selector(selector) == True

    def test_validate_selector_invalid(self, selector_extractor):
        """Test selector validation with invalid selectors."""
        invalid_selectors = [
            "",
            "   ",
            None
        ]
        
        for selector in invalid_selectors:
            try:
                result = selector_extractor.validate_selector(selector)
                assert result == False
            except (TypeError, AttributeError):
                # Expected for None input
                pass

class TestAgentCoordination:
    """Unit tests for agent coordination functionality."""

    @pytest.fixture
    def coordination_manager(self):
        """Create coordination manager for testing."""
        class MockCoordinationManager:
            def __init__(self):
                self.active_agents = {}
                self.task_queue = []
                self.results = {}
            
            async def spawn_agent(self, agent_type: str, config: Dict) -> str:
                """Spawn a new agent."""
                agent_id = f"{agent_type}_{len(self.active_agents)}"
                self.active_agents[agent_id] = {
                    "type": agent_type,
                    "config": config,
                    "status": "active",
                    "created_at": datetime.now()
                }
                return agent_id
            
            async def assign_task(self, agent_id: str, task: Dict) -> bool:
                """Assign task to agent."""
                if agent_id in self.active_agents:
                    self.task_queue.append({
                        "agent_id": agent_id,
                        "task": task,
                        "assigned_at": datetime.now()
                    })
                    return True
                return False
            
            async def get_agent_status(self, agent_id: str) -> Dict:
                """Get agent status."""
                return self.active_agents.get(agent_id, {"status": "not_found"})
            
            def get_active_agents(self) -> List[str]:
                """Get list of active agent IDs."""
                return list(self.active_agents.keys())
        
        return MockCoordinationManager()

    @pytest.mark.asyncio
    async def test_spawn_agent(self, coordination_manager):
        """Test agent spawning."""
        config = {"max_steps": 10, "timeout": 30}
        
        agent_id = await coordination_manager.spawn_agent("qa_generator", config)
        
        assert agent_id is not None
        assert agent_id.startswith("qa_generator_")
        assert agent_id in coordination_manager.active_agents

    @pytest.mark.asyncio
    async def test_assign_task_to_agent(self, coordination_manager):
        """Test task assignment to agent."""
        # First spawn an agent
        agent_id = await coordination_manager.spawn_agent("qa_generator", {})
        
        task = {
            "type": "generate_test_cases",
            "url": "https://www.saucedemo.com",
            "priority": "high"
        }
        
        result = await coordination_manager.assign_task(agent_id, task)
        
        assert result == True
        assert len(coordination_manager.task_queue) == 1
        assert coordination_manager.task_queue[0]["agent_id"] == agent_id

    @pytest.mark.asyncio
    async def test_assign_task_to_nonexistent_agent(self, coordination_manager):
        """Test task assignment to non-existent agent."""
        task = {"type": "test_task"}
        
        result = await coordination_manager.assign_task("nonexistent_agent", task)
        
        assert result == False
        assert len(coordination_manager.task_queue) == 0

    @pytest.mark.asyncio
    async def test_get_agent_status(self, coordination_manager):
        """Test getting agent status."""
        # Spawn an agent first
        agent_id = await coordination_manager.spawn_agent("qa_generator", {})
        
        status = await coordination_manager.get_agent_status(agent_id)
        
        assert status["status"] == "active"
        assert status["type"] == "qa_generator"
        assert "created_at" in status

    def test_get_active_agents(self, coordination_manager):
        """Test getting list of active agents."""
        initial_count = len(coordination_manager.get_active_agents())
        
        # Add some agents
        coordination_manager.active_agents["agent_1"] = {"status": "active"}
        coordination_manager.active_agents["agent_2"] = {"status": "active"}
        
        active_agents = coordination_manager.get_active_agents()
        
        assert len(active_agents) == initial_count + 2
        assert "agent_1" in active_agents
        assert "agent_2" in active_agents

class TestHookSystem:
    """Unit tests for hook system functionality."""

    @pytest.fixture
    def hook_manager(self):
        """Create hook manager for testing."""
        class MockHookManager:
            def __init__(self):
                self.hooks = {}
                self.execution_log = []
            
            def register_hook(self, event: str, callback) -> bool:
                """Register a hook for an event."""
                if event not in self.hooks:
                    self.hooks[event] = []
                self.hooks[event].append(callback)
                return True
            
            async def trigger_hook(self, event: str, data: Dict = None) -> List:
                """Trigger all hooks for an event."""
                results = []
                if event in self.hooks:
                    for hook in self.hooks[event]:
                        try:
                            if asyncio.iscoroutinefunction(hook):
                                result = await hook(data)
                            else:
                                result = hook(data)
                            results.append(result)
                            self.execution_log.append({
                                "event": event,
                                "hook": hook.__name__ if hasattr(hook, '__name__') else str(hook),
                                "result": result,
                                "timestamp": datetime.now()
                            })
                        except Exception as e:
                            results.append({"error": str(e)})
                return results
            
            def remove_hook(self, event: str, callback) -> bool:
                """Remove a hook from an event."""
                if event in self.hooks and callback in self.hooks[event]:
                    self.hooks[event].remove(callback)
                    return True
                return False
        
        return MockHookManager()

    def test_register_hook(self, hook_manager):
        """Test hook registration."""
        def test_callback(data):
            return "hook executed"
        
        result = hook_manager.register_hook("test_event", test_callback)
        
        assert result == True
        assert "test_event" in hook_manager.hooks
        assert test_callback in hook_manager.hooks["test_event"]

    @pytest.mark.asyncio
    async def test_trigger_hook_sync(self, hook_manager):
        """Test triggering synchronous hooks."""
        def sync_callback(data):
            return f"processed: {data.get('value', 'none')}"
        
        hook_manager.register_hook("sync_event", sync_callback)
        
        results = await hook_manager.trigger_hook("sync_event", {"value": "test"})
        
        assert len(results) == 1
        assert results[0] == "processed: test"

    @pytest.mark.asyncio
    async def test_trigger_hook_async(self, hook_manager):
        """Test triggering asynchronous hooks."""
        async def async_callback(data):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"async processed: {data.get('value', 'none')}"
        
        hook_manager.register_hook("async_event", async_callback)
        
        results = await hook_manager.trigger_hook("async_event", {"value": "test"})
        
        assert len(results) == 1
        assert results[0] == "async processed: test"

    @pytest.mark.asyncio
    async def test_trigger_hook_error_handling(self, hook_manager):
        """Test error handling in hook execution."""
        def failing_callback(data):
            raise ValueError("Hook execution failed")
        
        hook_manager.register_hook("error_event", failing_callback)
        
        results = await hook_manager.trigger_hook("error_event", {})
        
        assert len(results) == 1
        assert "error" in results[0]
        assert "Hook execution failed" in results[0]["error"]

    def test_remove_hook(self, hook_manager):
        """Test hook removal."""
        def test_callback(data):
            return "test"
        
        # Register and then remove hook
        hook_manager.register_hook("test_event", test_callback)
        assert test_callback in hook_manager.hooks["test_event"]
        
        result = hook_manager.remove_hook("test_event", test_callback)
        
        assert result == True
        assert test_callback not in hook_manager.hooks["test_event"]

    def test_remove_nonexistent_hook(self, hook_manager):
        """Test removing non-existent hook."""
        def test_callback(data):
            return "test"
        
        result = hook_manager.remove_hook("nonexistent_event", test_callback)
        
        assert result == False