#!/usr/bin/env python3
"""
Simple test to validate the POC fixes without requiring browser execution.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from exploratory_qa_generator import ExploratoryQAGenerator, EXPLORATORY_QA_PROMPT, test_accumulator

def test_prompt_fixes():
    """Test that the system prompt fixes are applied."""
    print("🧪 Testing system prompt fixes...")
    
    # Check that the prompt contains the critical override language
    assert "CRITICAL OVERRIDE" in EXPLORATORY_QA_PROMPT
    assert "NOT trying to complete any specific goal" in EXPLORATORY_QA_PROMPT
    assert "EXPLORATION MODE" in EXPLORATORY_QA_PROMPT
    assert "Continue exploring until max_steps is reached" in EXPLORATORY_QA_PROMPT
    
    print("✅ System prompt contains critical override language")

def test_generator_initialization():
    """Test that the generator can be initialized with mock LLM."""
    print("🧪 Testing generator initialization...")
    
    try:
        generator = ExploratoryQAGenerator(use_mock_llm=True)
        assert generator.use_mock_llm == True
        assert hasattr(generator, 'session_id')
        print(f"✅ Generator initialized successfully with session: {generator.session_id}")
    except Exception as e:
        print(f"❌ Generator initialization failed: {e}")
        raise

def test_hook_function():
    """Test that the hook function exists and can be called safely."""
    print("🧪 Testing hook function...")
    
    from exploratory_qa_generator import exploratory_step_hook
    
    # Clear accumulator
    test_accumulator.clear()
    
    # Create a mock agent object
    class MockAgent:
        def __init__(self):
            self.history = []
    
    mock_agent = MockAgent()
    
    # Test hook with empty history (should not crash)
    try:
        import asyncio
        asyncio.run(exploratory_step_hook(mock_agent))
        print("✅ Hook function handles empty history gracefully")
    except Exception as e:
        print(f"❌ Hook function failed with empty history: {e}")
        raise

def test_max_steps_increased():
    """Test that default max_steps has been increased."""
    print("🧪 Testing max_steps default...")
    
    generator = ExploratoryQAGenerator(use_mock_llm=True)
    
    # Check the function signature default
    import inspect
    sig = inspect.signature(generator.generate_exploratory_tests)
    max_steps_param = sig.parameters['max_steps']
    
    assert max_steps_param.default >= 20, f"Expected max_steps >= 20, got {max_steps_param.default}"
    print(f"✅ Default max_steps is now {max_steps_param.default}")

def test_selector_generation():
    """Test that selector generation improvements work."""
    print("🧪 Testing selector generation...")
    
    from test_models import SelectorExtractor
    
    # Test fallback selector generation
    selector = SelectorExtractor.get_fallback_selector('click', {'index': 1})
    assert selector != 'body'  # Should be more specific
    assert 'button' in selector or 'btn' in selector
    
    print(f"✅ Generated specific selector for click action: {selector}")
    
    # Test type selector with context
    selector = SelectorExtractor.get_fallback_selector('type', {'text': 'username'})
    assert 'username' in selector or 'email' in selector
    
    print(f"✅ Generated contextual selector for type action: {selector}")

def run_all_tests():
    """Run all validation tests."""
    print("🚀 Running POC validation tests...")
    print("=" * 50)
    
    tests = [
        test_prompt_fixes,
        test_generator_initialization,
        test_hook_function,
        test_max_steps_increased,
        test_selector_generation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            failed += 1
        print()  # Empty line between tests
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All POC fixes validated successfully!")
        return True
    else:
        print("⚠️  Some tests failed - fixes need review")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)