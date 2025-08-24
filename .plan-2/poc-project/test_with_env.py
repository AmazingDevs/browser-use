#!/usr/bin/env python3
"""
Test with .env file configuration
"""

import asyncio
import os
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.append('src')

from exploratory_qa_generator import ExploratoryQAGenerator


async def main():
    """Test the real browser integration with configured LLM."""
    print("=" * 60)
    print("REAL BROWSER-USE INTEGRATION TEST WITH .ENV CONFIG")
    print("=" * 60)
    
    # Show configuration
    print(f"LLM Model: {os.getenv('BROWSER_USE_LLM_MODEL')}")
    print(f"LLM URL: {os.getenv('BROWSER_USE_LLM_URL')}")
    print(f"API Key: {os.getenv('BROWSER_USE_LLM_API_KEY', 'Not set')[:20]}...")
    print(f"Chrome Path: {os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH')}")
    print(f"Headless Mode: {os.getenv('POC_HEADLESS', 'true')}")
    
    try:
        print(f"\\n[INFO] Creating ExploratoryQAGenerator...")
        generator = ExploratoryQAGenerator(use_mock_llm=False)
        print(f"[SUCCESS] Generator created with LLM provider: {generator.llm_provider}")
        
        print(f"\\n[INFO] Starting real exploration of SauceDemo...")
        print(f"[INFO] This will use real AI to generate test cases!")
        
        result = await generator.generate_exploratory_tests(
            url="https://www.saucedemo.com",
            max_steps=3  # Start small to test
        )
        
        if result.get('success'):
            print(f"\\n[SUCCESS] Real browser exploration completed!")
            
            summary = result.get('exploration_summary', {})
            print(f"\\n=== RESULTS ===")
            print(f"Session ID: {result['session_id']}")
            print(f"Total Steps: {summary.get('total_steps', 0)}")
            print(f"Complete Scenarios: {summary.get('total_complete_scenarios', 0)}")
            print(f"Incomplete Scenarios: {summary.get('total_incomplete_scenarios', 0)}")
            
            # Show output files
            output_files = summary.get('output_files', {})
            print(f"\\n=== GENERATED FILES ===")
            for file_type, file_path in output_files.items():
                if Path(file_path).exists():
                    size = Path(file_path).stat().st_size
                    print(f"{file_type}: {file_path} ({size} bytes)")
            
            # Show sample from feature file
            feature_file = output_files.get('feature_file')
            if feature_file and Path(feature_file).exists():
                print(f"\\n=== SAMPLE TEST CASES ===")
                with open(feature_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:20]  # First 20 lines
                    for line in lines:
                        print(f"  {line.rstrip()}")
                    if len(lines) == 20:
                        print(f"  ... (see full file for more)")
            
            print(f"\\n[SUCCESS] AI-driven test case generation is fully functional!")
            
        else:
            print(f"[ERROR] Test failed: {result.get('error')}")
            
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())