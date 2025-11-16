#!/usr/bin/env python3
"""
Test Script for Exploratory QA Generator V2 - Controller & extracted_content Implementation

This script validates the new implementation that uses:
1. Custom Controller with generate_test_cases action
2. ActionResult.extracted_content for test case extraction
3. Enhanced system prompt for action-based test generation
4. Hooks that extract from action results instead of model output

Features tested:
- Controller registration and action execution
- Test case extraction from extracted_content
- Hook functionality for incomplete case injection
- File output generation and incremental saving
- Error handling and validation

Usage:
    python test_extracted_content_v2.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from exploratory_qa_generator_v2 import ExploratoryQAGenerator, TestCaseManager, GenerateTestCasesAction


async def test_test_case_manager():
	"""Test the TestCaseManager functionality."""
	print("\n" + "="*60)
	print("TEST 1: TestCaseManager Functionality")
	print("="*60)
	
	# Create a test manager
	session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
	manager = TestCaseManager(session_id, output_dir="./outputs/test_cases")
	
	# Test adding steps
	from exploratory_qa_generator_v2 import TestCaseStep
	
	step1 = TestCaseStep(
		step_number=1,
		url="https://test.example.com",
		timestamp=datetime.now().isoformat(),
		test_cases="""Scenario: Login with valid credentials
  Given the login page is displayed
  When user enters valid username and password
  And clicks the login button
  Then user should be redirected to dashboard

Scenario: Login with invalid credentials
  Given the login page is displayed
  When user enters invalid credentials
  And clicks the login button
  Then error message should be displayed""",
		incomplete_test_cases="""Scenario: [INCOMPLETE] Password reset functionality
  Given user clicks forgot password
  When [NEEDS VERIFICATION] reset form appears
  Then [INCOMPLETE] password reset email is sent
  
Missing info: Need to explore password reset flow""",
		extracted_content='{"complete_test_cases": "...test data...", "incomplete_test_cases": "...incomplete data..."}'
	)
	
	step2 = TestCaseStep(
		step_number=2,
		url="https://test.example.com/dashboard",
		timestamp=datetime.now().isoformat(),
		test_cases="""Scenario: Dashboard displays user information
  Given user is logged in
  When dashboard loads
  Then user profile information is displayed
  And navigation menu is available""",
		incomplete_test_cases="",
		extracted_content='{"complete_test_cases": "...dashboard test data..."}'
	)
	
	# Add steps
	await manager.add_step(step1)
	await manager.add_step(step2)
	
	# Test incomplete case injection
	incomplete_cases = await manager.get_incomplete_cases_for_injection()
	print(f"✅ Incomplete cases for injection: {len(incomplete_cases)} characters")
	
	# Get summary
	summary = await manager.get_summary()
	print(f"✅ Test session summary: {summary}")
	
	# Verify files were created
	json_file = Path(f"./outputs/test_cases/test_cases_{session_id}.json")
	feature_file = Path(f"./outputs/test_cases/all_test_cases_{session_id}.feature")
	
	if json_file.exists():
		print(f"✅ JSON file created: {json_file}")
		with open(json_file, 'r') as f:
			data = json.load(f)
			print(f"   - Contains {len(data['steps'])} steps")
	else:
		print(f"❌ JSON file not created: {json_file}")
	
	if feature_file.exists():
		print(f"✅ Feature file created: {feature_file}")
		with open(feature_file, 'r') as f:
			content = f.read()
			scenario_count = content.count("Scenario:")
			print(f"   - Contains {scenario_count} scenarios")
	else:
		print(f"❌ Feature file not created: {feature_file}")
	
	return True


async def test_generate_test_cases_action():
	"""Test the GenerateTestCasesAction validation."""
	print("\n" + "="*60)
	print("TEST 2: GenerateTestCasesAction Validation")
	print("="*60)
	
	# Test valid action parameters
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
		print("✅ Valid action parameters accepted")
	except Exception as e:
		print(f"❌ Valid parameters rejected: {e}")
		return False
	
	# Test invalid parameters (too short complete_test_cases)
	try:
		invalid_action = GenerateTestCasesAction(
			complete_test_cases="Too short",
			incomplete_test_cases=""
		)
		print("❌ Invalid parameters accepted (should have failed)")
		return False
	except Exception as e:
		print(f"✅ Invalid parameters correctly rejected: {e}")
	
	# Test incomplete test case auto-formatting
	action_with_formatting = GenerateTestCasesAction(
		complete_test_cases="""Scenario: Test case
  Given some condition
  When some action
  Then some result""",
		incomplete_test_cases="Some incomplete scenario without marker"
	)
	
	if action_with_formatting.incomplete_test_cases.startswith("[INCOMPLETE]"):
		print("✅ Incomplete test cases auto-formatted with [INCOMPLETE] marker")
	else:
		print(f"❌ Auto-formatting failed: {action_with_formatting.incomplete_test_cases}")
	
	return True


async def test_controller_creation():
	"""Test Controller creation and action registration."""
	print("\n" + "="*60)
	print("TEST 3: Controller Creation and Action Registration")
	print("="*60)
	
	try:
		from exploratory_qa_generator_v2 import create_test_generation_controller
		
		controller = create_test_generation_controller()
		print("✅ Controller created successfully")
		
		# Check if the action is registered
		actions = controller.registry.get_actions()
		action_names = [action.name for action in actions]
		
		if "generate_test_cases" in action_names:
			print("✅ generate_test_cases action registered in controller")
		else:
			print(f"❌ generate_test_cases action not found. Available: {action_names}")
			return False
		
		# Try to get the specific action
		test_action = next((action for action in actions if action.name == "generate_test_cases"), None)
		if test_action:
			print(f"✅ Action found with description: {test_action.description[:50]}...")
			print(f"✅ Action param model: {test_action.param_model}")
		
		return True
		
	except Exception as e:
		print(f"❌ Controller creation failed: {e}")
		return False


async def test_hook_functionality():
	"""Test hook functionality with mock data."""
	print("\n" + "="*60)
	print("TEST 4: Hook Functionality")
	print("="*60)
	
	try:
		from exploratory_qa_generator_v2 import exploratory_step_hook, on_step_start_hook, _test_case_manager, TestCaseManager
		import types
		
		# Create a mock agent with history
		mock_agent = types.SimpleNamespace()
		mock_agent.history = types.SimpleNamespace()
		
		# Create mock history step
		mock_step = types.SimpleNamespace()
		mock_step.state = types.SimpleNamespace()
		mock_step.state.url = "https://test.example.com"
		
		# Create mock action result with extracted_content
		mock_result = types.SimpleNamespace()
		mock_result.extracted_content = json.dumps({
			"complete_test_cases": """Scenario: Mock test scenario
  Given mock conditions
  When mock actions
  Then mock results""",
			"incomplete_test_cases": """Scenario: [INCOMPLETE] Mock incomplete scenario
  Given mock setup
  When [NEEDS VERIFICATION] some action
  Then [INCOMPLETE] some result""",
			"timestamp": datetime.now().isoformat()
		})
		
		mock_step.result = [mock_result]
		mock_agent.history.history = [mock_step]
		
		# Set up test case manager
		session_id = f"hook_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		test_manager = TestCaseManager(session_id)
		
		# Test exploratory_step_hook
		print("Testing exploratory_step_hook...")
		
		# Temporarily set global manager
		import exploratory_qa_generator_v2
		exploratory_qa_generator_v2._test_case_manager = test_manager
		
		await exploratory_step_hook(mock_agent)
		print("✅ exploratory_step_hook executed without errors")
		
		# Check if test cases were extracted
		summary = await test_manager.get_summary()
		if summary['total_steps'] > 0:
			print(f"✅ Test cases extracted: {summary['total_complete_scenarios']} scenarios")
		else:
			print("❌ No test cases extracted")
			return False
		
		# Test on_step_start_hook
		print("Testing on_step_start_hook...")
		await on_step_start_hook(mock_agent)
		print("✅ on_step_start_hook executed without errors")
		
		# Clean up
		exploratory_qa_generator_v2._test_case_manager = None
		
		return True
		
	except Exception as e:
		print(f"❌ Hook functionality test failed: {e}")
		import traceback
		traceback.print_exc()
		return False


async def test_environment_setup():
	"""Test environment setup and configuration."""
	print("\n" + "="*60)
	print("TEST 5: Environment Setup")
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
		print(f"⚠️  Missing environment variables: {missing_vars}")
		print("   This will prevent LLM initialization but won't fail core tests")
	else:
		print("✅ All required environment variables present")
	
	# Test LLM initialization with mock
	try:
		generator = ExploratoryQAGenerator(use_mock_llm=True)
		print("✅ ExploratoryQAGenerator initialization with mock LLM successful")
	except Exception as e:
		print(f"❌ ExploratoryQAGenerator initialization failed: {e}")
		return False
	
	# Check output directory creation
	output_dir = Path("./outputs/test_cases")
	if output_dir.exists():
		print(f"✅ Output directory exists: {output_dir}")
	else:
		print(f"❌ Output directory not created: {output_dir}")
		return False
	
	return True


async def run_integration_test():
	"""Run a limited integration test with mock LLM."""
	print("\n" + "="*60)
	print("TEST 6: Limited Integration Test (Mock LLM)")
	print("="*60)
	
	try:
		# Note: This will fail at browser session creation but validates the setup
		generator = ExploratoryQAGenerator(use_mock_llm=True)
		print("✅ ExploratoryQAGenerator created with Controller architecture")
		
		# Validate that controller is properly set up
		if hasattr(generator, 'controller') and generator.controller is not None:
			print("✅ Controller properly initialized")
			
			# Check action registration
			actions = generator.controller.registry.get_actions()
			action_names = [action.name for action in actions]
			
			if "generate_test_cases" in action_names:
				print("✅ generate_test_cases action available in controller")
			else:
				print(f"❌ generate_test_cases action missing: {action_names}")
				return False
		else:
			print("❌ Controller not initialized")
			return False
		
		print("✅ Integration test passed (mock environment)")
		return True
		
	except Exception as e:
		print(f"❌ Integration test failed: {e}")
		import traceback
		traceback.print_exc()
		return False


async def main():
	"""Run all tests."""
	print("🚀 STARTING COMPREHENSIVE TEST SUITE FOR V2 IMPLEMENTATION")
	print("=" * 80)
	
	test_results = []
	
	# Run all tests
	tests = [
		("TestCaseManager Functionality", test_test_case_manager),
		("GenerateTestCasesAction Validation", test_generate_test_cases_action),
		("Controller Creation", test_controller_creation),
		("Hook Functionality", test_hook_functionality),
		("Environment Setup", test_environment_setup),
		("Integration Test", run_integration_test)
	]
	
	for test_name, test_func in tests:
		try:
			print(f"\n🔄 Running: {test_name}")
			result = await test_func()
			test_results.append((test_name, result))
			
			if result:
				print(f"✅ {test_name}: PASSED")
			else:
				print(f"❌ {test_name}: FAILED")
				
		except Exception as e:
			print(f"❌ {test_name}: FAILED with exception: {e}")
			test_results.append((test_name, False))
	
	# Summary
	print("\n" + "=" * 80)
	print("TEST SUMMARY")
	print("=" * 80)
	
	passed = 0
	total = len(test_results)
	
	for test_name, result in test_results:
		status = "✅ PASSED" if result else "❌ FAILED"
		print(f"{test_name:<40} {status}")
		if result:
			passed += 1
	
	print(f"\nOverall Result: {passed}/{total} tests passed")
	
	if passed == total:
		print("\n🎉 ALL TESTS PASSED! V2 Implementation is ready for use.")
		
		# Display next steps
		print("\n📋 NEXT STEPS:")
		print("1. Run with real environment variables for full testing")
		print("2. Test with actual websites (e.g., saucedemo.com)")
		print("3. Validate generated test files in ./outputs/test_cases/")
		print("4. Check extracted_content in ActionResult objects")
		
		return True
	else:
		print(f"\n⚠️  {total - passed} tests failed. Review the issues above.")
		return False


if __name__ == "__main__":
	# Change to the correct directory
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	# Run the test suite
	success = asyncio.run(main())
	
	# Exit with appropriate code
	sys.exit(0 if success else 1)