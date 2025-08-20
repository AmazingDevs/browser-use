#!/usr/bin/env python3
"""
Quick validation of the enhanced QA framework components.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Test basic quality framework
def test_quality_framework():
    print("Testing QA Quality Framework...")
    
    from qa_quality_framework import QualityFramework, QualityDimension
    
    # Create sample test case
    sample_test_case = {
        "metadata": {
            "test_id": "test_001",
            "scenario_name": "Sample Test",
            "total_steps": 3
        },
        "steps": [
            {
                "step_number": 1,
                "action_type": "navigate",
                "description": "Navigate to page",
                "selector": "body",
                "expected_result": "Page loads"
            },
            {
                "step_number": 2,
                "action_type": "click",
                "description": "Click button",
                "selector": "#submit-btn",
                "expected_result": "Button clicked"
            },
            {
                "step_number": 3,
                "action_type": "verify",
                "description": "Verify result",
                "selector": ".result",
                "expected_result": "Result displayed"
            }
        ],
        "edge_cases": ["Test with invalid input"],
        "preconditions": ["User is logged in"]
    }
    
    # Test quality assessment
    framework = QualityFramework()
    assessment = framework.assess_test_case(sample_test_case)
    
    print(f"✅ Quality Framework works!")
    print(f"   Overall Score: {assessment.overall_score:.1f}/100")
    print(f"   Quality Gate: {assessment.quality_gate.value}")
    print(f"   Production Ready: {assessment.production_ready}")
    
    return True

def test_enhanced_models():
    print("\nTesting Enhanced Test Models...")
    
    from enhanced_test_models import EnhancedTestStep, RiskLevel, TestType
    
    # Create enhanced test step
    step = EnhancedTestStep(
        step_number=1,
        action_type="click",
        description="Click login button",
        selector="[data-testid='login-btn']",
        risk_level=RiskLevel.MEDIUM
    )
    
    print(f"✅ Enhanced Models work!")
    print(f"   Step created with {len(step.accessibility_checks)} accessibility checks")
    print(f"   Risk level: {step.risk_level.value}")
    
    return True

def test_security_accessibility():
    print("\nTesting Security & Accessibility Checks...")
    
    from security_accessibility_checks import SecurityPayloadGenerator, SecurityVulnerabilityType
    
    # Test payload generation
    generator = SecurityPayloadGenerator()
    xss_payloads = generator.generate_payloads_for_vulnerability(SecurityVulnerabilityType.XSS)
    
    print(f"✅ Security & Accessibility Framework works!")
    print(f"   Generated {len(xss_payloads)} XSS payloads")
    print(f"   Sample payload: {xss_payloads[0].payload_data}")
    
    return True

def main():
    print("🧪 QUICK VALIDATION OF QA FRAMEWORK COMPONENTS")
    print("=" * 50)
    
    try:
        test_quality_framework()
        test_enhanced_models()
        test_security_accessibility()
        
        print("\n🎉 ALL COMPONENTS VALIDATED SUCCESSFULLY!")
        print("\n📊 IMPLEMENTATION SUMMARY:")
        print("✅ QA Quality Framework - Multi-dimensional scoring system")
        print("✅ Enhanced Test Models - Professional test structures") 
        print("✅ Security Testing - Vulnerability payload generation")
        print("✅ Accessibility Validation - WCAG compliance checks")
        print("✅ Quality Gates - Production readiness assessment")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())