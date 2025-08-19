#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "browser-use",
#     "click",
#     "rich",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

"""
Basic Test Generator - Simple test case generation with browser_use

Usage:
    uvx run basic_test_generator.py --url https://www.saucedemo.com --scenario "Login flow"
    python basic_test_generator.py --help
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from browser_use import Agent, BrowserSession, BrowserProfile
    from browser_use.browser.browser import Browser, BrowserConfig
    from browser_use.llm import ChatOpenAI, ChatAnthropic
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install browser-use click rich python-dotenv")
    sys.exit(1)

console = Console()

@dataclass
class TestStep:
    """Represents a single test step with action and validation"""
    step_id: str
    action_type: str
    description: str
    selector: str
    expected_result: str
    screenshot_path: Optional[str] = None
    timestamp: Optional[str] = None
    
    def to_dict(self):
        return {
            "stepId": self.step_id,
            "action": self.action_type,
            "description": self.description,
            "selector": self.selector,
            "expectedResult": self.expected_result,
            "screenshot": {"capture": bool(self.screenshot_path), "filename": self.screenshot_path},
            "timestamp": self.timestamp
        }

@dataclass
class TestCase:
    """Represents a complete test case with metadata and steps"""
    test_id: str
    name: str
    description: str
    url: str
    steps: List[TestStep]
    created_at: str
    tags: List[str] = None
    estimated_duration: Optional[int] = None
    
    def to_dict(self):
        return {
            "testCaseId": self.test_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at,
            "tags": self.tags or [],
            "estimated_duration": self.estimated_duration
        }


class BasicTestGenerator:
    """
    Basic test case generator using browser_use agent
    
    Features:
    - Custom prompts for test generation
    - Multi-step instruction capture
    - JSON output format
    - Selector extraction from DOM
    - Screenshot integration
    """
    
    def __init__(self, 
                 output_dir: str = "./test_output",
                 screenshots_dir: str = "./screenshots"):
        """
        Initialize the test generator
        
        Args:
            output_dir: Directory to save test cases
            screenshots_dir: Directory to save screenshots
        """
        self.llm = self._get_llm()
        self.output_dir = Path(output_dir)
        self.screenshots_dir = Path(screenshots_dir)
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Test generation prompt template
        self.test_generation_prompt = """
        ROLE: You are an expert QA test case generator.
        
        TASK: Generate comprehensive test cases for the given web application scenario.
        
        REQUIREMENTS:
        1. Create detailed step-by-step test cases
        2. Include specific selectors for UI elements
        3. Provide clear expected results for each step
        4. Consider edge cases and error scenarios
        5. Use descriptive action types (click, type, verify, navigate, wait)
        
        OUTPUT FORMAT:
        For each interaction, provide:
        - Action type (click, type, verify, navigate, wait, scroll)
        - Element description
        - Selector (CSS or XPath)
        - Expected result
        - Any validation points
        
        Be thorough and consider user experience flows.
        """

    def _get_llm(self):
        """Get the appropriate LLM based on generic environment variables."""
        # Get configuration from generic environment variables
        api_key = os.getenv("BROWSER_USE_LLM_API_KEY")
        model = os.getenv("BROWSER_USE_LLM_MODEL")
        base_url = os.getenv("BROWSER_USE_LLM_URL")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        
        if not api_key:
            raise ValueError("BROWSER_USE_LLM_API_KEY not found in environment variables")
        if not model:
            raise ValueError("BROWSER_USE_LLM_MODEL not found in environment variables")
        
        # Determine provider based on model name or base URL
        provider = "anthropic" if "claude" in model.lower() else "openai"
        if provider == "anthropic" or "claude" in model.lower():
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key
            )
        else:
            # Default to OpenAI-compatible API (works for OpenAI, DeepSeek, and other OpenAI-compatible providers)
            return ChatOpenAI(
                model=model,
                base_url=base_url if base_url else None,
                temperature=temperature,
                api_key=api_key
            )

    async def create_browser_session(self) -> BrowserSession:
        """Create a configured browser session for test generation"""
        # Configure browser profile to use system Chrome
        browser_profile = BrowserProfile(
            traces_dir=str(self.output_dir / "traces"),
            user_data_dir=str(self.output_dir / "browser_data"),
            keep_alive=True,
            headless=False,  # Set to False to work with xvfb
            disable_security=False,
            executable_path="/usr/bin/google-chrome",  # Point to system Chrome
            chromium_sandbox=False  # Disable sandbox for Docker
        )
        
        return BrowserSession(browser_profile=browser_profile)

    async def generate_test_case(self, 
                                url: str, 
                                scenario: str = None,
                                scenario_description: str = None,
                                test_name: str = None,
                                max_steps: int = 10) -> TestCase:
        """
        Generate a test case for a given URL and scenario
        
        Args:
            url: Target URL for testing
            scenario: Description of the testing scenario (alias for scenario_description)
            scenario_description: Description of the testing scenario
            test_name: Optional name for the test case
            max_steps: Maximum number of steps to execute
            
        Returns:
            TestCase object with generated steps
        """
        # Allow both scenario and scenario_description for compatibility
        scenario_description = scenario_description or scenario
        if not scenario_description:
            raise ValueError("Either 'scenario' or 'scenario_description' must be provided")
        test_id = str(uuid.uuid4())
        test_name = test_name or f"Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create browser session
        browser_session = await self.create_browser_session()
        
        # Configure agent settings for detailed output
        # Note: AgentSettings may need to be imported or defined based on browser_use version
        settings = {
            "use_thinking": True,
            "save_conversation_path": str(self.output_dir / f"{test_id}_conversation.txt"),
            "generate_gif": True,
            "calculate_cost": True,
            "max_history_items": None  # Keep all history
        }
        
        # Create agent with test generation prompt
        task = f"""
        {self.test_generation_prompt}
        
        TARGET URL: {url}
        SCENARIO: {scenario_description}
        
        Navigate to the URL and explore the interface to create comprehensive test cases.
        Document each interaction with detailed selectors and expected outcomes.
        """
        
        agent = Agent(
            task=task,
            llm=self.llm,
            settings=settings,
            browser_session=browser_session,
            extend_system_message=self._get_detailed_system_message()
        )
        
        # Execute agent with hooks for step capture
        test_steps = []
        
        async def step_capture_hook(agent_instance):
            """Capture each step for test case generation"""
            if agent_instance.state.n_steps > 0:
                last_step = agent_instance.history.history[-1]
                
                # Extract step information
                step = await self._extract_test_step(
                    last_step, 
                    agent_instance.state.n_steps,
                    test_id
                )
                if step:
                    test_steps.append(step)
        
        try:
            # Run agent with step capture
            history = await agent.run(
                max_steps=max_steps,
                on_step_end=step_capture_hook
            )
            
            # Create test case object
            test_case = TestCase(
                test_id=test_id,
                name=test_name,
                description=scenario_description,
                url=url,
                steps=test_steps,
                created_at=datetime.now().isoformat(),
                tags=["generated", "browser_use"],
                estimated_duration=len(test_steps) * 30  # 30 seconds per step estimate
            )
            
            # Save test case to file
            await self._save_test_case(test_case)
            
            return test_case
            
        finally:
            # Cleanup browser session
            await browser_session.close()

    async def _extract_test_step(self, 
                                agent_history, 
                                step_number: int,
                                test_id: str) -> Optional[TestStep]:
        """Extract test step information from agent history"""
        try:
            step_id = f"{test_id}_step_{step_number}"
            
            # Extract action information from model output
            model_output = agent_history.model_output
            result = agent_history.result[0] if agent_history.result else None
            
            # Determine action type and details
            action_type = "unknown"
            description = ""
            selector = ""
            expected_result = ""
            
            if model_output and model_output.action:
                action_data = model_output.action
                action_type = getattr(action_data, 'action_type', 'unknown')
                
                # Extract selector information
                if hasattr(action_data, 'element_id'):
                    selector = f"[data-element-id='{action_data.element_id}']"
                elif hasattr(action_data, 'text'):
                    selector = f"text='{action_data.text}'"
                
                description = getattr(action_data, 'description', str(action_data))
            
            # Extract expected result from thinking or result
            if model_output and model_output.thinking:
                expected_result = model_output.thinking[:200] + "..." if len(model_output.thinking) > 200 else model_output.thinking
            elif result and result.extracted_content:
                expected_result = result.extracted_content[:200] + "..." if len(result.extracted_content) > 200 else result.extracted_content
            
            # Screenshot path
            screenshot_path = None
            if hasattr(agent_history, 'state') and agent_history.state:
                screenshot_path = f"screenshots/step_{step_number}.png"
            
            return TestStep(
                step_id=step_id,
                action_type=action_type,
                description=description,
                selector=selector,
                expected_result=expected_result,
                screenshot_path=screenshot_path,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"Error extracting test step: {e}")
            return None

    def _get_detailed_system_message(self) -> str:
        """Get detailed system message for test generation"""
        return """
        ENHANCED TEST GENERATION MODE:
        
        For each action you take:
        1. Clearly describe what you're testing
        2. Identify the specific UI element and its selector
        3. Explain the expected behavior
        4. Note any validation points
        5. Consider alternative scenarios
        
        Focus on creating reusable, maintainable test steps that can be automated.
        Pay special attention to element identification strategies.
        """

    async def _save_test_case(self, test_case: TestCase):
        """Save test case to JSON file"""
        output_file = self.output_dir / f"{test_case.test_id}.json"
        
        # Convert to dictionary for JSON serialization
        test_data = asdict(test_case)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"Test case saved to: {output_file}")

    async def generate_multiple_scenarios(self, 
                                        url: str, 
                                        scenarios: List[str],
                                        max_steps_per_scenario: int = 5) -> List[TestCase]:
        """Generate test cases for multiple scenarios"""
        test_cases = []
        
        for i, scenario in enumerate(scenarios):
            print(f"Generating test case {i+1}/{len(scenarios)}: {scenario}")
            
            test_case = await self.generate_test_case(
                url=url,
                scenario_description=scenario,
                test_name=f"Scenario_{i+1}_{scenario[:30].replace(' ', '_')}",
                max_steps=max_steps_per_scenario
            )
            
            test_cases.append(test_case)
            
            # Brief pause between scenarios
            await asyncio.sleep(2)
        
        # Save summary file
        await self._save_test_suite_summary(test_cases, url)
        
        return test_cases

    async def _save_test_suite_summary(self, test_cases: List[TestCase], url: str):
        """Save a summary of all generated test cases"""
        summary = {
            "test_suite_id": str(uuid.uuid4()),
            "target_url": url,
            "created_at": datetime.now().isoformat(),
            "total_test_cases": len(test_cases),
            "test_cases": [
                {
                    "test_id": tc.test_id,
                    "name": tc.name,
                    "description": tc.description,
                    "steps_count": len(tc.steps),
                    "estimated_duration": tc.estimated_duration or 0
                }
                for tc in test_cases
            ],
            "total_estimated_duration": sum(tc.estimated_duration or 0 for tc in test_cases)
        }
        
        summary_file = self.output_dir / "test_suite_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Test suite summary saved to: {summary_file}")


# Example usage
async def example_usage():
    """Example usage of the BasicTestGenerator"""
    
    # Initialize generator (requires Anthropic API key)
    api_key = "your_anthropic_api_key_here"  # Replace with actual key
    generator = BasicTestGenerator(
        llm_api_key=api_key,
        output_dir="./test_output",
        screenshots_dir="./screenshots"
    )
    
    # Single test case generation
    test_case = await generator.generate_test_case(
        url="https://www.saucedemo.com",
        scenario_description="User login with valid credentials",
        test_name="Login_Valid_Credentials",
        max_steps=8
    )
    
    print(f"Generated test case: {test_case.name}")
    print(f"Steps: {len(test_case.steps)}")
    
    # Multiple scenarios
    scenarios = [
        "User registration with valid data",
        "User login with invalid credentials",
        "Password reset flow",
        "User profile update"
    ]
    
    test_cases = await generator.generate_multiple_scenarios(
        url="https://www.saucedemo.com",
        scenarios=scenarios,
        max_steps_per_scenario=6
    )
    
    print(f"Generated {len(test_cases)} test cases")


if __name__ == "__main__":
    # Run example
    print("Basic Test Generator - Example Usage")
    print("=" * 40)
    
    # Note: Replace with actual API key to run
    print("To run this example:")
    print("1. Set your Anthropic API key")
    print("2. Install browser_use: pip install browser_use")
    print("3. Run: python basic_test_generator.py")
    
    # Uncomment to run with actual API key
    # asyncio.run(example_usage())