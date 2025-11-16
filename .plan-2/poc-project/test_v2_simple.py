#!/usr/bin/env python3
"""
Simple Test Script for Exploratory QA Generator V2 - No Unicode Characters

This script validates the new implementation that uses Controller and extracted_content.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from exploratory_qa_generator_v2 import ExploratoryQAGenerator, TestCaseManager, GenerateTestCasesAction


async def test_test_case_manager():
	"""Test the TestCaseManager functionality."""
	print("\n" + "="*60)
	print("TEST 1: TestCaseManager Functionality")
	print("="*60)
	
	session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
	manager = TestCaseManager(session_id, output_dir="./outputs/test_cases")
	
	# Import TestCaseStep
	from exploratory_qa_generator_v2 import TestCaseStep
	
	step1 = TestCaseStep(
		step_number=1,
		url="https://test.example.com",
		timestamp=datetime.now().isoformat(),
		test_cases="""Scenario: Login with valid credentials
  Given the login page is displayed
  When user enters valid username and password
  And clicks the login button
  Then user should be redirected to dashboard""",
		incomplete_test_cases="""Scenario: [INCOMPLETE] Password reset functionality
  Given user clicks forgot password
  When [NEEDS VERIFICATION] reset form appears
  Then [INCOMPLETE] password reset email is sent""",
		extracted_content='{"complete_test_cases": "test data", "incomplete_test_cases": "incomplete data"}'
	)
	
	await manager.add_step(step1)
	
	incomplete_cases = await manager.get_incomplete_cases_for_injection()
	print(f"[PASS] Incomplete cases for injection: {len(incomplete_cases)} characters")
	
	summary = await manager.get_summary()
	print(f"[PASS] Test session summary generated successfully")
	
	return True


async def test_generate_test_cases_action():
	"""Test the GenerateTestCasesAction validation."""
	print("\n" + "="*60)
	print("TEST 2: GenerateTestCasesAction Validation")
	print("="*60)
	
	try:
		valid_action = GenerateTestCasesAction(
			complete_test_cases="""Scenario: Valid form submission
  Given the form is displayed
  When user fills all required fields
  And clicks submit
  Then success message appears""",
			incomplete_test_cases="""Scenario: [INCOMPLETE] Email verification
  Given user submits form
  When [NEEDS VERIFICATION] email is sent
  Then [INCOMPLETE] verification process completes"""
		)
		print("[PASS] Valid action parameters accepted")
	except Exception as e:
		print(f"[FAIL] Valid parameters rejected: {e}")
		return False
	
	try:
		invalid_action = GenerateTestCasesAction(
			complete_test_cases="Too short",
			incomplete_test_cases=""
		)
		print("[FAIL] Invalid parameters accepted (should have failed)")
		return False
	except Exception as e:
		print(f"[PASS] Invalid parameters correctly rejected")
	
	return True


async def test_controller_creation():
	"""Test Controller creation and action registration."""
	print("\n" + "="*60)
	print("TEST 3: Controller Creation and Action Registration")
	print("="*60)
	
	try:
		from exploratory_qa_generator_v2 import create_test_generation_controller
		
		controller = create_test_generation_controller()
		print("[PASS] Controller created successfully")
		
		# Access actions from the registry.registry.actions dictionary
		actions_dict = controller.registry.registry.actions
		action_names = list(actions_dict.keys())
		
		if "generate_test_cases" in action_names:
			print("[PASS] generate_test_cases action registered in controller")
		else:
			print(f"[FAIL] generate_test_cases action not found. Available: {action_names}")
			return False
		
		return True
		
	except Exception as e:
		print(f"[FAIL] Controller creation failed: {e}")
		return False


async def test_environment_setup():
	"""Test environment setup and configuration."""
	print("\n" + "="*60)
	print("TEST 4: Environment Setup")
	print("="*60)
	
	required_env_vars = [
		"BROWSER_USE_LLM_API_KEY",
		"BROWSER_USE_LLM_MODEL"
	]
	
	missing_vars = []
	for var in required_env_vars:
		if not os.getenv(var):
			missing_vars.append(var)
	
	if missing_vars:
		print(f"[WARN] Missing environment variables: {missing_vars}")
		print("       This will prevent LLM initialization but won't fail core tests")
	else:
		print("[PASS] All required environment variables present")
	
	try:
		generator = ExploratoryQAGenerator(use_mock_llm=True)
		print("[PASS] ExploratoryQAGenerator initialization with mock LLM successful")
	except Exception as e:
		print(f"[FAIL] ExploratoryQAGenerator initialization failed: {e}")
		return False
	
	output_dir = Path("./outputs/test_cases")
	if output_dir.exists():
		print(f"[PASS] Output directory exists: {output_dir}")
	else:
		print(f"[FAIL] Output directory not created: {output_dir}")
		return False
	
	return True


async def run_integration_test():
	"""Run a limited integration test with mock LLM."""
	print("\n" + "="*60)
	print("TEST 5: Limited Integration Test (Mock LLM)")
	print("="*60)
	
	try:
		generator = ExploratoryQAGenerator(use_mock_llm=True)
		print("[PASS] ExploratoryQAGenerator created with Controller architecture")
		
		if hasattr(generator, 'controller') and generator.controller is not None:
			print("[PASS] Controller properly initialized")
			
			actions_dict = generator.controller.registry.registry.actions
			action_names = list(actions_dict.keys())
			
			if "generate_test_cases" in action_names:
				print("[PASS] generate_test_cases action available in controller")
			else:
				print(f"[FAIL] generate_test_cases action missing: {action_names}")
				return False
		else:
			print("[FAIL] Controller not initialized")
			return False
		
		print("[PASS] Integration test passed (mock environment)")
		return True
		
	except Exception as e:
		print(f"[FAIL] Integration test failed: {e}")
		import traceback
		traceback.print_exc()
		return False


async def main():
	"""Run all tests."""
	print("STARTING COMPREHENSIVE TEST SUITE FOR V2 IMPLEMENTATION")
	print("=" * 80)
	
	test_results = []
	
	tests = [
		("TestCaseManager Functionality", test_test_case_manager),
		("GenerateTestCasesAction Validation", test_generate_test_cases_action),
		("Controller Creation", test_controller_creation),
		("Environment Setup", test_environment_setup),
		("Integration Test", run_integration_test)
	]
	
	for test_name, test_func in tests:
		try:
			print(f"\n=> Running: {test_name}")
			result = await test_func()
			test_results.append((test_name, result))
			
			if result:
				print(f"[PASS] {test_name}")
			else:
				print(f"[FAIL] {test_name}")
				
		except Exception as e:
			print(f"[FAIL] {test_name}: FAILED with exception: {e}")
			test_results.append((test_name, False))
	
	# Summary
	print("\n" + "=" * 80)
	print("TEST SUMMARY")
	print("=" * 80)
	
	passed = 0
	total = len(test_results)
	
	for test_name, result in test_results:
		status = "[PASS]" if result else "[FAIL]"
		print(f"{test_name:<40} {status}")
		if result:
			passed += 1
	
	print(f"\nOverall Result: {passed}/{total} tests passed")
	
	if passed == total:
		print("\nALL TESTS PASSED! V2 Implementation is ready for use.")
		
		print("\nNEXT STEPS:")
		print("1. Run with real environment variables for full testing")
		print("2. Test with actual websites (e.g., saucedemo.com)")
		print("3. Validate generated test files in ./outputs/test_cases/")
		print("4. Check extracted_content in ActionResult objects")
		
		return True
	else:
		print(f"\nWARNING: {total - passed} tests failed. Review the issues above.")
		return False


if __name__ == "__main__":
	# Change to the correct directory
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	# Run the test suite
	success = asyncio.run(main())
	
	# Exit with appropriate code
	sys.exit(0 if success else 1)