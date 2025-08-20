#!/usr/bin/env python3
"""
Test script for OpenRouter integration with DeepSeek model.

This script demonstrates how to use the POC with OpenRouter and DeepSeek
using the generic environment variable configuration.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, rely on system environment variables
    pass

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from exploratory_qa_generator import ExploratoryQAGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if the required environment variables are set."""
    required_vars = [
        'BROWSER_USE_LLM_URL',
        'BROWSER_USE_LLM_API_KEY', 
        'BROWSER_USE_LLM_MODEL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("Please set the following in your .env file:")
        logger.info("BROWSER_USE_LLM_URL=https://openrouter.ai/api/v1")
        logger.info("BROWSER_USE_LLM_API_KEY=your-openrouter-api-key")
        logger.info("BROWSER_USE_LLM_MODEL=deepseek/deepseek-r1-0528-qwen3-8b")
        return False
    
    logger.info("✅ Environment configuration check passed")
    logger.info(f"URL: {os.getenv('BROWSER_USE_LLM_URL')}")
    logger.info(f"Model: {os.getenv('BROWSER_USE_LLM_MODEL')}")
    logger.info(f"API Key: {'Set' if os.getenv('BROWSER_USE_LLM_API_KEY') else 'Not set'}")
    
    return True

async def test_llm_initialization():
    """Test LLM initialization with OpenRouter configuration."""
    logger.info("🔧 Testing LLM Initialization...")
    
    try:
        # Initialize the generator
        generator = ExploratoryQAGenerator(timeout=60)
        
        logger.info(f"✅ LLM Provider: {generator.llm_provider}")
        logger.info(f"✅ LLM Instance: {type(generator._llm).__name__}")
        logger.info(f"✅ Configuration: {generator.config}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM initialization failed: {e}")
        return False

async def test_simple_exploration():
    """Test a simple exploration scenario."""
    logger.info("🌐 Testing Simple Web Exploration...")
    
    try:
        # Initialize the generator
        generator = ExploratoryQAGenerator(timeout=120)
        
        # Run a simple exploration
        result = await generator.generate_exploratory_tests(
            url="https://httpbin.org/get",
            max_steps=5
        )
        
        # Display results
        logger.info("📊 Exploration Results:")
        logger.info(f"  Test Cases: {len(result.get('test_cases', []))}")
        logger.info(f"  Total Steps: {result.get('total_steps', 0)}")
        
        if result.get('test_cases'):
            test_case = result['test_cases'][0]
            logger.info(f"  Sample Test: {test_case.get('metadata', {}).get('scenario_name', 'Unknown')}")
            logger.info(f"  Steps in Sample: {len(test_case.get('steps', []))}")
        
        # Save results
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "openrouter_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Exploration test failed: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return False

async def test_mock_mode():
    """Test the mock mode for development without API calls."""
    logger.info("🤖 Testing Mock Mode...")
    
    try:
        # Initialize with mock mode
        generator = ExploratoryQAGenerator(
            timeout=30,
            use_mock_llm=True
        )
        
        logger.info(f"✅ Mock LLM Provider: {generator.llm_provider}")
        logger.info(f"✅ Mock LLM Instance: {type(generator._llm).__name__}")
        
        # Test the format test cases method with mock data
        mock_steps = [
            {
                'action_type': 'navigate',
                'selector': '',
                'page_url': 'https://www.saucedemo.com',
                'timestamp': '2024-01-01T10:00:00Z',
                'description': 'Navigate to homepage'
            },
            {
                'action_type': 'click',
                'selector': '[data-testid="main-button"]',
                'page_url': 'https://www.saucedemo.com',
                'timestamp': '2024-01-01T10:00:05Z',
                'description': 'Click main button'
            }
        ]
        
        formatted = generator._format_test_cases(mock_steps)
        
        logger.info("📊 Mock Test Results:")
        logger.info(f"  Test Cases: {len(formatted.get('test_cases', []))}")
        logger.info(f"  Total Steps: {formatted.get('total_steps', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock mode test failed: {e}")
        return False

async def main():
    """Main test runner."""
    logger.info("🚀 OpenRouter Integration Test")
    logger.info("=" * 50)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed. Please configure your .env file.")
        return
    
    # Test scenarios
    tests = [
        ("LLM Initialization", test_llm_initialization),
        ("Mock Mode", test_mock_mode),
    ]
    
    # Only run live API tests if API key is provided
    api_key = os.getenv('BROWSER_USE_LLM_API_KEY')
    if api_key and api_key.strip() and api_key != 'your-api-key-here':
        tests.append(("Simple Exploration (Live API)", test_simple_exploration))
        logger.info("🌐 Live API tests enabled")
    else:
        logger.info("⚠️ Live API tests skipped (no API key provided)")
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        logger.info("-" * 30)
        
        try:
            success = await test_func()
            results[test_name] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = "💥 CRASHED"
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📈 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if "PASSED" in result)
    total = len(results)
    
    for test_name, result in results.items():
        logger.info(f"{result} {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! OpenRouter integration is working correctly.")
    else:
        logger.info("⚠️ Some tests failed. Check the logs above for details.")
    
    return results

if __name__ == "__main__":
    # Ensure outputs directory exists
    Path("outputs").mkdir(exist_ok=True)
    
    # Run tests
    results = asyncio.run(main())
    
    print("\n" + "=" * 50)
    print("🚀 OPENROUTER INTEGRATION TEST COMPLETE")
    print("=" * 50)
    print("📋 Check logs above for detailed results")
    print("📁 Test results saved in 'outputs/' directory")
    print("=" * 50)