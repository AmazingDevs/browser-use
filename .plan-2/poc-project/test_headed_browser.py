#!/usr/bin/env python3
"""
Test with headed browser and capture full stdout
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.append('src')

from exploratory_qa_generator import ExploratoryQAGenerator


class StdoutCapture:
    """Capture stdout to both file and console."""
    
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
        
    def write(self, message):
        # Write to both terminal and file
        try:
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()  # Ensure immediate write
        except UnicodeEncodeError:
            # Handle unicode issues by replacing problematic characters
            clean_message = message.encode('ascii', 'replace').decode('ascii')
            self.terminal.write(clean_message)
            self.log.write(clean_message)
            self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()


async def main():
    """Test with headed browser and full output capture."""
    # Set up output capture
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_output_{timestamp}.txt"
    
    # Redirect stdout
    stdout_capture = StdoutCapture(output_file)
    sys.stdout = stdout_capture
    
    try:
        print("=" * 80)
        print("REAL BROWSER-USE TEST WITH HEADED BROWSER")
        print(f"Output captured to: {output_file}")
        print("=" * 80)
        
        # Override headless mode for this test
        os.environ['POC_HEADLESS'] = 'false'
        
        # Show configuration
        print(f"[CONFIG] LLM Model: {os.getenv('BROWSER_USE_LLM_MODEL')}")
        print(f"[CONFIG] LLM URL: {os.getenv('BROWSER_USE_LLM_URL')}")
        print(f"[CONFIG] API Key: {os.getenv('BROWSER_USE_LLM_API_KEY', 'Not set')[:20]}...")
        print(f"[CONFIG] Chrome Path: {os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH')}")
        print(f"[CONFIG] Headless Mode: {os.getenv('POC_HEADLESS', 'true')}")
        
        print(f"\\n[INFO] Creating ExploratoryQAGenerator with headed browser...")
        generator = ExploratoryQAGenerator(use_mock_llm=False)
        print(f"[SUCCESS] Generator created with LLM provider: {generator.llm_provider}")
        
        print(f"\\n[INFO] Starting HEADED browser exploration of SauceDemo...")
        print(f"[INFO] Browser window will be visible!")
        print(f"[INFO] AI will generate test cases during exploration...")
        
        result = await generator.generate_exploratory_tests(
            url="https://www.saucedemo.com",
            max_steps=5  # More steps to see more test case generation
        )
        
        print("\\n" + "=" * 80)
        print("EXPLORATION RESULTS")
        print("=" * 80)
        
        if result.get('success'):
            print(f"[SUCCESS] Headed browser exploration completed!")
            
            summary = result.get('exploration_summary', {})
            print(f"\\n=== SUMMARY ===")
            print(f"Session ID: {result['session_id']}")
            print(f"URL Explored: {result['url']}")
            print(f"Total Steps: {summary.get('total_steps', 0)}")
            print(f"Complete Scenarios: {summary.get('total_complete_scenarios', 0)}")
            print(f"Incomplete Scenarios: {summary.get('total_incomplete_scenarios', 0)}")
            
            # Show output files
            output_files = summary.get('output_files', {})
            print(f"\\n=== GENERATED FILES ===")
            for file_type, file_path in output_files.items():
                if Path(file_path).exists():
                    size = Path(file_path).stat().st_size
                    print(f"- {file_type}: {file_path} ({size} bytes)")
            
            # Show detailed content from JSON file
            json_file = output_files.get('json_data')
            if json_file and Path(json_file).exists():
                print(f"\\n=== DETAILED TEST CASE DATA ===")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"Session: {data.get('session_id')}")
                    print(f"Total Steps: {data.get('total_steps', 0)}")
                    print(f"Last Updated: {data.get('last_updated')}")
                    
                    steps = data.get('steps', [])
                    for i, step in enumerate(steps, 1):
                        print(f"\\n--- Step {i} ---")
                        print(f"URL: {step.get('url', 'unknown')}")
                        print(f"Timestamp: {step.get('timestamp')}")
                        print(f"Action Type: {step.get('action_type', 'unknown')}")
                        
                        test_cases = step.get('test_cases', '')
                        incomplete_cases = step.get('incomplete_test_cases', '')
                        extracted = step.get('extracted_content', '')
                        
                        if test_cases and test_cases.strip():
                            print(f"[SUCCESS] Test Cases Generated ({len(test_cases)} chars):")
                            print(f"  {test_cases[:200]}...")
                        else:
                            print(f"[WARNING] No test cases generated for this step")
                        
                        if incomplete_cases and incomplete_cases.strip():
                            print(f"[INFO] Incomplete Cases ({len(incomplete_cases)} chars):")
                            print(f"  {incomplete_cases[:200]}...")
                        
                        if extracted and extracted.strip():
                            print(f"[INFO] Extracted Content ({len(extracted)} chars):")
                            print(f"  {extracted[:300]}...")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to parse JSON file: {e}")
            
            # Show feature file content
            feature_file = output_files.get('feature_file')
            if feature_file and Path(feature_file).exists():
                print(f"\\n=== GHERKIN FEATURE FILE SAMPLE ===")
                try:
                    with open(feature_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:30]  # First 30 lines
                        for line in lines:
                            print(f"  {line.rstrip()}")
                        if len(lines) >= 30:
                            print(f"  ... (see full file for more)")
                except Exception as e:
                    print(f"[ERROR] Failed to read feature file: {e}")
            
            print(f"\\n[SUCCESS] AI-driven test case generation with HEADED browser completed!")
            
        else:
            print(f"[ERROR] Test failed: {result.get('error')}")
            
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restore stdout and close file
        sys.stdout = stdout_capture.terminal
        stdout_capture.close()
        print(f"\\n[INFO] Full output saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())