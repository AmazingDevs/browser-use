"""
Exploratory QA Test Case Generator - Core Module

This module implements the main ExploratoryQAGenerator class that transforms 
browser-use into an autonomous Senior QA Engineer for exploratory testing.

Key Features:
- Hook-based test case generation with external accumulation
- Browser-use integration with corrected API patterns  
- Comprehensive error handling and async session management
- Playwright-compatible selector extraction
- JSON output structure for test automation frameworks
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from browser_use.llm import ChatOpenAI, ChatAnthropic

# Import from existing test_models module
from test_models import (
    ExploratoryTestStep, 
    ExploratoryTestCase, 
    SelectorExtractor,
    TestCaseFormatter,
    create_test_step,
    create_test_case
)


# Global test accumulator for external accumulation pattern
test_accumulator = []

# Exploratory QA system prompt for behavioral override
EXPLORATORY_QA_PROMPT = """
You are a Senior QA Engineer performing exploratory testing.
Your role is NOT to complete a specific goal, but to:
1. Explore the application systematically
2. Identify testable scenarios at each step
3. Document interactions with precise selectors
4. Generate test cases incrementally
5. Continue exploring until max_steps is reached

At EACH step, you must:
- Analyze the current page state
- Identify interactive elements
- Generate test data for the current interaction
- Build upon previous test steps
- Look for edge cases and validation points

IMPORTANT: Do not try to complete tasks or achieve specific goals. 
Instead, focus on discovering and testing various UI elements and workflows.
Interact with buttons, forms, links, menus, and other interactive elements
to understand the application's behavior and generate comprehensive test coverage.
"""


async def exploratory_step_hook(agent):
    """Hook for real-time test case building - no return values."""
    global test_accumulator
    
    try:
        # Correct DOM state access from agent history
        if not hasattr(agent, 'history') or not agent.history:
            return
            
        history = getattr(agent.history, 'history', []) if hasattr(agent.history, 'history') else agent.history
        
        if not history:
            return
            
        last_step = history[-1]
        current_dom_state = getattr(last_step, 'state', None)
        
        if not current_dom_state:
            return
        
        # Extract test step data from browser state
        model_output = getattr(last_step, 'model_output', None)
        result = getattr(last_step, 'result', None)
        
        action_type = 'unknown'
        if model_output:
            if hasattr(model_output, 'action'):
                action_type = model_output.action
            elif isinstance(model_output, dict) and 'action' in model_output:
                action_type = model_output['action']
        
        selector = SelectorExtractor.extract_selector_from_dom_state(current_dom_state)
        page_url = getattr(current_dom_state, 'url', '') or ''
        
        step_data = {
            'action_type': action_type,
            'selector': selector,
            'page_url': page_url,
            'timestamp': getattr(last_step, 'timestamp', datetime.now().isoformat()),
            'screenshot': getattr(result, 'screenshot', None) if result else None,
            'step_number': len(test_accumulator) + 1
        }
        
        # External accumulation - hooks don't return values
        test_accumulator.append(step_data)
        
    except Exception as e:
        # Proper error handling for hook failures
        print(f"Hook error during test case extraction: {e}")
        # Continue execution - don't break agent flow


class ExploratoryQAGenerator:
    """
    Main class for generating exploratory QA test cases using browser-use.
    
    This class transforms browser-use from a goal-oriented automation tool
    into an exploratory testing agent that generates comprehensive test cases.
    """
    
    def __init__(self, timeout: int = 300, use_mock_llm: bool = False, **kwargs):
        """Initialize the exploratory QA generator."""
        # Global accumulator accessible by hooks
        global test_accumulator
        test_accumulator.clear()
        
        self.explored_elements: Set[str] = set()
        self.timeout = timeout
        self.session_id = str(uuid.uuid4())[:8]
        self.use_mock_llm = use_mock_llm
        
        # Handle any additional kwargs that might be passed
        self.config = kwargs
        
        # Validate and initialize LLM immediately to catch configuration errors early
        try:
            self._llm = self._get_llm_instance()
            # Determine provider from LLM instance for backward compatibility
            self.llm_provider = self._determine_provider_from_model()
        except Exception as e:
            raise ValueError(f"Failed to initialize LLM: {e}")
        
    async def generate_exploratory_tests(self, url: str, max_steps: int = 20) -> Dict[str, Any]:
        """
        Generate exploratory test cases for a given URL.
        
        Args:
            url: Target URL to explore
            max_steps: Maximum number of exploration steps
            
        Returns:
            Dictionary containing test cases and exploration summary
        """
        try:
            print(f"Starting exploratory testing session for: {url}")
            
            # 1. Initialize browser with proper session management
            browser_session = await self._create_browser_session()
            
            # 2. Create agent with correct API parameters
            agent = await self._create_agent(url, browser_session, max_steps)
            
            # 3. Run exploration with proper hook registration
            await self._run_exploration(agent, max_steps)
            
            # 4. Access global accumulator for results
            global test_accumulator
            result = self._format_test_cases(test_accumulator)
            
            print(f"Exploration completed. Generated {len(result.get('test_cases', []))} test scenarios")
            return result
            
        except Exception as e:
            print(f"Error during exploratory testing: {e}")
            return {"error": str(e), "test_cases": [], "total_steps": 0}
        finally:
            # Cleanup resources
            await self._cleanup_session(browser_session if 'browser_session' in locals() else None)
    
    async def _create_browser_session(self):
        """Create browser session with error handling."""
        try:
            from browser_use import BrowserSession
            print("Creating browser session...")
            session = await BrowserSession.create()
            print("Browser session created successfully")
            return session
        except ImportError:
            raise RuntimeError("browser-use package not installed. Please install: pip install browser-use")
        except Exception as e:
            raise RuntimeError(f"Failed to create browser session: {e}")
    
    async def _create_agent(self, url: str, browser_session, max_steps: int):
        """Create and configure the browser-use agent."""
        try:
            from browser_use import Agent
            from browser_use.agent.views import AgentSettings
            
            llm_instance = self._get_llm_instance()
            
            task_description = (
                f"Explore the website at {url} systematically as a QA engineer. "
                f"Do not try to complete specific goals - instead, interact with various "
                f"UI elements to discover functionality. Click buttons, fill forms, "
                f"navigate menus, and test different user interactions."
            )
            
            # Configure agent settings
            agent_settings = AgentSettings(
                use_thinking=True,
                max_history_size=max_steps,
                disable_vision=False
            )
            
            # Create agent with correct API parameters
            agent = Agent(
                task=task_description,
                llm=llm_instance,
                browser_session=browser_session,
                injected_system_prompt=EXPLORATORY_QA_PROMPT,
                agent_settings=agent_settings
            )
            
            print("Agent created successfully")
            return agent
            
        except Exception as e:
            raise RuntimeError(f"Failed to create agent: {e}")
    
    async def _run_exploration(self, agent, max_steps: int):
        """Run the exploration with hook registration."""
        try:
            print(f"Starting exploration with max_steps: {max_steps}")
            
            # Run with proper hook registration
            await agent.run(
                max_steps=max_steps,
                on_step_end=exploratory_step_hook
            )
            
            print("Exploration completed successfully")
            
        except Exception as e:
            print(f"Error during exploration: {e}")
            # Don't re-raise - we want to process whatever data we collected
    
    def _get_llm_instance(self):
        """Get properly configured LLM instance using generic environment variables."""
        try:
            # Use mock LLM for testing if requested
            if self.use_mock_llm:
                return type('MockLLM', (), {})()
            
            # Get configuration from environment variables
            api_key = os.getenv("BROWSER_USE_LLM_API_KEY")
            model = os.getenv("BROWSER_USE_LLM_MODEL")
            base_url = os.getenv("BROWSER_USE_LLM_URL")
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
            
            # Validate required environment variables
            if not model:
                raise ValueError("BROWSER_USE_LLM_MODEL environment variable is required")
            if not api_key:
                raise ValueError("BROWSER_USE_LLM_API_KEY environment variable is required")
            
            # Auto-detect provider from model name
            provider = "anthropic" if "claude" in model.lower() else "openai"
            
            if provider == "anthropic":
                try:
                    
                    return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
                except ImportError:
                    raise RuntimeError("langchain-anthropic package not installed. Please install: pip install langchain-anthropic")
            else:
                try:
                    
                    return ChatOpenAI(
                        model=model,
                        base_url=base_url,
                        temperature=temperature,
                        api_key=api_key
                    )
                except ImportError:
                    raise RuntimeError("langchain-openai package not installed. Please install: pip install langchain-openai")
                    
        except ValueError as e:
            raise e  # Re-raise ValueError as is
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM: {e}")
    
    def _determine_provider_from_model(self):
        """Determine LLM provider from model configuration."""
        try:
            model = os.getenv("BROWSER_USE_LLM_MODEL", "")
            if "claude" in model.lower():
                return "anthropic"
            elif self.use_mock_llm:
                return "mock"
            else:
                return "openai"
        except Exception:
            return "unknown"
    
    async def _cleanup_session(self, browser_session):
        """Clean up browser session resources."""
        try:
            if browser_session:
                await browser_session.close()
                print("Browser session closed")
        except Exception as e:
            print(f"Error cleaning up session: {e}")
    
    def _format_test_cases(self, raw_steps: List[Dict]) -> Dict[str, Any]:
        """Convert accumulated steps into structured test cases."""
        if not raw_steps:
            return {
                "test_cases": [],
                "total_steps": 0,
                "exploration_summary": self._generate_empty_summary()
            }
        
        # Group steps into logical test scenarios
        scenarios = self._group_steps_into_scenarios(raw_steps)
        
        # Generate exploration summary
        summary = self._generate_summary(raw_steps)
        
        return {
            "test_cases": scenarios,
            "total_steps": len(raw_steps),
            "exploration_summary": summary,
            "session_id": self.session_id,
            "generated_at": datetime.now().isoformat()
        }
    
    def _group_steps_into_scenarios(self, raw_steps: List[Dict]) -> List[Dict]:
        """Group individual steps into logical test scenarios."""
        if not raw_steps:
            return []
        
        scenarios = []
        current_scenario = []
        current_url = ""
        scenario_count = 1
        
        for i, step in enumerate(raw_steps):
            step_url = step.get('page_url', '')
            
            # Start new scenario if URL changes significantly or every 5 steps
            if (step_url != current_url and current_scenario) or len(current_scenario) >= 5:
                if current_scenario:
                    scenarios.append(self._create_scenario_from_steps(
                        current_scenario, scenario_count, current_url
                    ))
                    scenario_count += 1
                current_scenario = []
            
            # Create test step using the create_test_step utility
            test_step = create_test_step(
                step_number=len(current_scenario) + 1,
                action_type=step.get('action_type', 'unknown'),
                description=self._generate_step_description(step),
                selector=step.get('selector') or 'body',  # Fallback selector
                input_data=None,  # Could be enhanced to extract input data
                expected_result=self._generate_expected_result(step),
                actual_result=None,  # Could be enhanced to capture actual results
                page_url=step.get('page_url', ''),
                timestamp=step.get('timestamp', datetime.now().isoformat()),
                screenshot_ref=step.get('screenshot')
            )
            
            current_scenario.append(test_step)
            current_url = step_url
        
        # Add final scenario
        if current_scenario:
            scenarios.append(self._create_scenario_from_steps(
                current_scenario, scenario_count, current_url
            ))
        
        return scenarios
    
    def _create_scenario_from_steps(self, steps: List[ExploratoryTestStep], scenario_num: int, url: str) -> Dict:
        """Create a test scenario from a group of steps."""
        scenario_name = f"Exploratory Scenario {scenario_num}"
        
        # Try to generate a more meaningful name based on actions
        action_types = [step.action_type for step in steps]
        if 'click' in action_types and 'type' in action_types:
            scenario_name = f"Form Interaction Scenario {scenario_num}"
        elif 'navigate' in action_types:
            scenario_name = f"Navigation Scenario {scenario_num}"
        elif 'click' in action_types:
            scenario_name = f"UI Interaction Scenario {scenario_num}"
        
        # Use TestCaseFormatter for proper conversion
        formatter = TestCaseFormatter()
        
        # Create test case object first
        test_case = create_test_case(
            test_id=f"exploratory_{scenario_num:03d}",
            scenario_name=scenario_name,
            steps=steps,
            discovered_elements=self._extract_discovered_elements(steps),
            edge_cases=self._identify_edge_cases(steps),
            coverage_metrics=self._calculate_coverage_metrics(steps)
        )
        
        # Convert to dictionary format
        return formatter.to_json(test_case)
    
    def _generate_step_description(self, step: Dict) -> str:
        """Generate human-readable description for a test step."""
        action = step.get('action_type', 'unknown')
        selector = step.get('selector', 'unknown element')
        
        descriptions = {
            'click': f"Click on {selector}",
            'type': f"Type in {selector}",
            'navigate': f"Navigate to page",
            'scroll': f"Scroll on page",
            'verify': f"Verify {selector}",
            'unknown': f"Interact with {selector}"
        }
        
        return descriptions.get(action, f"Perform {action} on {selector}")
    
    def _generate_expected_result(self, step: Dict) -> str:
        """Generate expected result for a test step."""
        action = step.get('action_type', 'unknown')
        
        expected_results = {
            'click': "Element should be clickable and respond to interaction",
            'type': "Text should be entered in the field successfully",
            'navigate': "Page should load successfully",
            'scroll': "Page should scroll smoothly",
            'verify': "Element should be visible and accessible",
            'unknown': "Action should complete successfully"
        }
        
        return expected_results.get(action, "Action should complete without errors")
    
    def _extract_discovered_elements(self, steps: List[ExploratoryTestStep]) -> List[Dict]:
        """Extract discovered UI elements from test steps."""
        elements = []
        seen_selectors = set()
        
        for step in steps:
            if step.selector and step.selector not in seen_selectors:
                elements.append({
                    "selector": step.selector,
                    "action_type": step.action_type,
                    "page_url": step.page_url
                })
                seen_selectors.add(step.selector)
        
        return elements
    
    def _identify_edge_cases(self, steps: List[ExploratoryTestStep]) -> List[str]:
        """Identify potential edge cases from test steps."""
        edge_cases = []
        
        # Check for form validation scenarios
        form_actions = [step for step in steps if step.action_type == 'type']
        if form_actions:
            edge_cases.append("Test form validation with empty inputs")
            edge_cases.append("Test form validation with invalid data")
        
        # Check for navigation scenarios
        nav_actions = [step for step in steps if step.action_type in ['click', 'navigate']]
        if len(nav_actions) > 2:
            edge_cases.append("Test back/forward navigation")
            edge_cases.append("Test page refresh behavior")
        
        return edge_cases
    
    def _calculate_coverage_metrics(self, steps: List[ExploratoryTestStep]) -> Dict:
        """Calculate coverage metrics for test steps."""
        total_steps = len(steps)
        action_types = [step.action_type for step in steps]
        unique_selectors = len(set(step.selector for step in steps if step.selector))
        
        return {
            "total_interactions": total_steps,
            "unique_elements": unique_selectors,
            "action_diversity": len(set(action_types)),
            "most_common_action": max(set(action_types), key=action_types.count) if action_types else "none"
        }
    
    def _generate_summary(self, raw_steps: List[Dict]) -> Dict:
        """Generate exploration summary from raw steps."""
        if not raw_steps:
            return self._generate_empty_summary()
        
        pages_visited = len(set(step.get('page_url', '') for step in raw_steps))
        elements_discovered = len(set(step.get('selector', '') for step in raw_steps if step.get('selector')))
        action_types = [step.get('action_type', '') for step in raw_steps]
        
        return {
            "pages_visited": pages_visited,
            "elements_discovered": elements_discovered,
            "total_interactions": len(raw_steps),
            "action_breakdown": {action: action_types.count(action) for action in set(action_types)},
            "exploration_duration": "N/A",  # Could be calculated from timestamps
            "session_id": self.session_id
        }
    
    def _generate_empty_summary(self) -> Dict:
        """Generate empty summary for failed explorations."""
        return {
            "pages_visited": 0,
            "elements_discovered": 0,
            "total_interactions": 0,
            "action_breakdown": {},
            "exploration_duration": "N/A",
            "session_id": self.session_id
        }
    
    def export_test_cases(self, test_cases: Dict, output_path: str = None) -> str:
        """Export test cases to JSON file."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"exploratory_tests_{timestamp}.json"
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_cases, f, indent=2, ensure_ascii=False)
            
            print(f"Test cases exported to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error exporting test cases: {e}")
            return ""


# Example usage and main function
async def main():
    """Example usage of ExploratoryQAGenerator."""
    try:
        # Initialize the exploratory QA generator
        generator = ExploratoryQAGenerator(llm_provider="anthropic")
        
        # Run exploratory testing
        result = await generator.generate_exploratory_tests(
            url="https://www.saucedemo.com",
            max_steps=10  # Reduced for demo
        )
        
        # Handle results
        if "error" in result:
            print(f"Exploration failed: {result['error']}")
            return result
            
        print(f"Generated {len(result['test_cases'])} test scenarios")
        print(f"Total exploration steps: {result['total_steps']}")
        
        # Export results
        output_file = generator.export_test_cases(result)
        print(f"Results saved to: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"Critical error: {e}")
        return {"error": str(e), "test_cases": []}


if __name__ == "__main__":
    # Run the async function
    result = asyncio.run(main())
    
    # Print summary
    if result.get("test_cases"):
        print("\n" + "="*50)
        print("EXPLORATION SUMMARY")
        print("="*50)
        summary = result.get("exploration_summary", {})
        for key, value in summary.items():
            print(f"{key}: {value}")