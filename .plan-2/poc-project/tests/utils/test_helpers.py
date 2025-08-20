"""
Test helper utilities for POC testing framework.

This module provides utility functions and classes to support
testing operations including mocking, data generation, assertions,
and test orchestration.
"""

import asyncio
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MockBrowserFactory:
    """Factory for creating mock browser components."""
    
    @staticmethod
    def create_mock_page(url: str = "https://www.saucedemo.com", **kwargs) -> Mock:
        """Create a mock browser page with standard methods."""
        page = Mock()
        
        # Basic properties
        page.url = url
        page.title = AsyncMock(return_value=kwargs.get('title', 'Test Page'))
        page.content = AsyncMock(return_value=kwargs.get('content', '<html><body>Test</body></html>'))
        page.is_closed = Mock(return_value=False)
        
        # Navigation methods
        page.goto = AsyncMock()
        page.reload = AsyncMock()
        page.go_back = AsyncMock()
        page.go_forward = AsyncMock()
        
        # Element interaction methods
        page.click = AsyncMock()
        page.fill = AsyncMock()
        page.select_option = AsyncMock()
        page.check = AsyncMock()
        page.uncheck = AsyncMock()
        page.hover = AsyncMock()
        page.focus = AsyncMock()
        page.blur = AsyncMock()
        
        # Element query methods
        page.query_selector = AsyncMock(return_value=Mock())
        page.query_selector_all = AsyncMock(return_value=[])
        page.wait_for_selector = AsyncMock(return_value=True)
        page.wait_for_load_state = AsyncMock()
        
        # JavaScript execution
        page.evaluate = AsyncMock(return_value="mock_result")
        page.add_script_tag = AsyncMock()
        
        # Screenshots and PDFs
        page.screenshot = AsyncMock(return_value=b'fake_screenshot')
        page.pdf = AsyncMock(return_value=b'fake_pdf')
        
        # Event handling
        page.on = Mock()
        page.off = Mock()
        page.once = Mock()
        
        # Cleanup
        page.close = AsyncMock()
        
        return page
    
    @staticmethod
    def create_mock_browser() -> Mock:
        """Create a mock browser with standard methods."""
        browser = Mock()
        
        browser.new_page = AsyncMock(return_value=MockBrowserFactory.create_mock_page())
        browser.new_context = AsyncMock()
        browser.contexts = []
        browser.version = "mock-browser-1.0"
        browser.is_connected = Mock(return_value=True)
        browser.close = AsyncMock()
        
        return browser
    
    @staticmethod
    def create_mock_context() -> Mock:
        """Create a mock browser context."""
        context = Mock()
        
        context.new_page = AsyncMock(return_value=MockBrowserFactory.create_mock_page())
        context.pages = []
        context.cookies = AsyncMock(return_value=[])
        context.add_cookies = AsyncMock()
        context.clear_cookies = AsyncMock()
        context.set_extra_http_headers = AsyncMock()
        context.close = AsyncMock()
        
        return context

class TestDataManager:
    """Manager for test data lifecycle."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp())
        self.created_files = []
        self.created_dirs = []
    
    def create_temp_file(self, content: str, suffix: str = ".txt") -> Path:
        """Create a temporary file with content."""
        temp_file = self.temp_dir / f"test_file_{len(self.created_files)}{suffix}"
        temp_file.write_text(content)
        self.created_files.append(temp_file)
        return temp_file
    
    def create_temp_json(self, data: Dict[str, Any]) -> Path:
        """Create a temporary JSON file."""
        content = json.dumps(data, indent=2)
        return self.create_temp_file(content, ".json")
    
    def create_temp_dir(self, name: str = None) -> Path:
        """Create a temporary directory."""
        dir_name = name or f"test_dir_{len(self.created_dirs)}"
        temp_dir = self.temp_dir / dir_name
        temp_dir.mkdir(parents=True, exist_ok=True)
        self.created_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all created temporary files and directories."""
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove file {file_path}: {e}")
        
        for dir_path in self.created_dirs:
            try:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
            except Exception as e:
                logger.warning(f"Failed to remove directory {dir_path}: {e}")
        
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to remove temp directory {self.temp_dir}: {e}")

class AsyncTestUtils:
    """Utilities for async testing."""
    
    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], bool],
        timeout: float = 5.0,
        check_interval: float = 0.1,
        error_message: str = "Condition not met within timeout"
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if await condition() if asyncio.iscoroutinefunction(condition) else condition():
                    return True
            except Exception:
                pass  # Ignore exceptions during condition checking
            
            await asyncio.sleep(check_interval)
        
        raise TimeoutError(error_message)
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float = 30.0):
        """Run a coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout} seconds")
    
    @staticmethod
    async def gather_with_results(tasks: List[asyncio.Task]) -> List[Dict[str, Any]]:
        """Gather tasks and return results with metadata."""
        results = []
        
        for i, task in enumerate(tasks):
            try:
                start_time = time.time()
                result = await task
                duration = time.time() - start_time
                
                results.append({
                    "index": i,
                    "success": True,
                    "result": result,
                    "duration": duration,
                    "error": None
                })
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    "index": i,
                    "success": False,
                    "result": None,
                    "duration": duration,
                    "error": str(e)
                })
        
        return results

class PerformanceTestUtils:
    """Utilities for performance testing."""
    
    @staticmethod
    def measure_execution_time(func: Callable) -> Callable:
        """Decorator to measure function execution time."""
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if hasattr(result, '__dict__'):
                result.execution_time = execution_time
            
            return result
        
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if hasattr(result, '__dict__'):
                result.execution_time = execution_time
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    @staticmethod
    def create_performance_monitor():
        """Create a performance monitoring context manager."""
        class PerformanceMonitor:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.memory_before = None
                self.memory_after = None
                self.metrics = {}
            
            def __enter__(self):
                self.start_time = time.time()
                try:
                    import psutil
                    process = psutil.Process()
                    self.memory_before = process.memory_info().rss / 1024 / 1024  # MB
                except ImportError:
                    self.memory_before = 0
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.end_time = time.time()
                try:
                    import psutil
                    process = psutil.Process()
                    self.memory_after = process.memory_info().rss / 1024 / 1024  # MB
                except ImportError:
                    self.memory_after = 0
                
                self.metrics = {
                    "duration": self.end_time - self.start_time,
                    "memory_delta": self.memory_after - self.memory_before,
                    "memory_before": self.memory_before,
                    "memory_after": self.memory_after
                }
        
        return PerformanceMonitor()

class TestAssertions:
    """Enhanced assertion methods for testing."""
    
    @staticmethod
    def assert_dict_contains(actual: Dict[str, Any], expected: Dict[str, Any], message: str = ""):
        """Assert that actual dict contains all key-value pairs from expected dict."""
        missing_keys = set(expected.keys()) - set(actual.keys())
        if missing_keys:
            raise AssertionError(f"{message} Missing keys: {missing_keys}")
        
        for key, expected_value in expected.items():
            actual_value = actual[key]
            if actual_value != expected_value:
                raise AssertionError(
                    f"{message} Key '{key}': expected {expected_value}, got {actual_value}"
                )
    
    @staticmethod
    def assert_list_contains_items(actual: List[Any], expected_items: List[Any], message: str = ""):
        """Assert that list contains all expected items."""
        missing_items = [item for item in expected_items if item not in actual]
        if missing_items:
            raise AssertionError(f"{message} Missing items: {missing_items}")
    
    @staticmethod
    def assert_performance_within_threshold(
        actual_time: float,
        threshold: float,
        metric_name: str = "operation"
    ):
        """Assert that performance metric is within threshold."""
        if actual_time > threshold:
            raise AssertionError(
                f"{metric_name} took {actual_time:.3f}s, exceeding threshold of {threshold:.3f}s"
            )
    
    @staticmethod
    def assert_url_matches_pattern(actual_url: str, pattern: str, message: str = ""):
        """Assert that URL matches expected pattern."""
        import re
        if not re.match(pattern, actual_url):
            raise AssertionError(f"{message} URL '{actual_url}' does not match pattern '{pattern}'")
    
    @staticmethod
    def assert_element_exists(page_content: str, selector: str, message: str = ""):
        """Assert that element with selector exists in page content."""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(page_content, 'html.parser')
            element = soup.select_one(selector)
            if not element:
                raise AssertionError(f"{message} Element with selector '{selector}' not found")
        except ImportError:
            # Fallback to simple string check if BeautifulSoup not available
            if selector not in page_content:
                raise AssertionError(f"{message} Selector '{selector}' not found in content")

class TestReporter:
    """Utility for generating test reports."""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
    
    def add_test_result(
        self,
        test_name: str,
        status: str,
        duration: float,
        error_message: str = None,
        details: Dict[str, Any] = None
    ):
        """Add a test result to the report."""
        self.test_results.append({
            "test_name": test_name,
            "status": status,
            "duration": duration,
            "error_message": error_message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate test summary report."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "passed"])
        failed_tests = len([r for r in self.test_results if r["status"] == "failed"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "skipped"])
        
        total_duration = sum(r["duration"] for r in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            },
            "results": self.test_results
        }
    
    def export_to_file(self, file_path: Path, format: str = "json"):
        """Export report to file."""
        summary = self.generate_summary()
        
        if format.lower() == "json":
            with open(file_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
        elif format.lower() == "html":
            html_content = self._generate_html_report(summary)
            with open(file_path, 'w') as f:
                f.write(html_content)
    
    def _generate_html_report(self, summary: Dict[str, Any]) -> str:
        """Generate HTML report content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .skipped {{ color: orange; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Test Execution Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {summary['summary']['total_tests']}</p>
                <p class="passed">Passed: {summary['summary']['passed']}</p>
                <p class="failed">Failed: {summary['summary']['failed']}</p>
                <p class="skipped">Skipped: {summary['summary']['skipped']}</p>
                <p>Success Rate: {summary['summary']['success_rate']:.1f}%</p>
                <p>Total Duration: {summary['summary']['total_duration']:.2f}s</p>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Error Message</th>
                </tr>
        """
        
        for result in summary['results']:
            status_class = result['status']
            error_msg = result['error_message'] or ''
            html += f"""
                <tr>
                    <td>{result['test_name']}</td>
                    <td class="{status_class}">{result['status'].upper()}</td>
                    <td>{result['duration']:.3f}</td>
                    <td>{error_msg}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html

class ErrorSimulator:
    """Utility for simulating various error conditions."""
    
    @staticmethod
    def create_timeout_error(message: str = "Operation timed out"):
        """Create a timeout error."""
        return TimeoutError(message)
    
    @staticmethod
    def create_network_error(message: str = "Network connection failed"):
        """Create a network error."""
        return ConnectionError(message)
    
    @staticmethod
    def create_element_not_found_error(selector: str):
        """Create an element not found error."""
        return ValueError(f"Element with selector '{selector}' not found")
    
    @staticmethod
    async def simulate_slow_operation(duration: float = 1.0, result: Any = None):
        """Simulate a slow async operation."""
        await asyncio.sleep(duration)
        return result
    
    @staticmethod
    def create_failing_mock(error_type: type = Exception, error_message: str = "Mock error"):
        """Create a mock that always raises an error."""
        mock = Mock()
        mock.side_effect = error_type(error_message)
        return mock
    
    @staticmethod
    def create_intermittent_mock(success_calls: int = 2, failure_calls: int = 1, error_type: type = Exception):
        """Create a mock that succeeds some times and fails others."""
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            cycle_length = success_calls + failure_calls
            position_in_cycle = call_count % cycle_length
            
            if position_in_cycle <= success_calls:
                return "success"
            else:
                raise error_type("Intermittent failure")
        
        mock = Mock()
        mock.side_effect = side_effect
        return mock

# Convenience functions for quick access
def create_mock_page(**kwargs) -> Mock:
    """Quick function to create a mock page."""
    return MockBrowserFactory.create_mock_page(**kwargs)

def create_temp_data_manager() -> TestDataManager:
    """Quick function to create a test data manager."""
    return TestDataManager()

def measure_performance(func: Callable) -> Callable:
    """Quick function to add performance measurement."""
    return PerformanceTestUtils.measure_execution_time(func)

def wait_for(condition: Callable, timeout: float = 5.0) -> Callable:
    """Quick function to wait for a condition."""
    return AsyncTestUtils.wait_for_condition(condition, timeout)