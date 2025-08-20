#!/usr/bin/env python3
"""
Validation script for the Exploratory QA Test Case Generator POC.

This script validates the core functionality and integration of the POC
components without requiring external web resources.
"""

import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from exploratory_qa_generator import ExploratoryQAGenerator
from test_models import (
    ExploratoryTestStep, ExploratoryTestCase, 
    SelectorExtractor, TestCaseFormatter
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

class ValidationRunner:
    """Runs comprehensive validation of POC components."""
    
    def __init__(self):
        self.results = {
            'test_models': {'passed': 0, 'failed': 0, 'details': []},
            'selector_extraction': {'passed': 0, 'failed': 0, 'details': []},
            'test_case_formatting': {'passed': 0, 'failed': 0, 'details': []},
            'generator_integration': {'passed': 0, 'failed': 0, 'details': []},
            'error_handling': {'passed': 0, 'failed': 0, 'details': []}
        }
    
    def _log_test(self, category: str, test_name: str, success: bool, details: str = ""):
        """Log test result and update statistics."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"   {status} {test_name}")
        
        if details:
            logger.info(f"      {details}")
        
        if success:
            self.results[category]['passed'] += 1
        else:
            self.results[category]['failed'] += 1
        
        self.results[category]['details'].append({
            'test': test_name,
            'status': 'passed' if success else 'failed',
            'details': details
        })
    
    def validate_test_models(self):
        """Validate test data models."""
        logger.info("🔍 Validating Test Data Models...")
        
        # Test ExploratoryTestStep creation
        try:
            step = ExploratoryTestStep(
                step_number=1,
                action_type="click",
                description="Click login button",
                selector="[data-testid='login-btn']",
                expected_result="Login form appears",
                page_url="https://www.saucedemo.com"
            )
            
            self._log_test(
                'test_models', 
                'ExploratoryTestStep creation',
                True,
                f"Created step with action_type: {step.action_type}"
            )
            
            # Validate required fields
            required_fields = ['step_number', 'action_type', 'description', 'selector', 'expected_result', 'page_url']
            missing_fields = [field for field in required_fields if not hasattr(step, field)]
            
            self._log_test(
                'test_models',
                'Required fields validation',
                len(missing_fields) == 0,
                f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
            )
            
        except Exception as e:
            self._log_test('test_models', 'ExploratoryTestStep creation', False, str(e))
        
        # Test ExploratoryTestCase creation
        try:
            test_case = ExploratoryTestCase(
                test_id="test_001",
                scenario_name="Login Flow",
                steps=[step],
                discovered_elements=[{"type": "button", "selector": "[data-testid='login-btn']"}],
                edge_cases=["Empty credentials", "Invalid credentials"],
                coverage_metrics={"elements_tested": 1, "paths_explored": 1}
            )
            
            self._log_test(
                'test_models',
                'ExploratoryTestCase creation',
                True,
                f"Created test case with {len(test_case.steps)} steps"
            )
            
            # Test helper methods
            total_steps = test_case.get_total_steps()
            unique_pages = test_case.get_unique_pages()
            
            self._log_test(
                'test_models',
                'Helper methods',
                total_steps == 1 and len(unique_pages) == 1,
                f"Total steps: {total_steps}, Unique pages: {len(unique_pages)}"
            )
            
        except Exception as e:
            self._log_test('test_models', 'ExploratoryTestCase creation', False, str(e))
    
    def validate_selector_extraction(self):
        """Validate selector extraction functionality."""
        logger.info("🎯 Validating Selector Extraction...")
        
        extractor = SelectorExtractor()
        
        # Mock DOM state for testing
        mock_dom_state = Mock()
        mock_dom_state.dom_elements = [
            Mock(
                attributes={'data-testid': 'submit-button', 'id': 'btn-submit', 'class': 'btn primary'},
                text='Submit Form',
                tag_name='button'
            ),
            Mock(
                attributes={'id': 'email-input', 'type': 'email'},
                text='',
                tag_name='input'
            )
        ]
        
        # Test data-testid extraction (highest priority)
        try:
            selector = extractor.extract_selector_from_dom_state(mock_dom_state)
            expected_selector = "[data-testid='submit-button']"
            
            self._log_test(
                'selector_extraction',
                'Data-testid selector extraction',
                selector == expected_selector,
                f"Expected: {expected_selector}, Got: {selector}"
            )
        except Exception as e:
            self._log_test('selector_extraction', 'Data-testid selector extraction', False, str(e))
        
        # Test CSS selector building
        try:
            mock_element = Mock(
                tag_name='button',
                attributes={'class': 'btn primary', 'type': 'submit'}
            )
            
            css_selector = extractor._build_css_selector(mock_element)
            expected_css = 'button.btn.primary'
            
            self._log_test(
                'selector_extraction',
                'CSS selector building',
                css_selector == expected_css,
                f"Expected: {expected_css}, Got: {css_selector}"
            )
        except Exception as e:
            self._log_test('selector_extraction', 'CSS selector building', False, str(e))
        
        # Test text selector
        try:
            text_selector = extractor._build_text_selector("Click Here")
            expected_text = "text='Click Here'"
            
            self._log_test(
                'selector_extraction',
                'Text selector building',
                text_selector == expected_text,
                f"Expected: {expected_text}, Got: {text_selector}"
            )
        except Exception as e:
            self._log_test('selector_extraction', 'Text selector building', False, str(e))
        
        # Test error handling with invalid input
        try:
            invalid_selector = extractor.extract_selector_from_dom_state(None)
            
            self._log_test(
                'selector_extraction',
                'Error handling for invalid input',
                invalid_selector is None,
                "Gracefully handled None input"
            )
        except Exception as e:
            self._log_test('selector_extraction', 'Error handling for invalid input', False, str(e))
    
    def validate_test_case_formatting(self):
        """Validate test case formatting functionality."""
        logger.info("🎭 Validating Test Case Formatting...")
        
        formatter = TestCaseFormatter()
        
        # Create sample test case
        step1 = ExploratoryTestStep(
            step_number=1,
            action_type="navigate",
            description="Navigate to login page",
            selector="",
            expected_result="Login page loads",
            page_url="https://www.saucedemo.com/login"
        )
        
        step2 = ExploratoryTestStep(
            step_number=2,
            action_type="type",
            description="Enter username",
            selector="#username",
            input_data="testuser@example.com",
            expected_result="Username field populated",
            page_url="https://www.saucedemo.com/login"
        )
        
        test_case = ExploratoryTestCase(
            test_id="login_test_001",
            scenario_name="Login Flow Validation",
            steps=[step1, step2],
            discovered_elements=[],
            edge_cases=[],
            coverage_metrics={}
        )
        
        # Test Playwright script generation
        try:
            script = formatter.to_playwright_script(test_case)
            
            # Verify key components in script
            required_components = [
                "async def test_login_flow_validation",
                "await page.goto",
                "await page.fill",
                "import asyncio",
                "from playwright.async_api import async_playwright"
            ]
            
            missing_components = [comp for comp in required_components if comp not in script]
            
            self._log_test(
                'test_case_formatting',
                'Playwright script generation',
                len(missing_components) == 0,
                f"Missing components: {missing_components}" if missing_components else "All components present"
            )
            
        except Exception as e:
            self._log_test('test_case_formatting', 'Playwright script generation', False, str(e))
        
        # Test JSON export
        try:
            json_data = formatter.to_json(test_case)
            
            # Verify JSON structure
            required_keys = ['metadata', 'steps', 'discovered_elements', 'edge_cases']
            missing_keys = [key for key in required_keys if key not in json_data]
            
            self._log_test(
                'test_case_formatting',
                'JSON export',
                len(missing_keys) == 0 and len(json_data['steps']) == 2,
                f"Missing keys: {missing_keys}" if missing_keys else f"JSON with {len(json_data['steps'])} steps"
            )
            
        except Exception as e:
            self._log_test('test_case_formatting', 'JSON export', False, str(e))
        
        # Test batch processing
        try:
            batch_json = formatter.batch_to_json([test_case])
            
            self._log_test(
                'test_case_formatting',
                'Batch JSON processing',
                'test_cases' in batch_json and len(batch_json['test_cases']) == 1,
                f"Batch contains {len(batch_json.get('test_cases', []))} test cases"
            )
            
        except Exception as e:
            self._log_test('test_case_formatting', 'Batch JSON processing', False, str(e))
    
    def validate_generator_integration(self):
        """Validate generator integration and configuration."""
        logger.info("🔧 Validating Generator Integration...")
        
        # Test initialization
        try:
            generator = ExploratoryQAGenerator(
                timeout=30,
                use_mock_llm=True  # Use mock for validation
            )
            
            self._log_test(
                'generator_integration',
                'Generator initialization',
                generator.llm_provider in ["anthropic", "openai", "generic", "mock"] and generator.timeout == 30,
                f"Provider: {generator.llm_provider}, Timeout: {generator.timeout}"
            )
            
        except Exception as e:
            self._log_test('generator_integration', 'Generator initialization', False, str(e))
        
        # Test LLM configuration
        try:
            # Test with mock to avoid API calls
            generator = ExploratoryQAGenerator(use_mock_llm=True)
            llm_instance = generator._llm
            
            self._log_test(
                'generator_integration',
                'LLM configuration',
                llm_instance is not None,
                f"LLM instance type: {type(llm_instance).__name__}"
            )
            
        except Exception as e:
            self._log_test('generator_integration', 'LLM configuration', False, str(e))
        
        # Test test case formatting
        try:
            generator = ExploratoryQAGenerator(use_mock_llm=True)
            
            # Mock raw steps
            raw_steps = [
                {
                    'action_type': 'click',
                    'selector': '[data-testid="login"]',
                    'page_url': 'https://www.saucedemo.com',
                    'timestamp': '2024-01-01T10:00:00Z'
                }
            ]
            
            formatted = generator._format_test_cases(raw_steps)
            
            self._log_test(
                'generator_integration',
                'Test case formatting',
                'test_cases' in formatted and 'total_steps' in formatted,
                f"Formatted with {len(formatted.get('test_cases', []))} test cases"
            )
            
        except Exception as e:
            self._log_test('generator_integration', 'Test case formatting', False, str(e))
    
    def validate_error_handling(self):
        """Validate error handling capabilities."""
        logger.info("🛡️ Validating Error Handling...")
        
        # Test invalid LLM configuration
        try:
            # Mock environment without required variables
            import os
            original_api_key = os.environ.get('BROWSER_USE_LLM_API_KEY')
            original_model = os.environ.get('BROWSER_USE_LLM_MODEL')
            
            # Remove required environment variables
            if 'BROWSER_USE_LLM_API_KEY' in os.environ:
                del os.environ['BROWSER_USE_LLM_API_KEY']
            if 'BROWSER_USE_LLM_MODEL' in os.environ:
                del os.environ['BROWSER_USE_LLM_MODEL']
            
            try:
                generator = ExploratoryQAGenerator()
                self._log_test('error_handling', 'Invalid LLM configuration', False, "Should have raised error")
            except ValueError as e:
                self._log_test(
                    'error_handling', 
                    'Invalid LLM configuration', 
                    True, 
                    f"Correctly raised ValueError: {str(e)[:50]}..."
                )
            finally:
                # Restore environment variables
                if original_api_key:
                    os.environ['BROWSER_USE_LLM_API_KEY'] = original_api_key
                if original_model:
                    os.environ['BROWSER_USE_LLM_MODEL'] = original_model
        except Exception as e:
            self._log_test('error_handling', 'Invalid LLM provider', False, str(e))
        
        # Test selector extraction with invalid data
        try:
            extractor = SelectorExtractor()
            result = extractor.extract_selector_from_dom_state("invalid_data")
            
            self._log_test(
                'error_handling',
                'Selector extraction error handling',
                result is None,
                "Gracefully handled invalid DOM state"
            )
        except Exception as e:
            self._log_test('error_handling', 'Selector extraction error handling', False, str(e))
        
        # Test empty test case formatting
        try:
            formatter = TestCaseFormatter()
            empty_case = ExploratoryTestCase(
                test_id="empty_test",
                scenario_name="Empty Test",
                steps=[],
                discovered_elements=[],
                edge_cases=[],
                coverage_metrics={}
            )
            
            script = formatter.to_playwright_script(empty_case)
            
            self._log_test(
                'error_handling',
                'Empty test case formatting',
                "async def test_empty_test" in script,
                "Generated valid script for empty test case"
            )
        except Exception as e:
            self._log_test('error_handling', 'Empty test case formatting', False, str(e))
    
    async def run_validation(self):
        """Run all validation tests."""
        logger.info("🚀 Starting POC Validation")
        logger.info("=" * 50)
        
        # Run validation categories
        validation_methods = [
            self.validate_test_models,
            self.validate_selector_extraction,
            self.validate_test_case_formatting,
            self.validate_generator_integration,
            self.validate_error_handling
        ]
        
        for method in validation_methods:
            try:
                method()
            except Exception as e:
                logger.error(f"❌ Validation method {method.__name__} failed: {e}")
        
        # Generate summary
        self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """Generate validation summary."""
        logger.info("\n" + "=" * 50)
        logger.info("📊 VALIDATION SUMMARY")
        logger.info("=" * 50)
        
        total_passed = sum(cat['passed'] for cat in self.results.values())
        total_failed = sum(cat['failed'] for cat in self.results.values())
        total_tests = total_passed + total_failed
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"✅ Total Passed: {total_passed}")
        logger.info(f"❌ Total Failed: {total_failed}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        logger.info("")
        
        # Category breakdown
        for category, results in self.results.items():
            total_cat = results['passed'] + results['failed']
            cat_success = (results['passed'] / total_cat * 100) if total_cat > 0 else 0
            
            status_icon = "✅" if results['failed'] == 0 else "⚠️" if cat_success >= 75 else "❌"
            
            logger.info(f"{status_icon} {category.replace('_', ' ').title()}: "
                       f"{results['passed']}/{total_cat} ({cat_success:.0f}%)")
        
        # Save detailed results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        validation_file = output_dir / "validation_results.json"
        with open(validation_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'total_passed': total_passed,
                    'total_failed': total_failed,
                    'success_rate': success_rate
                },
                'categories': self.results
            }, f, indent=2)
        
        logger.info(f"\n💾 Detailed results saved to: {validation_file}")
        
        # Overall status
        if total_failed == 0:
            logger.info("\n🎉 ALL VALIDATIONS PASSED! POC is ready for use.")
        elif success_rate >= 75:
            logger.info(f"\n⚠️ Most validations passed ({success_rate:.1f}%). Review failed tests.")
        else:
            logger.info(f"\n❌ Multiple validations failed ({success_rate:.1f}%). Review implementation.")

async def main():
    """Main validation entry point."""
    print("🔍 POC Validation Runner")
    print("=" * 50)
    print("This script validates the core functionality of the")
    print("Exploratory QA Test Case Generator POC without requiring")
    print("external web resources or API keys.")
    print("=" * 50)
    
    # Create outputs directory
    Path("outputs").mkdir(exist_ok=True)
    
    # Run validation
    validator = ValidationRunner()
    results = await validator.run_validation()
    
    print("\n" + "=" * 50)
    print("🏁 VALIDATION COMPLETE")
    print("=" * 50)
    print("📋 Check logs above for detailed results")
    print("📁 Detailed results saved to 'outputs/validation_results.json'")
    print("=" * 50)
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    
    # Exit with appropriate code
    total_failed = sum(cat['failed'] for cat in results.values())
    exit(0 if total_failed == 0 else 1)