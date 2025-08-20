"""
Unit tests for test data models and validation.

This module tests the data models used for representing test cases,
test steps, test results, and related validation logic.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

# Mock data models that would typically be imported
class TestPriority(Enum):
    """Test priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TestType(Enum):
    """Test types."""
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    INTEGRATION = "integration"
    REGRESSION = "regression"

class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestStep:
    """Represents a single test step."""
    id: str
    description: str
    action: str
    selector: Optional[str] = None
    expected_result: Optional[str] = None
    timeout: int = 30
    screenshot: bool = False
    data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate test step after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Test step ID cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Test step description cannot be empty")
        if not self.action or not self.action.strip():
            raise ValueError("Test step action cannot be empty")

@dataclass
class TestCase:
    """Represents a complete test case."""
    id: str
    title: str
    description: str
    steps: List[TestStep]
    expected_result: str
    priority: TestPriority = TestPriority.MEDIUM
    test_type: TestType = TestType.FUNCTIONAL
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    estimated_duration: int = 60  # seconds
    prerequisites: List[str] = field(default_factory=list)
    cleanup_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate test case after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Test case ID cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("Test case title cannot be empty")
        if not self.steps:
            raise ValueError("Test case must have at least one step")
        if not self.expected_result or not self.expected_result.strip():
            raise ValueError("Test case expected result cannot be empty")
    
    def add_step(self, step: TestStep) -> None:
        """Add a step to the test case."""
        self.steps.append(step)
        self.updated_at = datetime.now()
    
    def get_total_estimated_duration(self) -> int:
        """Calculate total estimated duration including steps."""
        step_duration = sum(step.timeout for step in self.steps)
        return max(self.estimated_duration, step_duration)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test case to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "steps": [
                {
                    "id": step.id,
                    "description": step.description,
                    "action": step.action,
                    "selector": step.selector,
                    "expected_result": step.expected_result,
                    "timeout": step.timeout,
                    "screenshot": step.screenshot,
                    "data": step.data
                }
                for step in self.steps
            ],
            "expected_result": self.expected_result,
            "priority": self.priority.value,
            "test_type": self.test_type.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "estimated_duration": self.estimated_duration,
            "prerequisites": self.prerequisites,
            "cleanup_steps": self.cleanup_steps,
            "metadata": self.metadata
        }

@dataclass
class TestResult:
    """Represents test execution results."""
    test_case_id: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_completed(self, status: TestStatus, error_message: Optional[str] = None):
        """Mark test as completed with given status."""
        self.status = status
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        if error_message:
            self.error_message = error_message
    
    def add_step_result(self, step_id: str, status: TestStatus, details: Dict[str, Any] = None):
        """Add result for a specific step."""
        self.step_results.append({
            "step_id": step_id,
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })

class TestTestStep:
    """Unit tests for TestStep model."""
    
    def test_valid_test_step_creation(self):
        """Test creating a valid test step."""
        step = TestStep(
            id="step_001",
            description="Click the login button",
            action="click",
            selector="#login-btn",
            expected_result="User is redirected to dashboard"
        )
        
        assert step.id == "step_001"
        assert step.description == "Click the login button"
        assert step.action == "click"
        assert step.selector == "#login-btn"
        assert step.expected_result == "User is redirected to dashboard"
        assert step.timeout == 30  # default value
        assert step.screenshot == False  # default value
    
    def test_test_step_empty_id_raises_error(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Test step ID cannot be empty"):
            TestStep(
                id="",
                description="Test description",
                action="click"
            )
    
    def test_test_step_empty_description_raises_error(self):
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="Test step description cannot be empty"):
            TestStep(
                id="step_001",
                description="",
                action="click"
            )
    
    def test_test_step_empty_action_raises_error(self):
        """Test that empty action raises ValueError."""
        with pytest.raises(ValueError, match="Test step action cannot be empty"):
            TestStep(
                id="step_001",
                description="Test description",
                action=""
            )
    
    def test_test_step_with_data(self):
        """Test test step with additional data."""
        data = {"input_value": "test@example.com", "wait_time": 2}
        step = TestStep(
            id="step_001",
            description="Fill email field",
            action="fill",
            selector="#email",
            data=data
        )
        
        assert step.data == data
        assert step.data["input_value"] == "test@example.com"

class TestTestCase:
    """Unit tests for TestCase model."""
    
    @pytest.fixture
    def sample_steps(self):
        """Create sample test steps."""
        return [
            TestStep(
                id="step_001",
                description="Navigate to login page",
                action="navigate",
                expected_result="Login page is displayed"
            ),
            TestStep(
                id="step_002", 
                description="Enter email",
                action="fill",
                selector="#email",
                expected_result="Email is entered"
            ),
            TestStep(
                id="step_003",
                description="Click login button",
                action="click",
                selector="#login-btn",
                expected_result="User is logged in"
            )
        ]
    
    def test_valid_test_case_creation(self, sample_steps):
        """Test creating a valid test case."""
        test_case = TestCase(
            id="tc_001",
            title="User Login Test",
            description="Test user login functionality",
            steps=sample_steps,
            expected_result="User successfully logs in and sees dashboard",
            priority=TestPriority.HIGH,
            test_type=TestType.FUNCTIONAL
        )
        
        assert test_case.id == "tc_001"
        assert test_case.title == "User Login Test"
        assert len(test_case.steps) == 3
        assert test_case.priority == TestPriority.HIGH
        assert test_case.test_type == TestType.FUNCTIONAL
        assert isinstance(test_case.created_at, datetime)
    
    def test_test_case_empty_id_raises_error(self, sample_steps):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Test case ID cannot be empty"):
            TestCase(
                id="",
                title="Test Title",
                description="Test description",
                steps=sample_steps,
                expected_result="Expected result"
            )
    
    def test_test_case_empty_title_raises_error(self, sample_steps):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="Test case title cannot be empty"):
            TestCase(
                id="tc_001",
                title="",
                description="Test description", 
                steps=sample_steps,
                expected_result="Expected result"
            )
    
    def test_test_case_no_steps_raises_error(self):
        """Test that test case with no steps raises ValueError."""
        with pytest.raises(ValueError, match="Test case must have at least one step"):
            TestCase(
                id="tc_001",
                title="Test Title",
                description="Test description",
                steps=[],
                expected_result="Expected result"
            )
    
    def test_test_case_empty_expected_result_raises_error(self, sample_steps):
        """Test that empty expected result raises ValueError."""
        with pytest.raises(ValueError, match="Test case expected result cannot be empty"):
            TestCase(
                id="tc_001",
                title="Test Title",
                description="Test description",
                steps=sample_steps,
                expected_result=""
            )
    
    def test_add_step_to_test_case(self, sample_steps):
        """Test adding a step to existing test case."""
        test_case = TestCase(
            id="tc_001",
            title="Test Title",
            description="Test description",
            steps=sample_steps[:2],  # Start with 2 steps
            expected_result="Expected result"
        )
        
        initial_count = len(test_case.steps)
        initial_updated_at = test_case.updated_at
        
        new_step = TestStep(
            id="step_004",
            description="Verify dashboard",
            action="verify",
            expected_result="Dashboard is visible"
        )
        
        test_case.add_step(new_step)
        
        assert len(test_case.steps) == initial_count + 1
        assert test_case.steps[-1] == new_step
        assert test_case.updated_at > initial_updated_at
    
    def test_get_total_estimated_duration(self, sample_steps):
        """Test calculation of total estimated duration."""
        # Set specific timeouts for steps
        sample_steps[0].timeout = 10
        sample_steps[1].timeout = 15
        sample_steps[2].timeout = 20
        
        test_case = TestCase(
            id="tc_001",
            title="Test Title",
            description="Test description",
            steps=sample_steps,
            expected_result="Expected result",
            estimated_duration=30
        )
        
        total_duration = test_case.get_total_estimated_duration()
        expected_step_duration = 10 + 15 + 20  # 45 seconds
        
        assert total_duration == expected_step_duration  # Should use step duration as it's higher
    
    def test_test_case_to_dict(self, sample_steps):
        """Test converting test case to dictionary."""
        test_case = TestCase(
            id="tc_001",
            title="Test Title",
            description="Test description",
            steps=sample_steps,
            expected_result="Expected result",
            priority=TestPriority.HIGH,
            test_type=TestType.FUNCTIONAL,
            tags=["login", "authentication"]
        )
        
        result_dict = test_case.to_dict()
        
        assert result_dict["id"] == "tc_001"
        assert result_dict["title"] == "Test Title"
        assert result_dict["priority"] == "high"
        assert result_dict["test_type"] == "functional"
        assert result_dict["tags"] == ["login", "authentication"]
        assert len(result_dict["steps"]) == 3
        assert "created_at" in result_dict
        assert "updated_at" in result_dict
    
    def test_test_case_with_prerequisites(self, sample_steps):
        """Test test case with prerequisites."""
        prerequisites = ["User account exists", "Browser is open"]
        
        test_case = TestCase(
            id="tc_001",
            title="Test Title",
            description="Test description",
            steps=sample_steps,
            expected_result="Expected result",
            prerequisites=prerequisites
        )
        
        assert test_case.prerequisites == prerequisites
    
    def test_test_case_with_cleanup_steps(self, sample_steps):
        """Test test case with cleanup steps."""
        cleanup_steps = ["Logout user", "Clear browser cache"]
        
        test_case = TestCase(
            id="tc_001",
            title="Test Title",
            description="Test description",
            steps=sample_steps,
            expected_result="Expected result",
            cleanup_steps=cleanup_steps
        )
        
        assert test_case.cleanup_steps == cleanup_steps

class TestTestResult:
    """Unit tests for TestResult model."""
    
    def test_test_result_creation(self):
        """Test creating a test result."""
        start_time = datetime.now()
        
        result = TestResult(
            test_case_id="tc_001",
            status=TestStatus.RUNNING,
            start_time=start_time
        )
        
        assert result.test_case_id == "tc_001"
        assert result.status == TestStatus.RUNNING
        assert result.start_time == start_time
        assert result.end_time is None
        assert result.duration is None
    
    def test_mark_test_completed_success(self):
        """Test marking test as completed successfully."""
        start_time = datetime.now() - timedelta(seconds=30)
        
        result = TestResult(
            test_case_id="tc_001",
            status=TestStatus.RUNNING,
            start_time=start_time
        )
        
        result.mark_completed(TestStatus.PASSED)
        
        assert result.status == TestStatus.PASSED
        assert result.end_time is not None
        assert result.duration is not None
        assert result.duration > 0
        assert result.error_message is None
    
    def test_mark_test_completed_with_error(self):
        """Test marking test as completed with error."""
        start_time = datetime.now() - timedelta(seconds=15)
        error_message = "Element not found: #submit-btn"
        
        result = TestResult(
            test_case_id="tc_001",
            status=TestStatus.RUNNING,
            start_time=start_time
        )
        
        result.mark_completed(TestStatus.FAILED, error_message)
        
        assert result.status == TestStatus.FAILED
        assert result.error_message == error_message
        assert result.duration is not None
    
    def test_add_step_result(self):
        """Test adding step results."""
        result = TestResult(
            test_case_id="tc_001",
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        step_details = {"selector_used": "#email", "value_entered": "test@example.com"}
        result.add_step_result("step_001", TestStatus.PASSED, step_details)
        
        assert len(result.step_results) == 1
        step_result = result.step_results[0]
        assert step_result["step_id"] == "step_001"
        assert step_result["status"] == "passed"
        assert step_result["details"] == step_details
        assert "timestamp" in step_result
    
    def test_add_multiple_step_results(self):
        """Test adding multiple step results."""
        result = TestResult(
            test_case_id="tc_001",
            status=TestStatus.RUNNING,
            start_time=datetime.now()
        )
        
        # Add multiple step results
        result.add_step_result("step_001", TestStatus.PASSED)
        result.add_step_result("step_002", TestStatus.PASSED)
        result.add_step_result("step_003", TestStatus.FAILED, {"error": "Timeout"})
        
        assert len(result.step_results) == 3
        assert result.step_results[0]["step_id"] == "step_001"
        assert result.step_results[1]["step_id"] == "step_002"
        assert result.step_results[2]["step_id"] == "step_003"
        assert result.step_results[2]["status"] == "failed"
    
    def test_test_result_with_performance_metrics(self):
        """Test test result with performance metrics."""
        performance_metrics = {
            "page_load_time": 2.5,
            "element_find_time": 0.3,
            "action_execution_time": 0.1
        }
        
        result = TestResult(
            test_case_id="tc_001",
            status=TestStatus.PASSED,
            start_time=datetime.now(),
            performance_metrics=performance_metrics
        )
        
        assert result.performance_metrics == performance_metrics
        assert result.performance_metrics["page_load_time"] == 2.5
    
    def test_test_result_with_screenshots(self):
        """Test test result with screenshots."""
        screenshots = ["screenshot1.png", "screenshot2.png", "screenshot3.png"]
        
        result = TestResult(
            test_case_id="tc_001",
            status=TestStatus.FAILED,
            start_time=datetime.now(),
            screenshots=screenshots
        )
        
        assert result.screenshots == screenshots
        assert len(result.screenshots) == 3

class TestEnumValues:
    """Test enum value definitions."""
    
    def test_test_priority_values(self):
        """Test TestPriority enum values."""
        assert TestPriority.LOW.value == "low"
        assert TestPriority.MEDIUM.value == "medium"
        assert TestPriority.HIGH.value == "high"
        assert TestPriority.CRITICAL.value == "critical"
    
    def test_test_type_values(self):
        """Test TestType enum values."""
        assert TestType.FUNCTIONAL.value == "functional"
        assert TestType.PERFORMANCE.value == "performance"
        assert TestType.SECURITY.value == "security"
        assert TestType.USABILITY.value == "usability"
        assert TestType.INTEGRATION.value == "integration"
        assert TestType.REGRESSION.value == "regression"
    
    def test_test_status_values(self):
        """Test TestStatus enum values."""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"

class TestDataValidation:
    """Test data validation utilities."""
    
    def test_validate_test_case_structure(self, sample_test_cases):
        """Test validation of test case structure."""
        for test_case in sample_test_cases:
            # These should all be valid test case structures
            assert "id" in test_case
            assert "title" in test_case
            assert "description" in test_case
            assert "steps" in test_case
            assert "expected_result" in test_case
            assert len(test_case["steps"]) > 0
    
    def test_json_serialization(self, sample_steps):
        """Test JSON serialization of test models."""
        test_case = TestCase(
            id="tc_001",
            title="JSON Test",
            description="Test JSON serialization",
            steps=sample_steps,
            expected_result="Should serialize to JSON"
        )
        
        # Convert to dict and then to JSON
        test_dict = test_case.to_dict()
        json_str = json.dumps(test_dict)
        
        # Should not raise an exception
        assert json_str is not None
        assert len(json_str) > 0
        
        # Should be able to parse back
        parsed_dict = json.loads(json_str)
        assert parsed_dict["id"] == "tc_001"
        assert parsed_dict["title"] == "JSON Test"
    
    def test_test_case_metadata_handling(self, sample_steps):
        """Test metadata handling in test cases."""
        metadata = {
            "author": "Test Author",
            "version": "1.0",
            "browser_requirements": ["Chrome", "Firefox"],
            "test_environment": "staging"
        }
        
        test_case = TestCase(
            id="tc_001",
            title="Metadata Test",
            description="Test metadata handling",
            steps=sample_steps,
            expected_result="Metadata should be preserved",
            metadata=metadata
        )
        
        assert test_case.metadata == metadata
        assert test_case.metadata["author"] == "Test Author"
        assert "Chrome" in test_case.metadata["browser_requirements"]
    
    def test_step_timeout_validation(self):
        """Test step timeout validation."""
        # Valid timeout
        step = TestStep(
            id="step_001",
            description="Test step",
            action="click",
            timeout=30
        )
        assert step.timeout == 30
        
        # Very short timeout (edge case)
        step_short = TestStep(
            id="step_002",
            description="Quick step",
            action="click",
            timeout=1
        )
        assert step_short.timeout == 1
        
        # Long timeout
        step_long = TestStep(
            id="step_003",
            description="Slow step",
            action="wait",
            timeout=300
        )
        assert step_long.timeout == 300