#!/usr/bin/env python3
"""
Quality Validator - Test case validation and quality metrics for browser_use

This script validates test case completeness, checks selector reliability,
measures context degradation, and provides comprehensive quality metrics
for automated test generation and maintenance.

Author: Claude Code
Date: 2025-08-15
"""

import asyncio
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import re

# Browser_use imports
from browser_use import Agent, BrowserSession, BrowserProfile
from browser_use.browser.views import Page


class ValidationStatus(Enum):
    """Validation status levels"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class QualityMetric(Enum):
    """Types of quality metrics"""
    COMPLETENESS = "completeness"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    COVERAGE = "coverage"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    check_id: str
    check_name: str
    status: ValidationStatus
    score: float  # 0.0 to 1.0
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    execution_time_ms: float


@dataclass
class SelectorReliabilityTest:
    """Test result for selector reliability"""
    selector: str
    selector_type: str
    found_elements: int
    is_unique: bool
    is_stable: bool
    performance_ms: float
    error_message: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


@dataclass
class TestCaseQuality:
    """Overall quality assessment of a test case"""
    test_case_id: str
    overall_score: float
    metric_scores: Dict[QualityMetric, float]
    validation_results: List[ValidationResult]
    selector_reliability: List[SelectorReliabilityTest]
    context_degradation_score: float
    recommendations: List[str]
    validation_timestamp: datetime


@dataclass
class QualityReport:
    """Comprehensive quality report"""
    report_id: str
    generated_at: datetime
    test_cases_analyzed: int
    overall_quality_score: float
    quality_distribution: Dict[str, int]
    common_issues: List[Dict[str, Any]]
    best_practices_compliance: Dict[str, float]
    trends: Dict[str, List[float]]


class QualityValidator:
    """
    Comprehensive quality validation system for browser_use test cases
    
    Features:
    - Test case completeness validation
    - Selector reliability testing
    - Context degradation measurement
    - Performance quality metrics
    - Accessibility compliance checking
    - Best practices validation
    - Quality trend analysis
    """
    
    def __init__(self,
                 output_dir: str = "./quality_reports",
                 enable_performance_tests: bool = True,
                 enable_accessibility_tests: bool = True,
                 strict_mode: bool = False):
        """
        Initialize the quality validator
        
        Args:
            output_dir: Directory for quality reports
            enable_performance_tests: Whether to run performance tests
            enable_accessibility_tests: Whether to run accessibility tests
            strict_mode: Use strict validation criteria
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_performance_tests = enable_performance_tests
        self.enable_accessibility_tests = enable_accessibility_tests
        self.strict_mode = strict_mode
        
        # Quality thresholds
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.75,
            "acceptable": 0.6,
            "poor": 0.4,
            "critical": 0.0
        }
        
        # Validation rules
        self.validation_rules = self._initialize_validation_rules()
        
        # Historical data for trend analysis
        self.historical_data = []

    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation rules and criteria"""
        return {
            "completeness": {
                "min_steps": 3,
                "required_fields": ["test_id", "name", "description", "steps"],
                "step_required_fields": ["action_type", "description", "selector"],
                "min_selectors_per_step": 1
            },
            "reliability": {
                "max_selector_search_time_ms": 5000,
                "min_unique_selectors": 0.7,  # 70% of selectors should be unique
                "max_brittle_selectors": 0.3,  # 30% max brittle selectors
                "required_fallback_selectors": 2
            },
            "maintainability": {
                "max_xpath_complexity": 5,  # Max xpath depth
                "min_readable_selectors": 0.8,  # 80% readable selectors
                "max_hardcoded_values": 0.2,  # 20% max hardcoded values
                "required_documentation": 0.9  # 90% steps documented
            },
            "coverage": {
                "min_element_types_covered": 3,
                "min_interaction_types": 2,
                "min_validation_points": 1,
                "coverage_completeness": 0.8
            },
            "performance": {
                "max_step_execution_time_ms": 10000,
                "max_page_load_time_ms": 15000,
                "min_resource_efficiency": 0.7,
                "max_memory_usage_mb": 100
            }
        }

    async def validate_test_case(self,
                               test_case_data: Dict[str, Any],
                               page: Page = None) -> TestCaseQuality:
        """
        Validate a complete test case and return quality assessment
        
        Args:
            test_case_data: Test case data to validate
            page: Optional browser page for live validation
            
        Returns:
            TestCaseQuality with comprehensive assessment
        """
        start_time = datetime.now()
        test_case_id = test_case_data.get("test_id", "unknown")
        
        # Run all validation checks
        validation_results = []
        
        # Completeness validation
        completeness_results = await self._validate_completeness(test_case_data)
        validation_results.extend(completeness_results)
        
        # Selector reliability validation
        selector_reliability = await self._validate_selector_reliability(test_case_data, page)
        
        # Maintainability validation
        maintainability_results = await self._validate_maintainability(test_case_data)
        validation_results.extend(maintainability_results)
        
        # Coverage validation
        coverage_results = await self._validate_coverage(test_case_data)
        validation_results.extend(coverage_results)
        
        # Performance validation (if enabled and page available)
        if self.enable_performance_tests and page:
            performance_results = await self._validate_performance(test_case_data, page)
            validation_results.extend(performance_results)
        
        # Accessibility validation (if enabled and page available)
        if self.enable_accessibility_tests and page:
            accessibility_results = await self._validate_accessibility(test_case_data, page)
            validation_results.extend(accessibility_results)
        
        # Calculate metric scores
        metric_scores = self._calculate_metric_scores(validation_results)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metric_scores)
        
        # Calculate context degradation
        context_degradation = await self._measure_context_degradation(test_case_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validation_results, selector_reliability)
        
        quality = TestCaseQuality(
            test_case_id=test_case_id,
            overall_score=overall_score,
            metric_scores=metric_scores,
            validation_results=validation_results,
            selector_reliability=selector_reliability,
            context_degradation_score=context_degradation,
            recommendations=recommendations,
            validation_timestamp=start_time
        )
        
        # Save quality report
        await self._save_quality_report(quality)
        
        return quality

    async def _validate_completeness(self, test_case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate test case completeness"""
        results = []
        rules = self.validation_rules["completeness"]
        
        # Check required fields
        missing_fields = []
        for field in rules["required_fields"]:
            if field not in test_case_data or not test_case_data[field]:
                missing_fields.append(field)
        
        results.append(ValidationResult(
            check_id="completeness_required_fields",
            check_name="Required Fields Present",
            status=ValidationStatus.PASSED if not missing_fields else ValidationStatus.FAILED,
            score=1.0 if not missing_fields else 0.0,
            message=f"Missing fields: {missing_fields}" if missing_fields else "All required fields present",
            details={"missing_fields": missing_fields, "total_fields": len(rules["required_fields"])},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        # Check minimum steps
        steps = test_case_data.get("steps", [])
        min_steps = rules["min_steps"]
        has_min_steps = len(steps) >= min_steps
        
        results.append(ValidationResult(
            check_id="completeness_min_steps",
            check_name="Minimum Steps Count",
            status=ValidationStatus.PASSED if has_min_steps else ValidationStatus.WARNING,
            score=1.0 if has_min_steps else max(0.0, len(steps) / min_steps),
            message=f"Has {len(steps)} steps (minimum: {min_steps})",
            details={"steps_count": len(steps), "minimum_required": min_steps},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        # Check step completeness
        step_scores = []
        for i, step in enumerate(steps):
            missing_step_fields = []
            for field in rules["step_required_fields"]:
                if field not in step or not step[field]:
                    missing_step_fields.append(field)
            
            step_score = 1.0 if not missing_step_fields else (
                (len(rules["step_required_fields"]) - len(missing_step_fields)) / len(rules["step_required_fields"])
            )
            step_scores.append(step_score)
        
        avg_step_score = statistics.mean(step_scores) if step_scores else 0.0
        
        results.append(ValidationResult(
            check_id="completeness_step_fields",
            check_name="Step Fields Completeness",
            status=ValidationStatus.PASSED if avg_step_score >= 0.9 else 
                   ValidationStatus.WARNING if avg_step_score >= 0.7 else ValidationStatus.FAILED,
            score=avg_step_score,
            message=f"Average step completeness: {avg_step_score:.2f}",
            details={"step_scores": step_scores, "average_score": avg_step_score},
            timestamp=datetime.now(),
            execution_time_ms=2.0
        ))
        
        return results

    async def _validate_selector_reliability(self,
                                           test_case_data: Dict[str, Any],
                                           page: Page = None) -> List[SelectorReliabilityTest]:
        """Validate selector reliability and stability"""
        results = []
        steps = test_case_data.get("steps", [])
        
        for step in steps:
            selector = step.get("selector", "")
            if not selector:
                continue
            
            start_time = datetime.now()
            
            try:
                if page:
                    # Live validation
                    elements = await self._find_elements_by_selector(page, selector)
                    found_count = len(elements)
                    is_unique = found_count == 1
                    
                    # Test stability by running multiple times
                    stability_tests = []
                    for _ in range(3):
                        test_elements = await self._find_elements_by_selector(page, selector)
                        stability_tests.append(len(test_elements) == found_count)
                    
                    is_stable = all(stability_tests)
                    
                else:
                    # Static analysis
                    found_count = -1  # Unknown
                    is_unique = self._analyze_selector_uniqueness(selector)
                    is_stable = self._analyze_selector_stability(selector)
                
                end_time = datetime.now()
                performance_ms = (end_time - start_time).total_seconds() * 1000
                
                # Generate suggestions
                suggestions = self._generate_selector_suggestions(selector, found_count, is_unique, is_stable)
                
                results.append(SelectorReliabilityTest(
                    selector=selector,
                    selector_type=self._determine_selector_type(selector),
                    found_elements=found_count,
                    is_unique=is_unique,
                    is_stable=is_stable,
                    performance_ms=performance_ms,
                    suggestions=suggestions
                ))
                
            except Exception as e:
                results.append(SelectorReliabilityTest(
                    selector=selector,
                    selector_type=self._determine_selector_type(selector),
                    found_elements=0,
                    is_unique=False,
                    is_stable=False,
                    performance_ms=0.0,
                    error_message=str(e),
                    suggestions=["Fix selector syntax error", "Use alternative selector strategy"]
                ))
        
        return results

    async def _find_elements_by_selector(self, page: Page, selector: str) -> List[Any]:
        """Find elements using various selector strategies"""
        try:
            # Try CSS selector first
            if not selector.startswith("//") and not selector.startswith("xpath="):
                return await page.query_selector_all(selector)
            
            # Try XPath
            if selector.startswith("//") or selector.startswith("xpath="):
                xpath_selector = selector.replace("xpath=", "")
                return await page.query_selector_all(f"xpath={xpath_selector}")
            
            # Try text content
            if selector.startswith("text="):
                text_value = selector.replace("text=", "")
                script = f"""
                () => {{
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_ELEMENT,
                        null,
                        false
                    );
                    
                    const elements = [];
                    let node;
                    while (node = walker.nextNode()) {{
                        if (node.textContent && node.textContent.includes('{text_value}')) {{
                            elements.push(node);
                        }}
                    }}
                    return elements;
                }}
                """
                return await page.evaluate(script)
            
            return []
            
        except Exception:
            return []

    def _analyze_selector_uniqueness(self, selector: str) -> bool:
        """Analyze if selector is likely to be unique (static analysis)"""
        # ID selectors are usually unique
        if "#" in selector and selector.count("#") == 1:
            return True
        
        # Data-testid attributes are designed to be unique
        if "data-testid" in selector or "data-test-id" in selector:
            return True
        
        # Complex selectors with multiple attributes are more likely unique
        if selector.count("[") >= 2:
            return True
        
        # Simple tag or class selectors are usually not unique
        if re.match(r"^[a-zA-Z]+$", selector) or re.match(r"^\.[a-zA-Z-_]+$", selector):
            return False
        
        return True  # Default to True for other cases

    def _analyze_selector_stability(self, selector: str) -> bool:
        """Analyze if selector is likely to be stable (static analysis)"""
        # ID and data-testid selectors are stable
        if "#" in selector or "data-testid" in selector:
            return True
        
        # XPath selectors with deep nesting are brittle
        if selector.startswith("//") and selector.count("/") > 5:
            return False
        
        # Selectors with positional indicators are brittle
        if re.search(r":nth-child|:first-child|:last-child", selector):
            return False
        
        # Text-based selectors can be brittle
        if selector.startswith("text="):
            return False
        
        return True

    def _determine_selector_type(self, selector: str) -> str:
        """Determine the type of selector"""
        if selector.startswith("//") or selector.startswith("xpath="):
            return "xpath"
        elif selector.startswith("text="):
            return "text"
        elif "#" in selector:
            return "id"
        elif "." in selector and not "[" in selector:
            return "class"
        elif "[" in selector:
            return "attribute"
        else:
            return "tag"

    def _generate_selector_suggestions(self,
                                     selector: str,
                                     found_count: int,
                                     is_unique: bool,
                                     is_stable: bool) -> List[str]:
        """Generate suggestions for improving selectors"""
        suggestions = []
        
        if found_count == 0:
            suggestions.append("Selector not found - verify element exists")
            suggestions.append("Consider using alternative selector strategies")
        
        if found_count > 1 and not is_unique:
            suggestions.append("Multiple elements found - make selector more specific")
            suggestions.append("Add unique attributes like ID or data-testid")
        
        if not is_stable:
            suggestions.append("Selector may be brittle - avoid positional selectors")
            suggestions.append("Use semantic attributes instead of structural selectors")
        
        if selector.startswith("//") and selector.count("/") > 3:
            suggestions.append("XPath is too complex - simplify or use CSS selector")
        
        if re.search(r":nth-child", selector):
            suggestions.append("Avoid nth-child selectors - use unique attributes")
        
        if "data-testid" not in selector and "id" not in selector:
            suggestions.append("Consider adding data-testid for better reliability")
        
        return suggestions

    async def _validate_maintainability(self, test_case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate test case maintainability"""
        results = []
        steps = test_case_data.get("steps", [])
        rules = self.validation_rules["maintainability"]
        
        # Analyze XPath complexity
        xpath_selectors = [step.get("selector", "") for step in steps if step.get("selector", "").startswith("//")]
        complex_xpaths = [sel for sel in xpath_selectors if sel.count("/") > rules["max_xpath_complexity"]]
        
        xpath_score = 1.0 if not complex_xpaths else max(0.0, 1.0 - len(complex_xpaths) / len(xpath_selectors)) if xpath_selectors else 1.0
        
        results.append(ValidationResult(
            check_id="maintainability_xpath_complexity",
            check_name="XPath Complexity",
            status=ValidationStatus.PASSED if xpath_score >= 0.8 else ValidationStatus.WARNING,
            score=xpath_score,
            message=f"{len(complex_xpaths)} complex XPath selectors found",
            details={"complex_xpaths": complex_xpaths, "total_xpaths": len(xpath_selectors)},
            timestamp=datetime.now(),
            execution_time_ms=2.0
        ))
        
        # Analyze selector readability
        readable_selectors = 0
        total_selectors = 0
        
        for step in steps:
            selector = step.get("selector", "")
            if selector:
                total_selectors += 1
                if self._is_readable_selector(selector):
                    readable_selectors += 1
        
        readability_score = readable_selectors / total_selectors if total_selectors > 0 else 1.0
        
        results.append(ValidationResult(
            check_id="maintainability_readability",
            check_name="Selector Readability",
            status=ValidationStatus.PASSED if readability_score >= rules["min_readable_selectors"] else ValidationStatus.WARNING,
            score=readability_score,
            message=f"{readable_selectors}/{total_selectors} selectors are readable",
            details={"readable_count": readable_selectors, "total_count": total_selectors},
            timestamp=datetime.now(),
            execution_time_ms=1.5
        ))
        
        # Check documentation completeness
        documented_steps = sum(1 for step in steps if step.get("description") and len(step["description"]) > 10)
        documentation_score = documented_steps / len(steps) if steps else 1.0
        
        results.append(ValidationResult(
            check_id="maintainability_documentation",
            check_name="Documentation Completeness",
            status=ValidationStatus.PASSED if documentation_score >= rules["required_documentation"] else ValidationStatus.WARNING,
            score=documentation_score,
            message=f"{documented_steps}/{len(steps)} steps have adequate documentation",
            details={"documented_count": documented_steps, "total_count": len(steps)},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        return results

    def _is_readable_selector(self, selector: str) -> bool:
        """Check if selector is human-readable"""
        # ID and data-testid selectors are readable
        if "#" in selector or "data-testid" in selector:
            return True
        
        # Simple class selectors are readable
        if re.match(r"^\.[a-zA-Z-_]+$", selector):
            return True
        
        # Complex XPath selectors are not readable
        if selector.startswith("//") and selector.count("/") > 3:
            return False
        
        # Long selectors are less readable
        if len(selector) > 100:
            return False
        
        return True

    async def _validate_coverage(self, test_case_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate test coverage"""
        results = []
        steps = test_case_data.get("steps", [])
        rules = self.validation_rules["coverage"]
        
        # Analyze element types coverage
        element_types = set()
        interaction_types = set()
        validation_points = 0
        
        for step in steps:
            action_type = step.get("action_type", "")
            selector = step.get("selector", "")
            
            # Extract element type from selector
            if selector:
                if "input" in selector.lower():
                    element_types.add("input")
                elif "button" in selector.lower():
                    element_types.add("button")
                elif "select" in selector.lower():
                    element_types.add("select")
                elif "a" in selector.lower() or "link" in selector.lower():
                    element_types.add("link")
                elif "form" in selector.lower():
                    element_types.add("form")
            
            # Count interaction types
            if action_type:
                interaction_types.add(action_type.lower())
            
            # Count validation points
            if action_type.lower() in ["verify", "check", "assert", "validate"]:
                validation_points += 1
        
        # Element types coverage
        element_coverage_score = min(1.0, len(element_types) / rules["min_element_types_covered"])
        
        results.append(ValidationResult(
            check_id="coverage_element_types",
            check_name="Element Types Coverage",
            status=ValidationStatus.PASSED if element_coverage_score >= 1.0 else ValidationStatus.WARNING,
            score=element_coverage_score,
            message=f"Covers {len(element_types)} element types",
            details={"element_types": list(element_types), "count": len(element_types)},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        # Interaction types coverage
        interaction_coverage_score = min(1.0, len(interaction_types) / rules["min_interaction_types"])
        
        results.append(ValidationResult(
            check_id="coverage_interaction_types",
            check_name="Interaction Types Coverage",
            status=ValidationStatus.PASSED if interaction_coverage_score >= 1.0 else ValidationStatus.WARNING,
            score=interaction_coverage_score,
            message=f"Covers {len(interaction_types)} interaction types",
            details={"interaction_types": list(interaction_types), "count": len(interaction_types)},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        # Validation points coverage
        validation_coverage_score = min(1.0, validation_points / rules["min_validation_points"])
        
        results.append(ValidationResult(
            check_id="coverage_validation_points",
            check_name="Validation Points Coverage",
            status=ValidationStatus.PASSED if validation_coverage_score >= 1.0 else ValidationStatus.WARNING,
            score=validation_coverage_score,
            message=f"Has {validation_points} validation points",
            details={"validation_points": validation_points, "minimum_required": rules["min_validation_points"]},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        return results

    async def _validate_performance(self, test_case_data: Dict[str, Any], page: Page) -> List[ValidationResult]:
        """Validate performance characteristics"""
        results = []
        
        # This would require actual performance measurement during execution
        # For now, we'll provide placeholder performance validation
        
        # Simulate performance metrics
        estimated_execution_time = len(test_case_data.get("steps", [])) * 2000  # 2 seconds per step
        
        results.append(ValidationResult(
            check_id="performance_estimated_time",
            check_name="Estimated Execution Time",
            status=ValidationStatus.PASSED if estimated_execution_time <= 60000 else ValidationStatus.WARNING,
            score=max(0.0, 1.0 - (estimated_execution_time - 60000) / 60000) if estimated_execution_time > 60000 else 1.0,
            message=f"Estimated execution time: {estimated_execution_time/1000:.1f} seconds",
            details={"estimated_time_ms": estimated_execution_time, "max_acceptable_ms": 60000},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        return results

    async def _validate_accessibility(self, test_case_data: Dict[str, Any], page: Page) -> List[ValidationResult]:
        """Validate accessibility considerations"""
        results = []
        steps = test_case_data.get("steps", [])
        
        # Check for accessibility-friendly selectors
        accessible_selectors = 0
        total_selectors = 0
        
        for step in steps:
            selector = step.get("selector", "")
            if selector:
                total_selectors += 1
                if self._is_accessible_selector(selector):
                    accessible_selectors += 1
        
        accessibility_score = accessible_selectors / total_selectors if total_selectors > 0 else 1.0
        
        results.append(ValidationResult(
            check_id="accessibility_selector_compliance",
            check_name="Accessibility-Friendly Selectors",
            status=ValidationStatus.PASSED if accessibility_score >= 0.7 else ValidationStatus.WARNING,
            score=accessibility_score,
            message=f"{accessible_selectors}/{total_selectors} selectors are accessibility-friendly",
            details={"accessible_count": accessible_selectors, "total_count": total_selectors},
            timestamp=datetime.now(),
            execution_time_ms=1.0
        ))
        
        return results

    def _is_accessible_selector(self, selector: str) -> bool:
        """Check if selector uses accessibility-friendly attributes"""
        accessible_patterns = [
            "aria-label", "aria-labelledby", "aria-describedby",
            "role=", "alt=", "title=", "data-testid"
        ]
        
        return any(pattern in selector for pattern in accessible_patterns)

    async def _measure_context_degradation(self, test_case_data: Dict[str, Any]) -> float:
        """Measure context degradation over test steps"""
        steps = test_case_data.get("steps", [])
        
        if len(steps) < 3:
            return 0.0  # Not enough steps to measure degradation
        
        # Simple degradation model based on selector complexity increase
        complexity_scores = []
        
        for step in steps:
            selector = step.get("selector", "")
            description = step.get("description", "")
            
            # Calculate complexity score
            complexity = 0
            complexity += len(selector) / 100  # Length factor
            complexity += selector.count("/") * 0.2  # XPath depth
            complexity += selector.count("[") * 0.1  # Attribute complexity
            complexity += (1.0 if len(description) < 10 else 0.0)  # Poor description
            
            complexity_scores.append(complexity)
        
        # Calculate degradation as increase in complexity over time
        if len(complexity_scores) < 2:
            return 0.0
        
        # Linear regression to find trend
        x_values = list(range(len(complexity_scores)))
        y_values = complexity_scores
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Normalize slope to 0-1 range (positive slope indicates degradation)
        degradation_score = max(0.0, min(1.0, slope))
        
        return degradation_score

    def _calculate_metric_scores(self, validation_results: List[ValidationResult]) -> Dict[QualityMetric, float]:
        """Calculate scores for each quality metric"""
        metric_scores = {}
        
        # Group results by metric type
        metric_groups = {
            QualityMetric.COMPLETENESS: [r for r in validation_results if "completeness" in r.check_id],
            QualityMetric.RELIABILITY: [r for r in validation_results if "reliability" in r.check_id],
            QualityMetric.MAINTAINABILITY: [r for r in validation_results if "maintainability" in r.check_id],
            QualityMetric.COVERAGE: [r for r in validation_results if "coverage" in r.check_id],
            QualityMetric.PERFORMANCE: [r for r in validation_results if "performance" in r.check_id],
            QualityMetric.ACCESSIBILITY: [r for r in validation_results if "accessibility" in r.check_id]
        }
        
        # Calculate average score for each metric
        for metric, results in metric_groups.items():
            if results:
                metric_scores[metric] = statistics.mean(result.score for result in results)
            else:
                metric_scores[metric] = 1.0  # Default to perfect if no tests
        
        return metric_scores

    def _calculate_overall_score(self, metric_scores: Dict[QualityMetric, float]) -> float:
        """Calculate overall quality score with weighted metrics"""
        weights = {
            QualityMetric.COMPLETENESS: 0.25,
            QualityMetric.RELIABILITY: 0.25,
            QualityMetric.MAINTAINABILITY: 0.20,
            QualityMetric.COVERAGE: 0.15,
            QualityMetric.PERFORMANCE: 0.10,
            QualityMetric.ACCESSIBILITY: 0.05
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, score in metric_scores.items():
            weight = weights.get(metric, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _generate_recommendations(self,
                                validation_results: List[ValidationResult],
                                selector_reliability: List[SelectorReliabilityTest]) -> List[str]:
        """Generate actionable recommendations for improvement"""
        recommendations = []
        
        # Analyze validation results
        failed_checks = [r for r in validation_results if r.status == ValidationStatus.FAILED]
        warning_checks = [r for r in validation_results if r.status == ValidationStatus.WARNING]
        
        # Critical issues first
        for result in failed_checks:
            if "completeness" in result.check_id:
                recommendations.append(f"CRITICAL: {result.message} - Add missing required fields")
            elif "reliability" in result.check_id:
                recommendations.append(f"CRITICAL: {result.message} - Fix unreliable selectors")
        
        # Warning issues
        for result in warning_checks[:3]:  # Limit to top 3 warnings
            recommendations.append(f"WARNING: {result.check_name} - {result.message}")
        
        # Selector-specific recommendations
        unreliable_selectors = [s for s in selector_reliability if not s.is_stable or not s.is_unique]
        if unreliable_selectors:
            recommendations.append(f"Improve {len(unreliable_selectors)} unreliable selectors")
            
            # Add specific suggestions from top unreliable selectors
            for selector_test in unreliable_selectors[:2]:
                recommendations.extend(selector_test.suggestions[:2])
        
        # General recommendations
        if len([r for r in validation_results if r.score < 0.7]) > 3:
            recommendations.append("Consider comprehensive test case redesign")
        
        return recommendations[:8]  # Limit to top 8 recommendations

    async def _save_quality_report(self, quality: TestCaseQuality):
        """Save quality report to file"""
        timestamp = quality.validation_timestamp.strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"quality_{quality.test_case_id}_{timestamp}.json"
        
        # Convert to serializable format
        quality_dict = asdict(quality)
        quality_dict["validation_timestamp"] = quality.validation_timestamp.isoformat()
        
        # Convert validation results
        for result in quality_dict["validation_results"]:
            result["timestamp"] = datetime.fromisoformat(result["timestamp"]).isoformat()
        
        # Convert enum keys to strings
        quality_dict["metric_scores"] = {k.value: v for k, v in quality.metric_scores.items()}
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(quality_dict, f, indent=2, ensure_ascii=False)
        
        print(f"Quality report saved to: {report_file}")

    async def generate_quality_report(self, test_cases: List[Dict[str, Any]]) -> QualityReport:
        """Generate comprehensive quality report for multiple test cases"""
        report_id = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        # Validate all test cases
        quality_assessments = []
        for test_case in test_cases:
            quality = await self.validate_test_case(test_case)
            quality_assessments.append(quality)
        
        # Calculate overall statistics
        overall_scores = [q.overall_score for q in quality_assessments]
        overall_quality_score = statistics.mean(overall_scores) if overall_scores else 0.0
        
        # Quality distribution
        quality_distribution = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0, "critical": 0}
        for score in overall_scores:
            if score >= self.quality_thresholds["excellent"]:
                quality_distribution["excellent"] += 1
            elif score >= self.quality_thresholds["good"]:
                quality_distribution["good"] += 1
            elif score >= self.quality_thresholds["acceptable"]:
                quality_distribution["acceptable"] += 1
            elif score >= self.quality_thresholds["poor"]:
                quality_distribution["poor"] += 1
            else:
                quality_distribution["critical"] += 1
        
        # Common issues analysis
        common_issues = self._analyze_common_issues(quality_assessments)
        
        # Best practices compliance
        best_practices = self._analyze_best_practices_compliance(quality_assessments)
        
        report = QualityReport(
            report_id=report_id,
            generated_at=datetime.now(),
            test_cases_analyzed=len(test_cases),
            overall_quality_score=overall_quality_score,
            quality_distribution=quality_distribution,
            common_issues=common_issues,
            best_practices_compliance=best_practices,
            trends={}  # Would be populated with historical data
        )
        
        # Save comprehensive report
        await self._save_comprehensive_report(report)
        
        return report

    def _analyze_common_issues(self, quality_assessments: List[TestCaseQuality]) -> List[Dict[str, Any]]:
        """Analyze common issues across test cases"""
        issue_counts = {}
        
        for quality in quality_assessments:
            for result in quality.validation_results:
                if result.status in [ValidationStatus.FAILED, ValidationStatus.WARNING]:
                    issue_key = result.check_name
                    if issue_key not in issue_counts:
                        issue_counts[issue_key] = {"count": 0, "total_score": 0.0, "check_id": result.check_id}
                    issue_counts[issue_key]["count"] += 1
                    issue_counts[issue_key]["total_score"] += result.score
        
        # Sort by frequency and create list
        common_issues = []
        for issue_name, data in sorted(issue_counts.items(), key=lambda x: x[1]["count"], reverse=True):
            common_issues.append({
                "issue": issue_name,
                "frequency": data["count"],
                "affected_test_cases": data["count"],
                "avg_score": data["total_score"] / data["count"],
                "check_id": data["check_id"]
            })
        
        return common_issues[:10]  # Top 10 issues

    def _analyze_best_practices_compliance(self, quality_assessments: List[TestCaseQuality]) -> Dict[str, float]:
        """Analyze compliance with best practices"""
        practices = {
            "unique_selectors": [],
            "stable_selectors": [],
            "accessible_selectors": [],
            "documented_steps": [],
            "reasonable_complexity": []
        }
        
        for quality in quality_assessments:
            # Analyze selector practices
            total_selectors = len(quality.selector_reliability)
            if total_selectors > 0:
                unique_selectors = sum(1 for s in quality.selector_reliability if s.is_unique)
                stable_selectors = sum(1 for s in quality.selector_reliability if s.is_stable)
                
                practices["unique_selectors"].append(unique_selectors / total_selectors)
                practices["stable_selectors"].append(stable_selectors / total_selectors)
            
            # Extract other practices from validation results
            for result in quality.validation_results:
                if "accessibility" in result.check_id:
                    practices["accessible_selectors"].append(result.score)
                elif "documentation" in result.check_id:
                    practices["documented_steps"].append(result.score)
                elif "complexity" in result.check_id:
                    practices["reasonable_complexity"].append(result.score)
        
        # Calculate averages
        compliance = {}
        for practice, scores in practices.items():
            compliance[practice] = statistics.mean(scores) if scores else 0.0
        
        return compliance

    async def _save_comprehensive_report(self, report: QualityReport):
        """Save comprehensive quality report"""
        report_file = self.output_dir / f"comprehensive_report_{report.report_id}.json"
        
        # Convert to serializable format
        report_dict = asdict(report)
        report_dict["generated_at"] = report.generated_at.isoformat()
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        print(f"Comprehensive quality report saved to: {report_file}")


# Example usage
async def example_usage():
    """Example usage of QualityValidator"""
    
    # Initialize validator
    validator = QualityValidator(
        output_dir="./quality_reports",
        enable_performance_tests=True,
        enable_accessibility_tests=True,
        strict_mode=False
    )
    
    # Sample test case data
    test_case = {
        "test_id": "login_test_001",
        "name": "User Login Flow",
        "description": "Test user login with valid credentials",
        "steps": [
            {
                "action_type": "navigate",
                "description": "Navigate to login page",
                "selector": "button.login-btn",
                "expected_result": "Login page displayed"
            },
            {
                "action_type": "type",
                "description": "Enter username",
                "selector": "#username",
                "expected_result": "Username entered"
            },
            {
                "action_type": "type",
                "description": "Enter password",
                "selector": "input[data-testid='password']",
                "expected_result": "Password entered"
            },
            {
                "action_type": "click",
                "description": "Click submit button",
                "selector": "//button[@type='submit']",
                "expected_result": "Form submitted"
            },
            {
                "action_type": "verify",
                "description": "Verify successful login",
                "selector": ".welcome-message",
                "expected_result": "Welcome message displayed"
            }
        ]
    }
    
    # Validate single test case
    quality = await validator.validate_test_case(test_case)
    
    print(f"Test Case Quality Report:")
    print(f"Overall Score: {quality.overall_score:.2f}")
    print(f"Context Degradation: {quality.context_degradation_score:.2f}")
    print(f"Recommendations: {len(quality.recommendations)}")
    
    for rec in quality.recommendations[:3]:
        print(f"  - {rec}")
    
    print(f"\nMetric Scores:")
    for metric, score in quality.metric_scores.items():
        print(f"  {metric.value}: {score:.2f}")
    
    print(f"\nSelector Reliability:")
    for selector_test in quality.selector_reliability[:3]:
        print(f"  {selector_test.selector}: unique={selector_test.is_unique}, stable={selector_test.is_stable}")
        if selector_test.suggestions:
            print(f"    Suggestions: {selector_test.suggestions[0]}")
    
    # Generate comprehensive report for multiple test cases
    test_cases = [test_case]  # In practice, you'd have multiple test cases
    comprehensive_report = await validator.generate_quality_report(test_cases)
    
    print(f"\nComprehensive Report:")
    print(f"Test Cases Analyzed: {comprehensive_report.test_cases_analyzed}")
    print(f"Overall Quality Score: {comprehensive_report.overall_quality_score:.2f}")
    print(f"Quality Distribution: {comprehensive_report.quality_distribution}")


if __name__ == "__main__":
    print("Quality Validator - Example Usage")
    print("=" * 40)
    
    asyncio.run(example_usage())