"""
QA Quality Framework for Exploratory Test Case Generation

This module implements comprehensive quality assessment and scoring for generated test cases,
providing professional-grade validation to ensure test cases meet production standards.

Key Features:
- Multi-dimensional quality scoring (clarity, completeness, automation readiness)
- Quality gates and thresholds for production readiness
- Automated quality improvement suggestions
- Risk-based quality validation
- Performance and maintainability metrics
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
import re
import json
from datetime import datetime


class QualityDimension(Enum):
    """Quality assessment dimensions for test cases."""
    CLARITY = "clarity"
    COMPLETENESS = "completeness"
    AUTOMATION_READINESS = "automation_readiness"
    MAINTAINABILITY = "maintainability"
    COVERAGE = "coverage"
    RELIABILITY = "reliability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"


class QualityGate(Enum):
    """Quality gate levels for test case validation."""
    FAILED = "failed"           # < 60% - Not production ready
    BASIC = "basic"             # 60-70% - Requires improvement
    GOOD = "good"               # 70-80% - Acceptable for testing
    EXCELLENT = "excellent"     # 80-90% - High quality
    OUTSTANDING = "outstanding" # 90-100% - Premium quality


@dataclass
class QualityScore:
    """Represents a quality score for a specific dimension."""
    dimension: QualityDimension
    score: float  # 0.0 to 100.0
    max_score: float = 100.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def percentage(self) -> float:
        """Get score as percentage."""
        return (self.score / self.max_score) * 100
    
    @property
    def grade(self) -> str:
        """Get letter grade for score."""
        if self.percentage >= 90:
            return "A+"
        elif self.percentage >= 80:
            return "A"
        elif self.percentage >= 70:
            return "B"
        elif self.percentage >= 60:
            return "C"
        else:
            return "F"


@dataclass
class QualityAssessment:
    """Complete quality assessment for a test case."""
    test_id: str
    overall_score: float
    quality_gate: QualityGate
    dimension_scores: Dict[QualityDimension, QualityScore]
    critical_issues: List[str] = field(default_factory=list)
    improvement_plan: List[str] = field(default_factory=list)
    production_ready: bool = False
    assessment_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted overall score based on dimension importance."""
        weights = {
            QualityDimension.CLARITY: 0.15,
            QualityDimension.COMPLETENESS: 0.20,
            QualityDimension.AUTOMATION_READINESS: 0.25,
            QualityDimension.MAINTAINABILITY: 0.15,
            QualityDimension.COVERAGE: 0.10,
            QualityDimension.RELIABILITY: 0.10,
            QualityDimension.SECURITY: 0.03,
            QualityDimension.ACCESSIBILITY: 0.02
        }
        
        total_weighted = 0.0
        total_weight = 0.0
        
        for dimension, weight in weights.items():
            if dimension in self.dimension_scores:
                total_weighted += self.dimension_scores[dimension].score * weight
                total_weight += weight
        
        return total_weighted / total_weight if total_weight > 0 else 0.0


class QualityFramework:
    """
    Main quality assessment framework for evaluating test cases.
    
    Provides comprehensive analysis across multiple quality dimensions with
    automated scoring, issue detection, and improvement recommendations.
    """
    
    def __init__(self):
        self.quality_thresholds = {
            QualityGate.OUTSTANDING: 90.0,
            QualityGate.EXCELLENT: 80.0,
            QualityGate.GOOD: 70.0,
            QualityGate.BASIC: 60.0,
            QualityGate.FAILED: 0.0
        }
        
        # Security patterns for validation
        self.security_patterns = {
            'xss_indicators': [
                r'<script.*?>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'alert\s*\(',
                r'document\.cookie'
            ],
            'sql_injection_indicators': [
                r'union\s+select',
                r'drop\s+table',
                r'delete\s+from',
                r'insert\s+into',
                r'update\s+.*\s+set',
                r'or\s+1\s*=\s*1',
                r';\s*--'
            ]
        }
    
    def assess_test_case(self, test_case: Dict[str, Any]) -> QualityAssessment:
        """
        Perform comprehensive quality assessment of a test case.
        
        Args:
            test_case: Test case dictionary to assess
            
        Returns:
            QualityAssessment with detailed scores and recommendations
        """
        test_id = test_case.get('metadata', {}).get('test_id', 'unknown')
        
        # Assess each quality dimension
        dimension_scores = {}
        
        dimension_scores[QualityDimension.CLARITY] = self._assess_clarity(test_case)
        dimension_scores[QualityDimension.COMPLETENESS] = self._assess_completeness(test_case)
        dimension_scores[QualityDimension.AUTOMATION_READINESS] = self._assess_automation_readiness(test_case)
        dimension_scores[QualityDimension.MAINTAINABILITY] = self._assess_maintainability(test_case)
        dimension_scores[QualityDimension.COVERAGE] = self._assess_coverage(test_case)
        dimension_scores[QualityDimension.RELIABILITY] = self._assess_reliability(test_case)
        dimension_scores[QualityDimension.SECURITY] = self._assess_security(test_case)
        dimension_scores[QualityDimension.ACCESSIBILITY] = self._assess_accessibility(test_case)
        
        # Calculate overall score
        overall_score = sum(score.score for score in dimension_scores.values()) / len(dimension_scores)
        
        # Determine quality gate
        quality_gate = self._determine_quality_gate(overall_score)
        
        # Identify critical issues
        critical_issues = self._identify_critical_issues(dimension_scores)
        
        # Generate improvement plan
        improvement_plan = self._generate_improvement_plan(dimension_scores)
        
        # Determine production readiness
        production_ready = overall_score >= self.quality_thresholds[QualityGate.GOOD]
        
        return QualityAssessment(
            test_id=test_id,
            overall_score=overall_score,
            quality_gate=quality_gate,
            dimension_scores=dimension_scores,
            critical_issues=critical_issues,
            improvement_plan=improvement_plan,
            production_ready=production_ready
        )
    
    def _assess_clarity(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess test case clarity and readability."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        steps = test_case.get('steps', [])
        scenario_name = test_case.get('metadata', {}).get('scenario_name', '')
        
        # Check scenario name clarity
        if not scenario_name or len(scenario_name) < 10:
            score -= 15
            issues.append("Scenario name is too short or missing")
            suggestions.append("Provide descriptive scenario name (10+ characters)")
        
        # Check step descriptions
        unclear_steps = 0
        for step in steps:
            description = step.get('description', '')
            if not description or len(description) < 5:
                unclear_steps += 1
            elif any(word in description.lower() for word in ['unknown', 'element', 'thing']):
                unclear_steps += 1
        
        if unclear_steps > 0:
            penalty = min(30, unclear_steps * 10)
            score -= penalty
            issues.append(f"{unclear_steps} steps have unclear descriptions")
            suggestions.append("Improve step descriptions with specific, actionable language")
        
        # Check for generic selectors
        generic_selectors = sum(1 for step in steps 
                              if step.get('selector', '').lower() in ['body', 'html', 'unknown element'])
        if generic_selectors > 0:
            score -= generic_selectors * 5
            issues.append(f"{generic_selectors} steps use generic selectors")
            suggestions.append("Replace generic selectors with specific element identifiers")
        
        details = {
            "scenario_name_length": len(scenario_name),
            "unclear_steps": unclear_steps,
            "generic_selectors": generic_selectors,
            "total_steps": len(steps)
        }
        
        return QualityScore(
            dimension=QualityDimension.CLARITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _assess_completeness(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess test case completeness and thoroughness."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        # Check required fields
        required_fields = ['steps', 'metadata']
        missing_fields = [field for field in required_fields if field not in test_case]
        
        if missing_fields:
            score -= len(missing_fields) * 25
            issues.append(f"Missing required fields: {missing_fields}")
            suggestions.append("Add all required test case fields")
        
        steps = test_case.get('steps', [])
        metadata = test_case.get('metadata', {})
        
        # Check step completeness
        incomplete_steps = 0
        for step in steps:
            required_step_fields = ['action_type', 'description', 'selector']
            missing_step_fields = [field for field in required_step_fields if not step.get(field)]
            if missing_step_fields:
                incomplete_steps += 1
        
        if incomplete_steps > 0:
            score -= incomplete_steps * 10
            issues.append(f"{incomplete_steps} steps are incomplete")
            suggestions.append("Ensure all steps have action_type, description, and selector")
        
        # Check for preconditions
        if not test_case.get('preconditions'):
            score -= 10
            issues.append("No preconditions specified")
            suggestions.append("Add preconditions to clarify test setup requirements")
        
        # Check for expected results
        steps_without_expectations = sum(1 for step in steps if not step.get('expected_result'))
        if steps_without_expectations > len(steps) * 0.5:  # More than 50% without expectations
            score -= 15
            issues.append("Many steps lack expected results")
            suggestions.append("Add expected results for better validation")
        
        # Check for edge cases
        if not test_case.get('edge_cases'):
            score -= 10
            issues.append("No edge cases identified")
            suggestions.append("Identify potential edge cases and error scenarios")
        
        details = {
            "total_steps": len(steps),
            "incomplete_steps": incomplete_steps,
            "steps_without_expectations": steps_without_expectations,
            "has_preconditions": bool(test_case.get('preconditions')),
            "has_edge_cases": bool(test_case.get('edge_cases'))
        }
        
        return QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _assess_automation_readiness(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess how ready the test case is for automation."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        steps = test_case.get('steps', [])
        
        # Check selector quality
        poor_selectors = 0
        for step in steps:
            selector = step.get('selector', '')
            if not selector or selector in ['body', 'html']:
                poor_selectors += 1
            elif not self._is_robust_selector(selector):
                poor_selectors += 1
        
        if poor_selectors > 0:
            penalty = min(40, poor_selectors * 15)
            score -= penalty
            issues.append(f"{poor_selectors} steps have poor selectors for automation")
            suggestions.append("Improve selectors using data-testid, ID, or stable attributes")
        
        # Check for automation-unfriendly actions
        manual_actions = sum(1 for step in steps 
                           if step.get('action_type') in ['manual_verification', 'visual_check'])
        if manual_actions > 0:
            score -= manual_actions * 10
            issues.append(f"{manual_actions} steps require manual verification")
            suggestions.append("Convert manual steps to automated assertions where possible")
        
        # Check for test data specification
        type_actions = [step for step in steps if step.get('action_type') == 'type']
        type_without_data = sum(1 for step in type_actions if not step.get('input_data'))
        
        if type_without_data > 0:
            score -= type_without_data * 5
            issues.append(f"{type_without_data} input steps lack test data")
            suggestions.append("Specify test data for all input fields")
        
        # Check for dynamic waits vs fixed delays
        wait_actions = [step for step in steps if 'wait' in step.get('action_type', '')]
        if len(wait_actions) == 0 and len(steps) > 3:
            score -= 10
            issues.append("No explicit waits - may cause flaky tests")
            suggestions.append("Add appropriate waits for dynamic elements")
        
        details = {
            "total_steps": len(steps),
            "poor_selectors": poor_selectors,
            "manual_actions": manual_actions,
            "type_without_data": type_without_data,
            "wait_actions": len(wait_actions)
        }
        
        return QualityScore(
            dimension=QualityDimension.AUTOMATION_READINESS,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _assess_maintainability(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess test case maintainability over time."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        steps = test_case.get('steps', [])
        
        # Check test case length
        if len(steps) > 15:
            score -= 15
            issues.append("Test case is too long (>15 steps)")
            suggestions.append("Consider breaking into smaller, focused test cases")
        
        # Check for hard-coded values
        hardcoded_values = 0
        for step in steps:
            input_data = step.get('input_data', '')
            if input_data and any(val in input_data.lower() for val in ['test', 'example', '123', 'abc']):
                hardcoded_values += 1
        
        if hardcoded_values > 0:
            score -= hardcoded_values * 5
            issues.append(f"{hardcoded_values} steps use hard-coded test data")
            suggestions.append("Use parameterized test data instead of hard-coded values")
        
        # Check for brittle selectors (XPath, complex CSS)
        brittle_selectors = 0
        for step in steps:
            selector = step.get('selector', '')
            if selector.startswith('//') or selector.count('>') > 2:
                brittle_selectors += 1
        
        if brittle_selectors > 0:
            score -= brittle_selectors * 8
            issues.append(f"{brittle_selectors} steps use brittle selectors")
            suggestions.append("Use more stable selectors (data-testid, semantic selectors)")
        
        # Check for cleanup steps
        has_cleanup = any('cleanup' in step.get('description', '').lower() for step in steps)
        if not has_cleanup and len(steps) > 5:
            score -= 10
            issues.append("No cleanup steps identified")
            suggestions.append("Add cleanup steps to ensure test isolation")
        
        details = {
            "total_steps": len(steps),
            "hardcoded_values": hardcoded_values,
            "brittle_selectors": brittle_selectors,
            "has_cleanup": has_cleanup
        }
        
        return QualityScore(
            dimension=QualityDimension.MAINTAINABILITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _assess_coverage(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess test coverage breadth and depth."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        steps = test_case.get('steps', [])
        coverage_metrics = test_case.get('coverage_metrics', {})
        
        # Check action diversity
        action_types = [step.get('action_type') for step in steps]
        unique_actions = len(set(action_types))
        
        if unique_actions < 3:
            score -= 20
            issues.append("Limited action diversity")
            suggestions.append("Include more diverse user interactions (click, type, verify, etc.)")
        
        # Check verification steps
        verification_steps = sum(1 for step in steps if step.get('action_type') == 'verify')
        if verification_steps == 0:
            score -= 25
            issues.append("No verification steps")
            suggestions.append("Add verification steps to validate expected outcomes")
        elif verification_steps < len(steps) * 0.2:  # Less than 20% verification
            score -= 10
            issues.append("Insufficient verification coverage")
            suggestions.append("Increase verification steps for better validation")
        
        # Check edge cases coverage
        edge_cases = test_case.get('edge_cases', [])
        if len(edge_cases) == 0:
            score -= 15
            issues.append("No edge cases covered")
            suggestions.append("Identify and test edge cases and error conditions")
        
        details = {
            "total_steps": len(steps),
            "unique_actions": unique_actions,
            "verification_steps": verification_steps,
            "edge_cases_count": len(edge_cases),
            "coverage_metrics": coverage_metrics
        }
        
        return QualityScore(
            dimension=QualityDimension.COVERAGE,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _assess_reliability(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess test case reliability and stability."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        steps = test_case.get('steps', [])
        
        # Check for proper waits
        click_steps = [step for step in steps if step.get('action_type') == 'click']
        waits_after_clicks = 0
        
        for i, step in enumerate(steps):
            if step.get('action_type') == 'click' and i < len(steps) - 1:
                next_step = steps[i + 1]
                if 'wait' in next_step.get('action_type', '') or 'timeout' in next_step.get('description', ''):
                    waits_after_clicks += 1
        
        if len(click_steps) > waits_after_clicks:
            score -= 15
            issues.append("Missing waits after dynamic actions")
            suggestions.append("Add waits after clicks and dynamic actions for stability")
        
        # Check for error handling
        has_error_handling = any('error' in step.get('description', '').lower() for step in steps)
        if not has_error_handling and len(steps) > 5:
            score -= 10
            issues.append("No error handling scenarios")
            suggestions.append("Include error handling and negative test scenarios")
        
        # Check for timing issues
        rapid_succession_actions = 0
        for i in range(len(steps) - 1):
            current_action = steps[i].get('action_type')
            next_action = steps[i + 1].get('action_type')
            if current_action in ['click', 'type'] and next_action in ['click', 'type']:
                rapid_succession_actions += 1
        
        if rapid_succession_actions > len(steps) * 0.3:  # More than 30% rapid actions
            score -= 15
            issues.append("Too many rapid succession actions")
            suggestions.append("Add appropriate delays between rapid actions")
        
        details = {
            "total_steps": len(steps),
            "click_steps": len(click_steps),
            "waits_after_clicks": waits_after_clicks,
            "has_error_handling": has_error_handling,
            "rapid_succession_actions": rapid_succession_actions
        }
        
        return QualityScore(
            dimension=QualityDimension.RELIABILITY,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _assess_security(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess security testing coverage."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        steps = test_case.get('steps', [])
        
        # Check for security-relevant inputs
        form_steps = [step for step in steps if step.get('action_type') == 'type']
        security_test_data = 0
        
        for step in form_steps:
            input_data = step.get('input_data', '')
            # Check for security test patterns
            for pattern_type, patterns in self.security_patterns.items():
                if any(re.search(pattern, input_data, re.IGNORECASE) for pattern in patterns):
                    security_test_data += 1
                    break
        
        # Basic security score (most tests won't include security testing)
        if len(form_steps) > 0:
            if security_test_data == 0:
                score = 70  # Neutral score for tests without explicit security testing
                suggestions.append("Consider adding security test data for form inputs")
            else:
                score = 100  # Bonus for including security test patterns
                details["security_patterns_found"] = security_test_data
        
        # Check for authentication scenarios
        auth_related = any(word in ' '.join([step.get('description', '') for step in steps]).lower() 
                          for word in ['login', 'password', 'auth', 'token', 'session'])
        
        if auth_related:
            details["auth_related"] = True
            suggestions.append("Ensure authentication scenarios include security validations")
        
        details.update({
            "form_steps": len(form_steps),
            "security_test_data": security_test_data,
            "auth_related": auth_related
        })
        
        return QualityScore(
            dimension=QualityDimension.SECURITY,
            score=score,
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _assess_accessibility(self, test_case: Dict[str, Any]) -> QualityScore:
        """Assess accessibility testing coverage."""
        score = 100.0
        issues = []
        suggestions = []
        details = {}
        
        steps = test_case.get('steps', [])
        
        # Check for accessibility-aware selectors
        accessible_selectors = 0
        for step in steps:
            selector = step.get('selector', '')
            if any(attr in selector for attr in ['aria-', 'role=', 'label=']):
                accessible_selectors += 1
        
        # Check for keyboard navigation
        keyboard_actions = sum(1 for step in steps 
                              if any(key in step.get('description', '').lower() 
                                   for key in ['tab', 'enter', 'space', 'arrow', 'escape']))
        
        # Basic accessibility scoring (most tests won't focus on accessibility)
        if len(steps) > 0:
            accessibility_score = 70  # Neutral baseline
            
            if accessible_selectors > 0:
                accessibility_score += 15
                details["accessible_selectors"] = accessible_selectors
                
            if keyboard_actions > 0:
                accessibility_score += 15
                details["keyboard_actions"] = keyboard_actions
                
            score = min(100, accessibility_score)
        
        if accessible_selectors == 0 and len(steps) > 0:
            suggestions.append("Consider using ARIA attributes and semantic selectors")
            
        if keyboard_actions == 0 and len(steps) > 0:
            suggestions.append("Include keyboard navigation testing where applicable")
        
        details.update({
            "total_steps": len(steps),
            "accessible_selectors": accessible_selectors,
            "keyboard_actions": keyboard_actions
        })
        
        return QualityScore(
            dimension=QualityDimension.ACCESSIBILITY,
            score=score,
            issues=issues,
            suggestions=suggestions,
            details=details
        )
    
    def _is_robust_selector(self, selector: str) -> bool:
        """Check if a selector is robust for automation."""
        if not selector:
            return False
            
        # Prefer data-testid, id, and semantic selectors
        robust_patterns = [
            r'^\[data-testid=',
            r'^#[\w\-_]+$',
            r'^text=',
            r'role=',
            r'aria-label='
        ]
        
        return any(re.match(pattern, selector) for pattern in robust_patterns)
    
    def _determine_quality_gate(self, overall_score: float) -> QualityGate:
        """Determine quality gate based on overall score."""
        for gate, threshold in self.quality_thresholds.items():
            if overall_score >= threshold:
                return gate
        return QualityGate.FAILED
    
    def _identify_critical_issues(self, dimension_scores: Dict[QualityDimension, QualityScore]) -> List[str]:
        """Identify critical issues that must be addressed."""
        critical_issues = []
        
        for dimension, score in dimension_scores.items():
            if score.score < 60:  # Critical threshold
                critical_issues.extend([f"[{dimension.value.upper()}] {issue}" for issue in score.issues])
        
        return critical_issues
    
    def _generate_improvement_plan(self, dimension_scores: Dict[QualityDimension, QualityScore]) -> List[str]:
        """Generate prioritized improvement plan."""
        improvement_plan = []
        
        # Sort dimensions by score (lowest first)
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1].score)
        
        for dimension, score in sorted_dimensions:
            if score.score < 80:  # Needs improvement
                improvement_plan.extend(score.suggestions)
        
        return improvement_plan
    
    def generate_quality_report(self, assessment: QualityAssessment) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        return {
            "summary": {
                "test_id": assessment.test_id,
                "overall_score": round(assessment.overall_score, 2),
                "weighted_score": round(assessment.weighted_score, 2),
                "quality_gate": assessment.quality_gate.value,
                "production_ready": assessment.production_ready,
                "assessment_date": assessment.assessment_timestamp
            },
            "dimension_scores": {
                dimension.value: {
                    "score": round(score.score, 2),
                    "percentage": round(score.percentage, 2),
                    "grade": score.grade,
                    "issues_count": len(score.issues),
                    "suggestions_count": len(score.suggestions)
                }
                for dimension, score in assessment.dimension_scores.items()
            },
            "critical_issues": assessment.critical_issues,
            "improvement_plan": assessment.improvement_plan,
            "recommendations": {
                "immediate_actions": assessment.improvement_plan[:3],
                "long_term_goals": assessment.improvement_plan[3:],
                "next_review_in_days": 7 if assessment.overall_score < 70 else 30
            }
        }
    
    def batch_assess_test_cases(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform batch quality assessment on multiple test cases."""
        assessments = []
        
        for test_case in test_cases:
            assessment = self.assess_test_case(test_case)
            assessments.append(assessment)
        
        # Generate batch statistics
        overall_scores = [a.overall_score for a in assessments]
        
        batch_stats = {
            "total_test_cases": len(assessments),
            "average_score": sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            "production_ready_count": sum(1 for a in assessments if a.production_ready),
            "quality_gate_distribution": {},
            "common_issues": self._identify_common_issues(assessments),
            "improvement_recommendations": self._batch_improvement_recommendations(assessments)
        }
        
        # Calculate quality gate distribution
        for gate in QualityGate:
            batch_stats["quality_gate_distribution"][gate.value] = sum(
                1 for a in assessments if a.quality_gate == gate
            )
        
        return {
            "batch_statistics": batch_stats,
            "individual_assessments": [self.generate_quality_report(a) for a in assessments],
            "generated_at": datetime.now().isoformat()
        }
    
    def _identify_common_issues(self, assessments: List[QualityAssessment]) -> List[str]:
        """Identify common issues across multiple assessments."""
        issue_counts = {}
        
        for assessment in assessments:
            for issue in assessment.critical_issues:
                # Extract issue type (remove dimension prefix)
                clean_issue = re.sub(r'^\[.*?\]\s*', '', issue)
                issue_counts[clean_issue] = issue_counts.get(clean_issue, 0) + 1
        
        # Return issues that appear in more than 25% of test cases
        threshold = len(assessments) * 0.25
        return [issue for issue, count in issue_counts.items() if count >= threshold]
    
    def _batch_improvement_recommendations(self, assessments: List[QualityAssessment]) -> List[str]:
        """Generate batch-level improvement recommendations."""
        recommendations = []
        
        # Analyze dimension performance across all test cases
        dimension_averages = {}
        for dimension in QualityDimension:
            scores = [a.dimension_scores[dimension].score for a in assessments 
                     if dimension in a.dimension_scores]
            if scores:
                dimension_averages[dimension] = sum(scores) / len(scores)
        
        # Identify weakest dimensions
        weak_dimensions = [dim for dim, avg in dimension_averages.items() if avg < 70]
        
        if weak_dimensions:
            recommendations.append(f"Focus on improving: {', '.join([d.value for d in weak_dimensions])}")
        
        # Check production readiness
        production_ready_percent = sum(1 for a in assessments if a.production_ready) / len(assessments) * 100
        if production_ready_percent < 70:
            recommendations.append("Implement quality gates to increase production readiness")
        
        return recommendations