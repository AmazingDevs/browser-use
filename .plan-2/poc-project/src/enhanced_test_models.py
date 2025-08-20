"""
Enhanced Test Models with QA Metadata and Professional Standards

This module extends the basic test models with comprehensive QA metadata,
professional testing standards, and enhanced structures for production-ready test cases.

Key Enhancements:
- Preconditions, postconditions, and cleanup procedures
- Test data requirements and validation rules
- Security and accessibility considerations
- Risk assessment and priority management
- Traceability and coverage tracking
- Quality metadata integration
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Union
from enum import Enum
from datetime import datetime
import uuid

# Import base models
from test_models import ExploratoryTestStep, ExploratoryTestCase, SelectorExtractor, TestCaseFormatter


class TestPriority(Enum):
    """Test case priority levels."""
    CRITICAL = "critical"     # Must pass for release
    HIGH = "high"            # Important functionality
    MEDIUM = "medium"        # Standard testing
    LOW = "low"             # Nice to have


class RiskLevel(Enum):
    """Risk assessment levels."""
    VERY_HIGH = "very_high"  # Critical business impact
    HIGH = "high"           # Significant impact
    MEDIUM = "medium"       # Moderate impact
    LOW = "low"            # Minimal impact
    VERY_LOW = "very_low"   # Negligible impact


class TestType(Enum):
    """Types of testing performed."""
    FUNCTIONAL = "functional"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    SMOKE = "smoke"


class ValidationRule(Enum):
    """Validation rule types for test data."""
    REQUIRED = "required"
    FORMAT = "format"
    RANGE = "range"
    PATTERN = "pattern"
    CUSTOM = "custom"


@dataclass
class TestDataRequirement:
    """Specification for test data requirements."""
    field_name: str
    data_type: str  # string, number, email, etc.
    validation_rules: List[ValidationRule]
    valid_examples: List[str] = field(default_factory=list)
    invalid_examples: List[str] = field(default_factory=list)
    description: str = ""
    is_sensitive: bool = False  # PII, passwords, etc.
    generation_strategy: str = "static"  # static, dynamic, random
    
    def __post_init__(self):
        if not self.valid_examples and self.data_type == "email":
            self.valid_examples = ["test@example.com", "user.name@domain.org"]
        if not self.invalid_examples and self.data_type == "email":
            self.invalid_examples = ["invalid-email", "@missing-local.com", "missing-at-sign.com"]


@dataclass
class SecurityConsideration:
    """Security testing considerations for test cases."""
    vulnerability_type: str  # XSS, SQL injection, CSRF, etc.
    test_scenarios: List[str]
    payloads: List[str] = field(default_factory=list)
    expected_behavior: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    def __post_init__(self):
        if self.vulnerability_type.upper() == "XSS" and not self.payloads:
            self.payloads = [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');''"
            ]
        elif self.vulnerability_type.upper() == "SQL_INJECTION" and not self.payloads:
            self.payloads = [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "admin'--"
            ]


@dataclass
class AccessibilityRequirement:
    """Accessibility testing requirements."""
    wcag_level: str = "AA"  # A, AA, AAA
    requirements: List[str] = field(default_factory=list)
    assistive_technologies: List[str] = field(default_factory=list)
    keyboard_navigation: bool = True
    screen_reader_support: bool = True
    color_contrast_check: bool = True
    
    def __post_init__(self):
        if not self.requirements:
            self.requirements = [
                "All interactive elements must be keyboard accessible",
                "All images must have alt text",
                "Form fields must have proper labels",
                "Page must have proper heading structure",
                "Color should not be the only way to convey information"
            ]
        if not self.assistive_technologies:
            self.assistive_technologies = ["NVDA", "JAWS", "VoiceOver"]


@dataclass
class PerformanceExpectation:
    """Performance testing expectations."""
    page_load_time_ms: Optional[int] = None
    action_response_time_ms: Optional[int] = None
    memory_usage_mb: Optional[int] = None
    network_requests_count: Optional[int] = None
    render_time_ms: Optional[int] = None
    
    def __post_init__(self):
        # Set reasonable defaults if not specified
        if self.page_load_time_ms is None:
            self.page_load_time_ms = 3000  # 3 seconds
        if self.action_response_time_ms is None:
            self.action_response_time_ms = 200  # 200ms for UI responsiveness


@dataclass
class TestPrecondition:
    """Precondition required before test execution."""
    condition_id: str
    description: str
    setup_steps: List[str] = field(default_factory=list)
    validation_criteria: str = ""
    automation_script: Optional[str] = None
    manual_verification: bool = False
    
    def __post_init__(self):
        if not self.condition_id:
            self.condition_id = f"precond_{uuid.uuid4().hex[:8]}"


@dataclass
class TestPostcondition:
    """Postcondition to validate after test execution."""
    condition_id: str
    description: str
    validation_steps: List[str] = field(default_factory=list)
    success_criteria: str = ""
    failure_action: str = "log_and_continue"  # log_and_continue, fail_test, retry
    
    def __post_init__(self):
        if not self.condition_id:
            self.condition_id = f"postcond_{uuid.uuid4().hex[:8]}"


@dataclass
class CleanupProcedure:
    """Cleanup procedure to run after test execution."""
    procedure_id: str
    description: str
    cleanup_steps: List[str] = field(default_factory=list)
    order: int = 1  # Execution order for multiple cleanup procedures
    mandatory: bool = True  # Whether cleanup must succeed
    automation_script: Optional[str] = None
    
    def __post_init__(self):
        if not self.procedure_id:
            self.procedure_id = f"cleanup_{uuid.uuid4().hex[:8]}"


@dataclass
class EnhancedTestStep:
    """Enhanced test step with comprehensive QA metadata."""
    # Base fields from ExploratoryTestStep
    step_number: int
    action_type: str
    description: str
    selector: str
    input_data: Optional[str] = None
    expected_result: str = ""
    actual_result: Optional[str] = None
    page_url: str = ""
    screenshot_ref: Optional[str] = None
    timestamp: Optional[str] = None
    assertions: Optional[List[str]] = None
    
    # Enhanced QA fields
    test_data_requirements: List[TestDataRequirement] = field(default_factory=list)
    security_considerations: List[SecurityConsideration] = field(default_factory=list)
    accessibility_checks: List[str] = field(default_factory=list)
    performance_expectations: Optional[PerformanceExpectation] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    validation_rules: List[str] = field(default_factory=list)
    error_scenarios: List[str] = field(default_factory=list)
    alternative_flows: List[str] = field(default_factory=list)
    
    # Traceability
    requirement_ids: List[str] = field(default_factory=list)
    user_story_id: Optional[str] = None
    acceptance_criteria_id: Optional[str] = None
    
    # Execution metadata
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if self.assertions is None:
            self.assertions = []
        
        # Auto-generate accessibility checks based on action type
        if not self.accessibility_checks:
            self._generate_accessibility_checks()
        
        # Auto-generate validation rules based on input data
        if self.input_data and not self.validation_rules:
            self._generate_validation_rules()
    
    def _generate_accessibility_checks(self):
        """Auto-generate accessibility checks based on action type."""
        if self.action_type == "click":
            self.accessibility_checks.extend([
                "Element should be keyboard accessible (Tab to reach, Enter/Space to activate)",
                "Element should have proper ARIA labels or visible text",
                "Focus should be clearly visible when element is focused"
            ])
        elif self.action_type == "type":
            self.accessibility_checks.extend([
                "Input field should have associated label",
                "Error messages should be programmatically associated with field",
                "Field should announce its purpose to screen readers"
            ])
        elif self.action_type == "navigate":
            self.accessibility_checks.extend([
                "Page should have proper heading structure (h1, h2, etc.)",
                "Page should have a meaningful title",
                "Focus should be set appropriately after navigation"
            ])
    
    def _generate_validation_rules(self):
        """Auto-generate validation rules based on input data."""
        if self.input_data:
            # Email validation
            if "@" in self.input_data:
                self.validation_rules.append("Validate email format")
                self.validation_rules.append("Test with invalid email formats")
            
            # Number validation
            if self.input_data.isdigit():
                self.validation_rules.append("Validate numeric input")
                self.validation_rules.append("Test with non-numeric characters")
            
            # Length validation
            if len(self.input_data) > 50:
                self.validation_rules.append("Test maximum length validation")
            
            # Special characters
            if any(char in self.input_data for char in '<>&"\''):
                self.validation_rules.append("Test special character handling")
                self.validation_rules.append("Verify XSS protection")


@dataclass
class EnhancedTestCase:
    """Enhanced test case with comprehensive QA metadata and professional standards."""
    # Base fields from ExploratoryTestCase
    test_id: str
    scenario_name: str
    steps: List[EnhancedTestStep]
    discovered_elements: List[Dict[str, Any]] = field(default_factory=list)
    edge_cases: List[str] = field(default_factory=list)
    coverage_metrics: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None
    
    # Enhanced QA fields
    preconditions: List[TestPrecondition] = field(default_factory=list)
    postconditions: List[TestPostcondition] = field(default_factory=list)
    cleanup_procedures: List[CleanupProcedure] = field(default_factory=list)
    test_data_requirements: List[TestDataRequirement] = field(default_factory=list)
    security_considerations: List[SecurityConsideration] = field(default_factory=list)
    accessibility_requirements: Optional[AccessibilityRequirement] = None
    performance_expectations: Optional[PerformanceExpectation] = None
    
    # Risk and classification
    risk_level: RiskLevel = RiskLevel.MEDIUM
    test_types: List[TestType] = field(default_factory=list)
    business_value: str = ""
    impact_analysis: str = ""
    
    # Traceability and requirements
    requirement_ids: List[str] = field(default_factory=list)
    user_story_ids: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    
    # Environment and configuration
    target_environments: List[str] = field(default_factory=list)
    browser_requirements: List[str] = field(default_factory=list)
    device_requirements: List[str] = field(default_factory=list)
    
    # Quality metadata
    quality_score: Optional[float] = None
    quality_gate_status: Optional[str] = None
    last_quality_assessment: Optional[str] = None
    quality_issues: List[str] = field(default_factory=list)
    
    # Execution tracking
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    maintenance_notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.test_types:
            self.test_types = [TestType.FUNCTIONAL]
        
        if not self.target_environments:
            self.target_environments = ["staging", "production"]
        
        if not self.browser_requirements:
            self.browser_requirements = ["Chrome", "Firefox", "Safari", "Edge"]
        
        if not self.accessibility_requirements:
            self.accessibility_requirements = AccessibilityRequirement()
        
        if not self.performance_expectations:
            self.performance_expectations = PerformanceExpectation()
        
        # Auto-generate basic cleanup if none specified
        if not self.cleanup_procedures and len(self.steps) > 3:
            self.cleanup_procedures.append(CleanupProcedure(
                procedure_id="auto_cleanup",
                description="Reset application state after test execution",
                cleanup_steps=[
                    "Clear browser cache and cookies",
                    "Reset any modified data",
                    "Logout user if authenticated",
                    "Close any open dialogs or modals"
                ]
            ))
    
    def add_security_consideration(self, vulnerability_type: str, test_scenarios: List[str], risk_level: RiskLevel = RiskLevel.MEDIUM):
        """Add security consideration to the test case."""
        security_consideration = SecurityConsideration(
            vulnerability_type=vulnerability_type,
            test_scenarios=test_scenarios,
            risk_level=risk_level
        )
        self.security_considerations.append(security_consideration)
    
    def add_test_data_requirement(self, field_name: str, data_type: str, validation_rules: List[ValidationRule]):
        """Add test data requirement."""
        requirement = TestDataRequirement(
            field_name=field_name,
            data_type=data_type,
            validation_rules=validation_rules
        )
        self.test_data_requirements.append(requirement)
    
    def get_total_validation_points(self) -> int:
        """Get total number of validation points across all steps."""
        total = 0
        for step in self.steps:
            total += len(step.assertions)
            total += len(step.validation_rules)
            total += len(step.accessibility_checks)
        return total
    
    def get_security_coverage_score(self) -> float:
        """Calculate security coverage score (0-100)."""
        if not self.security_considerations:
            return 0.0
        
        # Base score for having security considerations
        score = 50.0
        
        # Additional points for different vulnerability types
        vulnerability_types = set(sc.vulnerability_type for sc in self.security_considerations)
        score += len(vulnerability_types) * 10  # 10 points per unique vulnerability type
        
        # Additional points for comprehensive test scenarios
        total_scenarios = sum(len(sc.test_scenarios) for sc in self.security_considerations)
        score += min(40, total_scenarios * 5)  # Max 40 points for scenarios
        
        return min(100.0, score)
    
    def get_accessibility_coverage_score(self) -> float:
        """Calculate accessibility coverage score (0-100)."""
        if not self.accessibility_requirements:
            return 0.0
        
        score = 0.0
        
        # Points for having accessibility requirements
        if self.accessibility_requirements.requirements:
            score += 30
        
        # Points for keyboard navigation support
        if self.accessibility_requirements.keyboard_navigation:
            score += 20
        
        # Points for screen reader support
        if self.accessibility_requirements.screen_reader_support:
            score += 20
        
        # Points for accessibility checks in steps
        accessibility_steps = sum(1 for step in self.steps if step.accessibility_checks)
        if accessibility_steps > 0:
            score += min(30, accessibility_steps * 10)
        
        return min(100.0, score)


class EnhancedTestCaseFormatter:
    """Enhanced formatter for comprehensive test case output."""
    
    def __init__(self):
        self.base_formatter = TestCaseFormatter()
    
    def to_comprehensive_playwright_script(self, test_case: EnhancedTestCase) -> str:
        """Generate comprehensive Playwright script with QA enhancements."""
        script_lines = []
        
        # Add comprehensive imports and setup
        script_lines.extend([
            "const { test, expect } = require('@playwright/test');",
            "const { AccessibilityChecker } = require('./utils/accessibility-checker');",
            "const { SecurityTester } = require('./utils/security-tester');",
            "const { PerformanceMonitor } = require('./utils/performance-monitor');",
            "",
            f"test.describe('{test_case.scenario_name}', () => {{",
            f"  test('{test_case.test_id}', async ({{ page }}) => {{",
            ""
        ])
        
        # Add test metadata as comments
        script_lines.extend([
            f"    // Test ID: {test_case.test_id}",
            f"    // Priority: {test_case.priority}",
            f"    // Risk Level: {test_case.risk_level.value}",
            f"    // Estimated Duration: {test_case.estimated_duration}s",
            f"    // Test Types: {', '.join([tt.value for tt in test_case.test_types])}",
            ""
        ])
        
        # Add preconditions
        if test_case.preconditions:
            script_lines.append("    // === PRECONDITIONS ===")
            for precond in test_case.preconditions:
                script_lines.append(f"    // {precond.description}")
                for step in precond.setup_steps:
                    script_lines.append(f"    // Setup: {step}")
            script_lines.append("")
        
        # Initialize monitoring tools
        script_lines.extend([
            "    // Initialize monitoring tools",
            "    const accessibilityChecker = new AccessibilityChecker(page);",
            "    const securityTester = new SecurityTester(page);",
            "    const performanceMonitor = new PerformanceMonitor(page);",
            "",
            "    // Start performance monitoring",
            "    await performanceMonitor.startMonitoring();",
            ""
        ])
        
        # Convert each step with enhancements
        for step in test_case.steps:
            step_code = self._convert_enhanced_step_to_playwright(step)
            script_lines.extend(step_code)
            script_lines.append("")
        
        # Add security validations
        if test_case.security_considerations:
            script_lines.append("    // === SECURITY VALIDATIONS ===")
            for security in test_case.security_considerations:
                script_lines.append(f"    // Test for {security.vulnerability_type}")
                for scenario in security.test_scenarios:
                    script_lines.append(f"    // Scenario: {scenario}")
                script_lines.append("    await securityTester.runSecurityChecks();")
            script_lines.append("")
        
        # Add accessibility validations
        script_lines.extend([
            "    // === ACCESSIBILITY VALIDATIONS ===",
            "    await accessibilityChecker.runA11yChecks();",
            "    await accessibilityChecker.checkKeyboardNavigation();",
            "    await accessibilityChecker.checkColorContrast();",
            ""
        ])
        
        # Add performance validations
        if test_case.performance_expectations:
            perf = test_case.performance_expectations
            script_lines.extend([
                "    // === PERFORMANCE VALIDATIONS ===",
                "    const performanceMetrics = await performanceMonitor.getMetrics();",
            ])
            
            if perf.page_load_time_ms:
                script_lines.append(f"    expect(performanceMetrics.pageLoadTime).toBeLessThan({perf.page_load_time_ms});")
            
            if perf.action_response_time_ms:
                script_lines.append(f"    expect(performanceMetrics.averageResponseTime).toBeLessThan({perf.action_response_time_ms});")
            
            script_lines.append("")
        
        # Add postconditions
        if test_case.postconditions:
            script_lines.append("    // === POSTCONDITIONS ===")
            for postcond in test_case.postconditions:
                script_lines.append(f"    // Validate: {postcond.description}")
                for step in postcond.validation_steps:
                    script_lines.append(f"    // Check: {step}")
            script_lines.append("")
        
        # Add cleanup procedures
        if test_case.cleanup_procedures:
            script_lines.append("    // === CLEANUP PROCEDURES ===")
            for cleanup in sorted(test_case.cleanup_procedures, key=lambda x: x.order):
                script_lines.append(f"    // {cleanup.description}")
                for step in cleanup.cleanup_steps:
                    script_lines.append(f"    // Cleanup: {step}")
            script_lines.append("")
        
        # Close test
        script_lines.extend([
            "  });",
            "});",
            ""
        ])
        
        # Add edge cases as separate tests
        if test_case.edge_cases:
            script_lines.extend([
                f"  test.describe('Edge Cases for {test_case.test_id}', () => {{",
                ""
            ])
            
            for i, edge_case in enumerate(test_case.edge_cases):
                script_lines.extend([
                    f"    test('Edge Case {i+1}: {edge_case}', async ({{ page }}) => {{",
                    f"      // TODO: Implement edge case test for: {edge_case}",
                    "    });",
                    ""
                ])
            
            script_lines.append("  });")
        
        return "\n".join(script_lines)
    
    def _convert_enhanced_step_to_playwright(self, step: EnhancedTestStep) -> List[str]:
        """Convert enhanced test step to Playwright code with QA validations."""
        lines = []
        indent = "    "
        
        # Add step header with metadata
        lines.extend([
            f"{indent}// === STEP {step.step_number}: {step.description} ===",
            f"{indent}// Action: {step.action_type}",
            f"{indent}// Risk Level: {step.risk_level.value}",
            f"{indent}// Selector: {step.selector}"
        ])
        
        # Add test data requirements
        if step.test_data_requirements:
            lines.append(f"{indent}// Test Data Requirements:")
            for req in step.test_data_requirements:
                lines.append(f"{indent}//   {req.field_name}: {req.data_type}")
        
        # Add main action
        if step.action_type == 'navigate':
            if step.page_url:
                lines.append(f"{indent}await page.goto('{step.page_url}');")
            elif step.input_data:
                lines.append(f"{indent}await page.goto('{step.input_data}');")
        
        elif step.action_type == 'click':
            lines.extend([
                f"{indent}await page.waitForSelector('{step.selector}');",
                f"{indent}await page.click('{step.selector}');"
            ])
        
        elif step.action_type == 'type':
            if step.input_data:
                lines.extend([
                    f"{indent}await page.waitForSelector('{step.selector}');",
                    f"{indent}await page.fill('{step.selector}', '');",
                    f"{indent}await page.type('{step.selector}', '{step.input_data}');"
                ])
        
        # Add performance monitoring for this step
        if step.performance_expectations:
            lines.extend([
                f"{indent}// Monitor performance for this step",
                f"{indent}const stepStartTime = Date.now();",
            ])
        
        # Add security validations
        if step.security_considerations:
            lines.append(f"{indent}// Security validations for this step")
            for security in step.security_considerations:
                lines.append(f"{indent}// Check for {security.vulnerability_type}")
                for payload in security.payloads:
                    lines.append(f"{indent}// Test payload: {payload}")
        
        # Add accessibility checks
        if step.accessibility_checks:
            lines.append(f"{indent}// Accessibility checks")
            for check in step.accessibility_checks:
                lines.append(f"{indent}// A11y: {check}")
        
        # Add validation rules
        if step.validation_rules:
            lines.append(f"{indent}// Validation rules")
            for rule in step.validation_rules:
                lines.append(f"{indent}// Validate: {rule}")
        
        # Add assertions
        if step.assertions:
            for assertion in step.assertions:
                lines.append(f"{indent}// Assert: {assertion}")
                lines.append(f"{indent}await expect(page.locator('{step.selector}')).toBeVisible();")
        
        # Add expected result validation
        if step.expected_result:
            lines.extend([
                f"{indent}// Expected: {step.expected_result}",
                f"{indent}await expect(page.locator('{step.selector}')).toBeVisible();"
            ])
        
        # Complete performance monitoring
        if step.performance_expectations:
            lines.extend([
                f"{indent}const stepDuration = Date.now() - stepStartTime;",
                f"{indent}expect(stepDuration).toBeLessThan({step.performance_expectations.action_response_time_ms});"
            ])
        
        # Add wait for stability
        if step.action_type in ['click', 'type', 'select']:
            lines.append(f"{indent}await page.waitForTimeout(500); // Wait for action to complete")
        
        return lines
    
    def to_comprehensive_json(self, test_case: EnhancedTestCase) -> Dict[str, Any]:
        """Export enhanced test case as comprehensive JSON."""
        result = {
            "metadata": {
                "test_id": test_case.test_id,
                "scenario_name": test_case.scenario_name,
                "priority": test_case.priority,
                "risk_level": test_case.risk_level.value,
                "test_types": [tt.value for tt in test_case.test_types],
                "estimated_duration": test_case.estimated_duration,
                "business_value": test_case.business_value,
                "impact_analysis": test_case.impact_analysis,
                "total_steps": len(test_case.steps),
                "total_validation_points": test_case.get_total_validation_points(),
                "security_coverage_score": test_case.get_security_coverage_score(),
                "accessibility_coverage_score": test_case.get_accessibility_coverage_score(),
                "generated_at": datetime.now().isoformat()
            },
            "requirements_traceability": {
                "requirement_ids": test_case.requirement_ids,
                "user_story_ids": test_case.user_story_ids,
                "acceptance_criteria": test_case.acceptance_criteria
            },
            "quality_metadata": {
                "quality_score": test_case.quality_score,
                "quality_gate_status": test_case.quality_gate_status,
                "last_quality_assessment": test_case.last_quality_assessment,
                "quality_issues": test_case.quality_issues
            },
            "environment_configuration": {
                "target_environments": test_case.target_environments,
                "browser_requirements": test_case.browser_requirements,
                "device_requirements": test_case.device_requirements
            },
            "preconditions": [
                {
                    "condition_id": pc.condition_id,
                    "description": pc.description,
                    "setup_steps": pc.setup_steps,
                    "validation_criteria": pc.validation_criteria,
                    "manual_verification": pc.manual_verification
                }
                for pc in test_case.preconditions
            ],
            "postconditions": [
                {
                    "condition_id": pc.condition_id,
                    "description": pc.description,
                    "validation_steps": pc.validation_steps,
                    "success_criteria": pc.success_criteria,
                    "failure_action": pc.failure_action
                }
                for pc in test_case.postconditions
            ],
            "cleanup_procedures": [
                {
                    "procedure_id": cp.procedure_id,
                    "description": cp.description,
                    "cleanup_steps": cp.cleanup_steps,
                    "order": cp.order,
                    "mandatory": cp.mandatory
                }
                for cp in test_case.cleanup_procedures
            ],
            "test_data_requirements": [
                {
                    "field_name": tdr.field_name,
                    "data_type": tdr.data_type,
                    "validation_rules": [vr.value for vr in tdr.validation_rules],
                    "valid_examples": tdr.valid_examples,
                    "invalid_examples": tdr.invalid_examples,
                    "description": tdr.description,
                    "is_sensitive": tdr.is_sensitive,
                    "generation_strategy": tdr.generation_strategy
                }
                for tdr in test_case.test_data_requirements
            ],
            "security_considerations": [
                {
                    "vulnerability_type": sc.vulnerability_type,
                    "test_scenarios": sc.test_scenarios,
                    "payloads": sc.payloads,
                    "expected_behavior": sc.expected_behavior,
                    "risk_level": sc.risk_level.value
                }
                for sc in test_case.security_considerations
            ],
            "accessibility_requirements": {
                "wcag_level": test_case.accessibility_requirements.wcag_level,
                "requirements": test_case.accessibility_requirements.requirements,
                "assistive_technologies": test_case.accessibility_requirements.assistive_technologies,
                "keyboard_navigation": test_case.accessibility_requirements.keyboard_navigation,
                "screen_reader_support": test_case.accessibility_requirements.screen_reader_support,
                "color_contrast_check": test_case.accessibility_requirements.color_contrast_check
            },
            "performance_expectations": {
                "page_load_time_ms": test_case.performance_expectations.page_load_time_ms,
                "action_response_time_ms": test_case.performance_expectations.action_response_time_ms,
                "memory_usage_mb": test_case.performance_expectations.memory_usage_mb,
                "network_requests_count": test_case.performance_expectations.network_requests_count,
                "render_time_ms": test_case.performance_expectations.render_time_ms
            },
            "steps": [
                {
                    "step_number": step.step_number,
                    "action_type": step.action_type,
                    "description": step.description,
                    "selector": step.selector,
                    "input_data": step.input_data,
                    "expected_result": step.expected_result,
                    "page_url": step.page_url,
                    "timestamp": step.timestamp,
                    "risk_level": step.risk_level.value,
                    "assertions": step.assertions,
                    "validation_rules": step.validation_rules,
                    "accessibility_checks": step.accessibility_checks,
                    "error_scenarios": step.error_scenarios,
                    "alternative_flows": step.alternative_flows,
                    "requirement_ids": step.requirement_ids,
                    "retry_count": step.retry_count,
                    "max_retries": step.max_retries,
                    "timeout_seconds": step.timeout_seconds,
                    "test_data_requirements": [
                        {
                            "field_name": tdr.field_name,
                            "data_type": tdr.data_type,
                            "validation_rules": [vr.value for vr in tdr.validation_rules],
                            "is_sensitive": tdr.is_sensitive
                        }
                        for tdr in step.test_data_requirements
                    ],
                    "security_considerations": [
                        {
                            "vulnerability_type": sc.vulnerability_type,
                            "test_scenarios": sc.test_scenarios,
                            "risk_level": sc.risk_level.value
                        }
                        for sc in step.security_considerations
                    ]
                }
                for step in test_case.steps
            ],
            "discovered_elements": test_case.discovered_elements,
            "edge_cases": test_case.edge_cases,
            "coverage_metrics": test_case.coverage_metrics,
            "execution_history": test_case.execution_history,
            "maintenance_notes": test_case.maintenance_notes
        }
        
        return result


# Utility functions for creating enhanced test components

def create_enhanced_test_step(
    step_number: int,
    action_type: str,
    description: str,
    selector: str,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    **kwargs
) -> EnhancedTestStep:
    """Create an enhanced test step with QA metadata."""
    return EnhancedTestStep(
        step_number=step_number,
        action_type=action_type,
        description=description,
        selector=selector,
        risk_level=risk_level,
        **kwargs
    )


def create_enhanced_test_case(
    test_id: str,
    scenario_name: str,
    steps: List[EnhancedTestStep],
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    test_types: List[TestType] = None,
    **kwargs
) -> EnhancedTestCase:
    """Create an enhanced test case with comprehensive QA metadata."""
    if test_types is None:
        test_types = [TestType.FUNCTIONAL]
    
    return EnhancedTestCase(
        test_id=test_id,
        scenario_name=scenario_name,
        steps=steps,
        risk_level=risk_level,
        test_types=test_types,
        **kwargs
    )


def add_security_testing_step(
    base_step: EnhancedTestStep,
    vulnerability_type: str,
    test_scenarios: List[str],
    payloads: List[str] = None
) -> EnhancedTestStep:
    """Add security testing considerations to an existing step."""
    security_consideration = SecurityConsideration(
        vulnerability_type=vulnerability_type,
        test_scenarios=test_scenarios,
        payloads=payloads or []
    )
    base_step.security_considerations.append(security_consideration)
    return base_step


def add_accessibility_checks_to_step(
    base_step: EnhancedTestStep,
    additional_checks: List[str]
) -> EnhancedTestStep:
    """Add additional accessibility checks to an existing step."""
    base_step.accessibility_checks.extend(additional_checks)
    return base_step