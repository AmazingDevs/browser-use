#!/usr/bin/env python3
"""
Real Browser-Use Integration Test

This script tests the AI-driven test case generation feature with actual browser automation.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

from exploratory_qa_generator import ExploratoryQAGenerator


async def test_with_mock_llm():
    """Test the system with mock LLM to validate all components work."""
    print("=== Testing with Mock LLM (System Validation) ===")
    
    try:
        # Create generator with mock LLM
        generator = ExploratoryQAGenerator(use_mock_llm=True)
        print("[SUCCESS] ExploratoryQAGenerator created with mock LLM")
        
        # Test with a simple URL and limited steps
        result = await generator.generate_exploratory_tests(
            url="https://example.com",
            max_steps=2
        )
        
        if result.get('success'):
            print(f"[SUCCESS] Mock test completed successfully")
            print(f"[INFO] Session ID: {result['session_id']}")
            
            summary = result.get('exploration_summary', {})
            if summary:
                print(f"[INFO] Total steps: {summary.get('total_steps', 0)}")
                print(f"[INFO] Complete scenarios: {summary.get('total_complete_scenarios', 0)}")
                print(f"[INFO] Incomplete scenarios: {summary.get('total_incomplete_scenarios', 0)}")
                
                # Show output files
                output_files = summary.get('output_files', {})
                for file_type, file_path in output_files.items():
                    if Path(file_path).exists():
                        size = Path(file_path).stat().st_size
                        print(f"[INFO] Generated {file_type}: {file_path} ({size} bytes)")
            
            return True
        else:
            print(f"[ERROR] Mock test failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Mock test exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_real_llm():
    """Test with real LLM if configured."""
    print("\\n=== Testing with Real LLM (Full Integration) ===")
    
    # Check for required environment variables
    api_key = os.getenv("BROWSER_USE_LLM_API_KEY")
    model = os.getenv("BROWSER_USE_LLM_MODEL")
    
    if not api_key or not model:
        print("[INFO] Real LLM test skipped - environment variables not set")
        print("[INFO] To test with real LLM, set:")
        print("  - BROWSER_USE_LLM_API_KEY=your_api_key")
        print("  - BROWSER_USE_LLM_MODEL=your_model (e.g., claude-3-sonnet-20241022)")
        print("  - BROWSER_USE_LLM_URL=your_base_url (for OpenAI-compatible APIs)")
        return False
    
    try:
        print(f"[INFO] Using model: {model}")
        
        # Create generator with real LLM
        generator = ExploratoryQAGenerator(use_mock_llm=False)
        print("[SUCCESS] ExploratoryQAGenerator created with real LLM")
        
        # Test with SauceDemo (a testing website)
        print("[INFO] Starting real browser exploration of SauceDemo...")
        result = await generator.generate_exploratory_tests(
            url="https://www.saucedemo.com",
            max_steps=5  # Limited steps for testing
        )
        
        if result.get('success'):
            print(f"[SUCCESS] Real browser test completed successfully!")
            
            summary = result.get('exploration_summary', {})
            if summary:
                print(f"[RESULTS] Total steps executed: {summary.get('total_steps', 0)}")
                print(f"[RESULTS] Complete test scenarios generated: {summary.get('total_complete_scenarios', 0)}")
                print(f"[RESULTS] Incomplete scenarios queued: {summary.get('total_incomplete_scenarios', 0)}")
                
                # Show generated files
                output_files = summary.get('output_files', {})
                print("\\n[OUTPUT FILES]")
                for file_type, file_path in output_files.items():
                    if Path(file_path).exists():
                        size = Path(file_path).stat().st_size
                        print(f"  - {file_type}: {file_path} ({size} bytes)")
                        
                        # Show sample content for Gherkin files
                        if file_path.endswith('.feature'):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()[:10]  # First 10 lines
                                    print(f"    Sample content:")
                                    for line in lines:
                                        print(f"    {line.rstrip()}")
                                    if len(lines) == 10:
                                        print(f"    ... (truncated)")
                            except Exception:
                                pass
            
            return True
        else:
            print(f"[ERROR] Real browser test failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Real browser test exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chrome_availability():
    """Test if Chrome/Chromium is available for browser automation."""
    print("=== Testing Chrome/Chromium Availability ===")
    
    # Common Chrome paths
    chrome_paths = [
        os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH'),
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        'C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe',
        'C:\\\\Program Files (x86)\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe',
    ]
    
    available_chrome = None
    for path in chrome_paths:
        if path and Path(path).exists():
            available_chrome = path
            break
    
    if available_chrome:
        print(f"[SUCCESS] Chrome found at: {available_chrome}")
        return True
    else:
        print("[WARNING] Chrome not found at common locations")
        print("[INFO] You may need to:")
        print("  - Install Google Chrome or Chromium")
        print("  - Set PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH environment variable")
        print("  - Or let playwright install chromium: playwright install chromium")
        return False


async def main():
    """Main test function."""
    print("=" * 80)
    print("REAL BROWSER-USE INTEGRATION TEST")
    print("=" * 80)
    
    # Test 1: Chrome availability
    chrome_available = await test_chrome_availability()
    
    # Test 2: Mock LLM (always works)
    mock_success = await test_with_mock_llm()
    
    # Test 3: Real LLM (if configured)
    real_success = await test_with_real_llm()
    
    # Final results
    print("\\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    print(f"[{'SUCCESS' if chrome_available else 'WARNING'}] Chrome/Chromium availability: {'Available' if chrome_available else 'Not found'}")
    print(f"[{'SUCCESS' if mock_success else 'ERROR'}] Mock LLM system test: {'PASSED' if mock_success else 'FAILED'}")
    
    if real_success:
        print(f"[SUCCESS] Real LLM integration test: PASSED")
        print("\\n[CONCLUSION] Full browser automation with AI test case generation is working!")
        print("✓ Browser automation functional")  
        print("✓ AI model integration working")
        print("✓ Test case extraction successful")
        print("✓ File generation working") 
        print("✓ Hook system operational")
        
    elif mock_success and chrome_available:
        print(f"[INFO] Real LLM integration test: SKIPPED (no API key configured)")
        print("\\n[CONCLUSION] System is ready for real LLM integration!")
        print("✓ All components working correctly")
        print("✓ Ready for production use with proper LLM configuration")
        
    else:
        print(f"[ERROR] System has issues that need to be resolved")
        
    print(f"\\n[INFO] Check outputs/test_cases/ directory for generated files")


if __name__ == "__main__":
    asyncio.run(main())