"""
Performance tests for POC browser automation framework.

This module contains tests focused on performance metrics including:
- Execution timing
- Memory usage monitoring  
- Resource utilization
- Concurrency performance
- Load testing scenarios
"""

import pytest
import asyncio
import time
import psutil
import threading
from typing import Dict, Any, List, Callable
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import statistics

@dataclass
class PerformanceMetrics:
    """Container for performance measurement data."""
    start_time: float
    end_time: float
    duration: float
    memory_before: float
    memory_after: float
    memory_peak: float
    cpu_usage: List[float]
    operations_count: int
    throughput: float  # operations per second
    
    @property
    def memory_delta(self) -> float:
        """Memory usage delta in MB."""
        return self.memory_after - self.memory_before
    
    @property
    def avg_cpu_usage(self) -> float:
        """Average CPU usage percentage."""
        return statistics.mean(self.cpu_usage) if self.cpu_usage else 0.0

class PerformanceProfiler:
    """Performance profiling utility for tests."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.metrics_history = []
        self.monitoring_active = False
        self.cpu_samples = []
    
    async def start_monitoring(self, sample_interval: float = 0.1):
        """Start continuous performance monitoring."""
        self.monitoring_active = True
        self.cpu_samples = []
        
        async def monitor():
            while self.monitoring_active:
                try:
                    cpu_percent = self.process.cpu_percent()
                    self.cpu_samples.append(cpu_percent)
                    await asyncio.sleep(sample_interval)
                except Exception:
                    break
        
        asyncio.create_task(monitor())
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    async def profile_async_function(self, func: Callable, *args, **kwargs) -> PerformanceMetrics:
        """Profile an async function's performance."""
        # Start monitoring
        await self.start_monitoring()
        
        # Measure initial state
        start_time = time.time()
        memory_before = self.get_memory_usage()
        
        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Measure final state
            end_time = time.time()
            memory_after = self.get_memory_usage()
            
            # Stop monitoring
            self.stop_monitoring()
            
            # Calculate metrics
            duration = end_time - start_time
            operations_count = getattr(result, 'operations_count', 1) if hasattr(result, 'operations_count') else 1
            
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=max([memory_before, memory_after]),
                cpu_usage=self.cpu_samples.copy(),
                operations_count=operations_count,
                throughput=operations_count / duration if duration > 0 else 0
            )
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            self.stop_monitoring()
            raise e

# Mock classes for performance testing
class MockPerformantAgent:
    """Mock agent with configurable performance characteristics."""
    
    def __init__(self, processing_delay: float = 0.1, memory_usage_mb: float = 10):
        self.processing_delay = processing_delay
        self.memory_usage_mb = memory_usage_mb
        self.operations_count = 0
        self._memory_ballast = []
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task with simulated work."""
        # Simulate memory usage
        if self.memory_usage_mb > 0:
            # Allocate some memory to simulate usage
            chunk_size = int(self.memory_usage_mb * 1024 * 100)  # Rough approximation
            self._memory_ballast.append(b'x' * chunk_size)
        
        # Simulate processing time
        await asyncio.sleep(self.processing_delay)
        
        # Simulate some CPU work
        sum(range(1000))
        
        self.operations_count += 1
        
        return {
            "task_id": task.get("id", "unknown"),
            "status": "completed",
            "processing_time": self.processing_delay,
            "operations_count": self.operations_count
        }
    
    def cleanup(self):
        """Clean up allocated memory."""
        self._memory_ballast.clear()

class MockBrowserPage:
    """Mock browser page with performance simulation."""
    
    def __init__(self, load_time: float = 0.5):
        self.load_time = load_time
        self.url = "https://www.saucedemo.com"
        self.operations_log = []
    
    async def goto(self, url: str):
        """Navigate with simulated load time."""
        start = time.time()
        await asyncio.sleep(self.load_time)
        self.url = url
        load_duration = time.time() - start
        self.operations_log.append({"action": "goto", "url": url, "duration": load_duration})
    
    async def click(self, selector: str):
        """Click with minimal delay."""
        start = time.time()
        await asyncio.sleep(0.01)  # Very fast click
        duration = time.time() - start
        self.operations_log.append({"action": "click", "selector": selector, "duration": duration})
    
    async def fill(self, selector: str, value: str):
        """Fill input with typing simulation."""
        start = time.time()
        # Simulate typing speed (realistic delay)
        typing_delay = len(value) * 0.01  # 10ms per character
        await asyncio.sleep(typing_delay)
        duration = time.time() - start
        self.operations_log.append({"action": "fill", "selector": selector, "value": value, "duration": duration})

@pytest.mark.performance
class TestBasicPerformance:
    """Basic performance tests for individual components."""

    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()

    @pytest.fixture
    def fast_agent(self):
        """Fast mock agent for performance testing."""
        agent = MockPerformantAgent(processing_delay=0.01, memory_usage_mb=1)
        yield agent
        agent.cleanup()

    @pytest.fixture
    def slow_agent(self):
        """Slow mock agent for performance testing."""
        agent = MockPerformantAgent(processing_delay=0.5, memory_usage_mb=50)
        yield agent
        agent.cleanup()

    @pytest.mark.asyncio
    async def test_single_task_execution_time(self, profiler, fast_agent, performance_thresholds):
        """Test single task execution time."""
        task = {"id": "perf_task_001", "type": "simple"}
        
        metrics = await profiler.profile_async_function(
            fast_agent.process_task, task
        )
        
        # Should complete within performance threshold
        assert metrics.duration < performance_thresholds["response_time"]
        assert metrics.memory_delta < 100  # Less than 100MB increase

    @pytest.mark.asyncio
    async def test_memory_usage_per_task(self, profiler, fast_agent, performance_thresholds):
        """Test memory usage for task processing."""
        task = {"id": "memory_test", "type": "simple"}
        
        metrics = await profiler.profile_async_function(
            fast_agent.process_task, task
        )
        
        # Memory usage should be reasonable
        assert metrics.memory_after < performance_thresholds["memory_usage"]
        assert metrics.memory_delta < 50  # Less than 50MB per task

    @pytest.mark.asyncio
    async def test_cpu_usage_monitoring(self, profiler, fast_agent):
        """Test CPU usage during task execution."""
        task = {"id": "cpu_test", "type": "compute"}
        
        metrics = await profiler.profile_async_function(
            fast_agent.process_task, task
        )
        
        # Should have some CPU samples
        assert len(metrics.cpu_usage) > 0
        assert metrics.avg_cpu_usage >= 0  # CPU usage should be non-negative

    @pytest.mark.asyncio
    async def test_throughput_measurement(self, profiler, fast_agent):
        """Test throughput calculation."""
        tasks = [{"id": f"throughput_task_{i}", "type": "simple"} for i in range(5)]
        
        async def process_multiple_tasks():
            results = []
            for task in tasks:
                result = await fast_agent.process_task(task)
                results.append(result)
            # Mock operations count for throughput calculation
            class MockResult:
                operations_count = len(tasks)
            return MockResult()
        
        metrics = await profiler.profile_async_function(process_multiple_tasks)
        
        # Throughput should be reasonable
        assert metrics.throughput > 0
        assert metrics.operations_count == 5

@pytest.mark.performance
class TestConcurrencyPerformance:
    """Performance tests for concurrent operations."""

    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()

    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, profiler, performance_thresholds):
        """Test performance of concurrent task processing."""
        # Create multiple agents
        agents = [MockPerformantAgent(processing_delay=0.1) for _ in range(5)]
        tasks = [{"id": f"concurrent_task_{i}", "type": "simple"} for i in range(5)]
        
        async def process_concurrent_tasks():
            # Process tasks concurrently
            coroutines = [
                agent.process_task(task) 
                for agent, task in zip(agents, tasks)
            ]
            results = await asyncio.gather(*coroutines)
            
            class MockResult:
                operations_count = len(results)
            return MockResult()
        
        # Measure concurrent execution
        metrics = await profiler.profile_async_function(process_concurrent_tasks)
        
        # Concurrent execution should be faster than sequential
        # 5 tasks at 0.1s each should take ~0.1s concurrently, not 0.5s
        assert metrics.duration < 0.3  # Allow some overhead
        assert metrics.operations_count == 5
        
        # Cleanup
        for agent in agents:
            agent.cleanup()

    @pytest.mark.asyncio
    async def test_high_concurrency_limits(self, profiler):
        """Test system limits under high concurrency."""
        # Create many concurrent tasks
        num_tasks = 50
        agents = [MockPerformantAgent(processing_delay=0.01, memory_usage_mb=2) for _ in range(num_tasks)]
        tasks = [{"id": f"stress_task_{i}", "type": "simple"} for i in range(num_tasks)]
        
        async def high_concurrency_test():
            # Process many tasks concurrently
            semaphore = asyncio.Semaphore(20)  # Limit concurrent operations
            
            async def limited_process(agent, task):
                async with semaphore:
                    return await agent.process_task(task)
            
            coroutines = [
                limited_process(agent, task)
                for agent, task in zip(agents, tasks)
            ]
            results = await asyncio.gather(*coroutines)
            
            class MockResult:
                operations_count = len(results)
            return MockResult()
        
        metrics = await profiler.profile_async_function(high_concurrency_test)
        
        # Should handle high concurrency reasonably
        assert metrics.operations_count == num_tasks
        assert metrics.duration < 5.0  # Should complete within 5 seconds
        
        # Cleanup
        for agent in agents:
            agent.cleanup()

    @pytest.mark.asyncio
    async def test_thread_pool_performance(self, profiler):
        """Test performance with thread pool execution."""
        def cpu_intensive_task(task_id: int) -> Dict[str, Any]:
            """CPU-intensive task for thread pool testing."""
            # Simulate CPU work
            result = sum(i * i for i in range(10000))
            return {"task_id": task_id, "result": result}
        
        async def thread_pool_test():
            num_tasks = 10
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, cpu_intensive_task, i)
                    for i in range(num_tasks)
                ]
                results = await asyncio.gather(*tasks)
            
            class MockResult:
                operations_count = len(results)
            return MockResult()
        
        metrics = await profiler.profile_async_function(thread_pool_test)
        
        # Thread pool should handle CPU tasks efficiently
        assert metrics.operations_count == 10
        assert metrics.duration < 2.0  # Should be reasonably fast

@pytest.mark.performance
class TestBrowserPerformance:
    """Performance tests for browser operations."""

    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()

    @pytest.fixture
    def fast_page(self):
        """Fast-loading mock page."""
        return MockBrowserPage(load_time=0.1)

    @pytest.fixture
    def slow_page(self):
        """Slow-loading mock page."""
        return MockBrowserPage(load_time=2.0)

    @pytest.mark.asyncio
    async def test_page_load_performance(self, profiler, fast_page, performance_thresholds):
        """Test page loading performance."""
        metrics = await profiler.profile_async_function(
            fast_page.goto, "https://www.saucedemo.com/fast"
        )
        
        assert metrics.duration < performance_thresholds["page_load_time"]

    @pytest.mark.asyncio
    async def test_element_interaction_speed(self, profiler, fast_page, performance_thresholds):
        """Test speed of element interactions."""
        async def multiple_interactions():
            await fast_page.click("#button1")
            await fast_page.fill("#input1", "test value")
            await fast_page.click("#button2")
            await fast_page.fill("#input2", "another value")
            
            class MockResult:
                operations_count = 4
            return MockResult()
        
        metrics = await profiler.profile_async_function(multiple_interactions)
        
        # Multiple interactions should be fast
        assert metrics.duration < 1.0
        assert metrics.operations_count == 4

    @pytest.mark.asyncio
    async def test_form_filling_performance(self, profiler, fast_page):
        """Test performance of form filling operations."""
        form_data = {
            "#name": "John Doe",
            "#email": "john@example.com", 
            "#address": "123 Main St, Anytown, USA",
            "#phone": "+1-555-123-4567",
            "#comments": "This is a long comment field with lots of text to simulate realistic form data entry."
        }
        
        async def fill_form():
            for selector, value in form_data.items():
                await fast_page.fill(selector, value)
            
            class MockResult:
                operations_count = len(form_data)
            return MockResult()
        
        metrics = await profiler.profile_async_function(fill_form)
        
        # Form filling should scale with content length
        assert metrics.operations_count == len(form_data)
        # Typing simulation should take reasonable time
        expected_min_time = sum(len(value) * 0.01 for value in form_data.values())
        assert metrics.duration >= expected_min_time * 0.8  # Allow some variance

@pytest.mark.performance
@pytest.mark.slow
class TestLoadTesting:
    """Load testing scenarios."""

    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()

    @pytest.mark.asyncio
    async def test_sustained_load(self, profiler):
        """Test performance under sustained load."""
        duration_seconds = 10
        operations_per_second = 5
        
        async def sustained_load_test():
            start_time = time.time()
            operations_count = 0
            
            while time.time() - start_time < duration_seconds:
                batch_start = time.time()
                
                # Create batch of operations
                agents = [MockPerformantAgent(processing_delay=0.05) for _ in range(operations_per_second)]
                tasks = [{"id": f"load_task_{operations_count + i}"} for i in range(operations_per_second)]
                
                # Execute batch
                coroutines = [agent.process_task(task) for agent, task in zip(agents, tasks)]
                await asyncio.gather(*coroutines)
                
                operations_count += operations_per_second
                
                # Cleanup batch
                for agent in agents:
                    agent.cleanup()
                
                # Wait for next second
                batch_duration = time.time() - batch_start
                if batch_duration < 1.0:
                    await asyncio.sleep(1.0 - batch_duration)
            
            class MockResult:
                operations_count = operations_count
            return MockResult()
        
        metrics = await profiler.profile_async_function(sustained_load_test)
        
        # Should maintain consistent performance
        expected_operations = duration_seconds * operations_per_second
        assert metrics.operations_count >= expected_operations * 0.9  # Allow 10% variance
        assert metrics.duration <= duration_seconds + 2  # Allow some overhead

    @pytest.mark.asyncio
    async def test_burst_load_handling(self, profiler):
        """Test handling of burst loads."""
        burst_size = 100
        
        async def burst_test():
            # Create burst of operations
            agents = [MockPerformantAgent(processing_delay=0.02) for _ in range(burst_size)]
            tasks = [{"id": f"burst_task_{i}"} for i in range(burst_size)]
            
            # Execute all at once
            coroutines = [agent.process_task(task) for agent, task in zip(agents, tasks)]
            results = await asyncio.gather(*coroutines)
            
            # Cleanup
            for agent in agents:
                agent.cleanup()
            
            class MockResult:
                operations_count = len(results)
            return MockResult()
        
        metrics = await profiler.profile_async_function(burst_test)
        
        # Should handle burst efficiently
        assert metrics.operations_count == burst_size
        assert metrics.duration < 5.0  # Should complete quickly even with burst

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, profiler, performance_thresholds):
        """Test behavior under memory pressure."""
        # Create memory-intensive operations
        memory_per_task = 20  # MB
        num_tasks = 10
        
        async def memory_pressure_test():
            agents = [MockPerformantAgent(processing_delay=0.1, memory_usage_mb=memory_per_task) for _ in range(num_tasks)]
            tasks = [{"id": f"memory_task_{i}"} for i in range(num_tasks)]
            
            # Process with limited concurrency to avoid overwhelming system
            semaphore = asyncio.Semaphore(5)
            
            async def limited_process(agent, task):
                async with semaphore:
                    result = await agent.process_task(task)
                    # Cleanup immediately after processing
                    agent.cleanup()
                    return result
            
            coroutines = [limited_process(agent, task) for agent, task in zip(agents, tasks)]
            results = await asyncio.gather(*coroutines)
            
            class MockResult:
                operations_count = len(results)
            return MockResult()
        
        metrics = await profiler.profile_async_function(memory_pressure_test)
        
        # Should handle memory pressure without excessive growth
        assert metrics.operations_count == num_tasks
        # Memory growth should be bounded
        assert metrics.memory_delta < performance_thresholds["memory_usage"]

@pytest.mark.performance 
class TestPerformanceRegression:
    """Performance regression tests."""

    @pytest.fixture
    def profiler(self):
        """Performance profiler fixture."""
        return PerformanceProfiler()

    @pytest.fixture
    def baseline_metrics(self):
        """Baseline performance metrics for regression testing."""
        return {
            "single_task_duration": 0.1,
            "concurrent_tasks_duration": 0.5,
            "memory_per_task": 10.0,
            "throughput_ops_per_sec": 20.0
        }

    @pytest.mark.asyncio
    async def test_single_task_regression(self, profiler, baseline_metrics):
        """Test for performance regression in single task execution."""
        agent = MockPerformantAgent(processing_delay=0.05)
        task = {"id": "regression_test", "type": "baseline"}
        
        metrics = await profiler.profile_async_function(agent.process_task, task)
        
        # Should not be significantly slower than baseline
        baseline_duration = baseline_metrics["single_task_duration"]
        assert metrics.duration <= baseline_duration * 1.2  # Allow 20% degradation
        
        agent.cleanup()

    @pytest.mark.asyncio
    async def test_throughput_regression(self, profiler, baseline_metrics):
        """Test for throughput regression."""
        num_tasks = 10
        agents = [MockPerformantAgent(processing_delay=0.05) for _ in range(num_tasks)]
        tasks = [{"id": f"throughput_test_{i}"} for i in range(num_tasks)]
        
        async def throughput_test():
            coroutines = [agent.process_task(task) for agent, task in zip(agents, tasks)]
            results = await asyncio.gather(*coroutines)
            
            class MockResult:
                operations_count = len(results)
            return MockResult()
        
        metrics = await profiler.profile_async_function(throughput_test)
        
        # Throughput should not degrade significantly
        baseline_throughput = baseline_metrics["throughput_ops_per_sec"]
        assert metrics.throughput >= baseline_throughput * 0.8  # Allow 20% degradation
        
        # Cleanup
        for agent in agents:
            agent.cleanup()

    @pytest.mark.asyncio
    async def test_memory_usage_regression(self, profiler, baseline_metrics):
        """Test for memory usage regression."""
        agent = MockPerformantAgent(processing_delay=0.05, memory_usage_mb=5)
        task = {"id": "memory_regression_test"}
        
        metrics = await profiler.profile_async_function(agent.process_task, task)
        
        # Memory usage should not increase significantly
        baseline_memory = baseline_metrics["memory_per_task"]
        assert metrics.memory_delta <= baseline_memory * 1.5  # Allow 50% increase
        
        agent.cleanup()

class TestPerformanceUtilities:
    """Test performance testing utilities themselves."""
    
    def test_performance_metrics_creation(self):
        """Test PerformanceMetrics dataclass."""
        metrics = PerformanceMetrics(
            start_time=1000.0,
            end_time=1001.0,
            duration=1.0,
            memory_before=100.0,
            memory_after=110.0,
            memory_peak=115.0,
            cpu_usage=[10.0, 15.0, 20.0],
            operations_count=5,
            throughput=5.0
        )
        
        assert metrics.memory_delta == 10.0
        assert metrics.avg_cpu_usage == 15.0
    
    def test_performance_profiler_initialization(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()
        
        assert profiler.process is not None
        assert profiler.metrics_history == []
        assert not profiler.monitoring_active
    
    def test_mock_agent_performance_characteristics(self):
        """Test mock agent performance configuration."""
        fast_agent = MockPerformantAgent(processing_delay=0.01, memory_usage_mb=1)
        slow_agent = MockPerformantAgent(processing_delay=1.0, memory_usage_mb=100)
        
        assert fast_agent.processing_delay == 0.01
        assert slow_agent.processing_delay == 1.0
        assert fast_agent.memory_usage_mb == 1
        assert slow_agent.memory_usage_mb == 100
        
        # Cleanup
        fast_agent.cleanup()
        slow_agent.cleanup()