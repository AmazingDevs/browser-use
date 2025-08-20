"""
Exploratory QA Test Case Generator - Revised Core Module

This module implements the main ExploratoryQAGenerator class that leverages 
browser-use's built-in AI capabilities for exploratory testing.

Key Features:
- Extracts from browser_use AI responses instead of hard-coding selectors
- Uses AgentHistory, ActionResult, and extracted_content from browser_use
- System prompt override mechanism (doesn't modify original)
- Leverages browser_use's DOM analysis and AI reasoning
- JSON output structure compatible with test automation frameworks
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

# QA exploration override prompt - appends to original system prompt
EXPLORATORY_QA_OVERRIDE = """
ADDITIONAL EXPLORATION INSTRUCTIONS:

You are conducting exploratory QA testing. Your goal is to systematically explore 
and document website functionality for test case generation.

🔍 EXPLORATION APPROACH:
- Interact with different UI elements to discover functionality
- Try various inputs to test form validation and behavior
- Navigate through different sections and pages
- Focus on documenting what you discover, not completing specific tasks
- Continue exploring until max_steps is reached

📋 DOCUMENTATION FOCUS:
- After each action, provide detailed observations in your thinking
- Document element behaviors, error messages, and system responses
- Note any unexpected behaviors or potential issues
- Describe the current page state and available interactions

⚡ INTERACTION PATTERNS:
- Click buttons and links to see their effects
- Type test data into form fields
- Try edge cases like empty inputs or special characters
- Navigate between pages to map site structure
- Test dropdown menus, toggles, and interactive elements

Continue systematic exploration to build comprehensive understanding of the application.
"""


async def exploratory_step_hook(agent):
    """Revised hook that extracts from browser_use AI responses instead of hard-coding selectors."""
    global test_accumulator
    
    try:
        print(f"[HOOK] Step {len(test_accumulator) + 1} - Extracting from browser_use AI...")
        
        # Access browser_use history data
        if not agent.history or not agent.history.history:
            print("[HOOK] No history available")
            return
            
        last_step = agent.history.history[-1]
        print(f"[HOOK] Processing browser_use step: {type(last_step)}")
        
        # Extract from browser_use AI responses
        ai_thinking = None
        ai_actions = None
        ai_extracted_content = None
        browser_state = None
        page_url = ''
        
        # Extract AI thinking and reasoning from model_output
        try:
            if hasattr(last_step, 'model_output') and last_step.model_output:
                ai_thinking = getattr(last_step.model_output, 'thinking', None)
                ai_actions = getattr(last_step.model_output, 'action', None)
                print(f"[HOOK] AI Thinking available: {bool(ai_thinking)}")
                print(f"[HOOK] AI Actions: {ai_actions}")
        except Exception as e:
            print(f"[HOOK] Model output extraction error: {e}")
        
        # Extract AI-extracted content from ActionResult
        try:
            if hasattr(last_step, 'result') and last_step.result:
                if isinstance(last_step.result, list) and last_step.result:
                    result_obj = last_step.result[0]
                    ai_extracted_content = getattr(result_obj, 'extracted_content', None)
                    print(f"[HOOK] AI extracted content available: {bool(ai_extracted_content)}")
        except Exception as e:
            print(f"[HOOK] Result extraction error: {e}")
        
        # Extract browser state that browser_use AI already analyzed
        try:
            if hasattr(last_step, 'state') and last_step.state:
                browser_state = last_step.state
                if hasattr(browser_state, 'url'):
                    page_url = str(browser_state.url)
                print(f"[HOOK] Browser state available: {bool(browser_state)}")
                print(f"[HOOK] Page URL: {page_url}")
        except Exception as e:
            print(f"[HOOK] State extraction error: {e}")
        
        # Get current page URL from browser session
        try:
            if hasattr(agent, 'browser_session') and agent.browser_session:
                current_page = await agent.browser_session.get_current_page()
                if current_page:
                    page_url = str(current_page.url)
        except Exception as e:
            print(f"[HOOK] Browser session URL error: {e}")
        
        # Build test step from browser_use AI data (not hard-coded)
        test_step = extract_test_data_from_browseruse_ai(
            ai_thinking=ai_thinking,
            ai_actions=ai_actions, 
            ai_extracted_content=ai_extracted_content,
            browser_state=browser_state,
            page_url=page_url,
            step_number=len(test_accumulator) + 1
        )
        
        print(f"[HOOK] Generated test step: {test_step.get('action_description', 'Unknown')}")
        
        # Add to accumulator
        test_accumulator.append(test_step)
        print(f"[HOOK] Total steps accumulated: {len(test_accumulator)}")
        
    except Exception as e:
        print(f"[HOOK] Critical error: {e}")
        import traceback
        traceback.print_exc()
        # Don't let hook errors break the agent


def extract_test_data_from_browseruse_ai(ai_thinking, ai_actions, ai_extracted_content, browser_state, page_url, step_number):
    """Extract test step data from browser_use AI responses instead of hard-coding selectors."""
    try:
        # Extract action information from AI responses
        action_type = 'unknown'
        action_description = 'Unknown action'
        selector_info = 'body'  # Fallback
        input_data = None
        ai_observations = None
        
        # Parse AI actions to understand what was performed
        if ai_actions:
            action_type, selector_info, input_data = _parse_ai_actions(ai_actions)
        
        # Extract AI observations from thinking
        if ai_thinking:
            action_description = _extract_action_description_from_thinking(ai_thinking, action_type)
            ai_observations = _extract_key_observations_from_thinking(ai_thinking)
        
        # Use AI extracted content if available
        page_content = None
        if ai_extracted_content:
            page_content = str(ai_extracted_content)[:500]  # Limit size
        
        # Build test step using browser_use AI data
        test_step = {
            'step_number': step_number,
            'action_type': action_type,
            'action_description': action_description,
            'selector_info': selector_info,  # From browser_use, not hard-coded
            'input_data': input_data,
            'page_url': page_url,
            'ai_thinking': ai_thinking[:300] if ai_thinking else None,  # First 300 chars
            'ai_observations': ai_observations,
            'ai_extracted_content': page_content,
            'timestamp': datetime.now().isoformat(),
            'browser_state_available': bool(browser_state)
        }
        
        return test_step
        
    except Exception as e:
        print(f"[HOOK] Error extracting from browser_use AI: {e}")
        # Return minimal valid step
        return {
            'step_number': step_number,
            'action_type': 'unknown',
            'action_description': 'Error extracting from browser_use AI',
            'selector_info': 'body',
            'page_url': page_url,
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }


def _parse_ai_actions(ai_actions):
    """Parse browser_use AI actions to extract action type and details."""
    try:
        if isinstance(ai_actions, list):
            # Multiple actions - analyze first one
            if ai_actions:
                first_action = ai_actions[0]
                return _analyze_single_action(first_action)
        else:
            # Single action
            return _analyze_single_action(ai_actions)
    except Exception as e:
        print(f"[HOOK] Error parsing AI actions: {e}")
    
    return 'unknown', 'body', None


def _analyze_single_action(action):
    """Analyze a single AI action to extract meaningful data."""
    try:
        if isinstance(action, dict):
            # Dictionary format action
            if 'go_to_url' in action:
                return 'navigate', f"URL: {action['go_to_url'].get('url', 'unknown')}", None
            elif 'click_element_by_index' in action:
                index = action['click_element_by_index'].get('index', 'unknown')
                return 'click', f"Element index: {index}", None
            elif 'input_text' in action:
                index = action['input_text'].get('index', 'unknown')
                text = action['input_text'].get('text', '')
                return 'type', f"Element index: {index}", text
            elif 'extract_structured_data' in action:
                query = action['extract_structured_data'].get('query', 'data extraction')
                return 'extract', f"Query: {query}", None
            elif 'scroll_down' in action or 'scroll_up' in action:
                return 'scroll', 'Page scroll', None
            elif 'done' in action:
                return 'done', 'Task completion', None
        
        # String format action
        action_str = str(action).lower()
        if 'navigate' in action_str or 'go_to' in action_str:
            return 'navigate', 'Navigation action', None
        elif 'click' in action_str:
            return 'click', 'Click action', None
        elif 'input' in action_str or 'type' in action_str:
            return 'type', 'Input action', None
        elif 'scroll' in action_str:
            return 'scroll', 'Scroll action', None
            
    except Exception as e:
        print(f"[HOOK] Error analyzing single action: {e}")
    
    return 'unknown', 'Generic action', None


def _extract_action_description_from_thinking(ai_thinking, action_type):
    """Extract meaningful action description from AI thinking."""
    try:
        thinking_lower = ai_thinking.lower() if ai_thinking else ''
        
        # Look for descriptive phrases in AI thinking
        if action_type == 'navigate':
            if 'navigate to' in thinking_lower:
                # Extract navigation target
                start = thinking_lower.find('navigate to') + 12
                end = thinking_lower.find('.', start)
                if end > start:
                    return f"Navigate to {ai_thinking[start:end].strip()}"
            return "Navigate to page"
        elif action_type == 'click':
            if 'click' in thinking_lower:
                # Find click description
                click_idx = thinking_lower.find('click')
                end = thinking_lower.find('.', click_idx)
                if end > click_idx:
                    return ai_thinking[click_idx:end].strip().capitalize()
            return "Click element"
        elif action_type == 'type':
            if 'type' in thinking_lower or 'enter' in thinking_lower or 'input' in thinking_lower:
                # Find input description
                for keyword in ['type', 'enter', 'input']:
                    if keyword in thinking_lower:
                        start_idx = thinking_lower.find(keyword)
                        end = thinking_lower.find('.', start_idx)
                        if end > start_idx:
                            return ai_thinking[start_idx:end].strip().capitalize()
            return "Enter text input"
        
        # Generic fallback
        return f"Perform {action_type} action"
        
    except Exception as e:
        print(f"[HOOK] Error extracting action description: {e}")
        return f"Perform {action_type} action"


def _extract_key_observations_from_thinking(ai_thinking):
    """Extract key observations from AI thinking for QA purposes."""
    try:
        if not ai_thinking:
            return None
            
        # Look for observation keywords
        observations = []
        thinking_lower = ai_thinking.lower()
        
        # Look for error mentions
        if 'error' in thinking_lower or 'fail' in thinking_lower:
            observations.append('Error or failure mentioned')
            
        # Look for validation mentions
        if 'valid' in thinking_lower or 'invalid' in thinking_lower:
            observations.append('Validation mentioned')
            
        # Look for form mentions
        if 'form' in thinking_lower:
            observations.append('Form interaction')
            
        # Look for page change mentions
        if 'page' in thinking_lower and ('load' in thinking_lower or 'change' in thinking_lower):
            observations.append('Page state change')
            
        return observations if observations else None
        
    except Exception as e:
        print(f"[HOOK] Error extracting observations: {e}")
        return None


class ExploratoryQAGenerator:
    """
    Main class for generating exploratory QA test cases using browser-use.
    
    This class leverages browser-use's built-in AI capabilities to generate 
    comprehensive test cases without hard-coding selectors.
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
        
    async def generate_exploratory_tests(self, url: str, max_steps: int = 25) -> Dict[str, Any]:
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
        """Create browser session with error handling and critical validations."""
        try:
            from browser_use import BrowserSession, BrowserProfile
            import os
            from pathlib import Path
            
            print("Creating browser session...")
            
            # Get environment variables with validation
            chromium_path = os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH', '/usr/bin/google-chrome')
            headless = os.getenv('POC_HEADLESS', 'true').lower() == 'true'
            
            # Critical fix: Validate Chrome executable exists
            if not os.path.exists(chromium_path):
                raise FileNotFoundError(f"Chrome executable not found: {chromium_path}")
            
            # Critical fix: Ensure directories exist
            traces_dir = Path("./outputs/traces")
            browser_data_dir = Path("./outputs/browser_data")
            traces_dir.mkdir(parents=True, exist_ok=True)
            browser_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure browser profile to use system Chrome
            browser_profile = BrowserProfile(
                traces_dir=str(traces_dir),
                user_data_dir=str(browser_data_dir),
                keep_alive=True,
                headless=headless,
                disable_security=False,
                executable_path=chromium_path,  # Point to system Chrome
                chromium_sandbox=False  # Disable sandbox for Docker/environments without sandbox support
            )
            
            print(f"Using Chrome at: {chromium_path}")
            print(f"Headless mode: {headless}")
            print(f"Browser data dir: {browser_data_dir}")
            
            # Create browser session with retry logic
            session = BrowserSession(browser_profile=browser_profile)
            
            print("Browser session created successfully")
            return session
        except ImportError:
            raise RuntimeError("browser-use package not installed. Please install: pip install browser-use")
        except FileNotFoundError as e:
            raise RuntimeError(f"Chrome executable validation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to create browser session: {e}")
    
    async def _create_agent(self, url: str, browser_session, max_steps: int):
        """Create and configure the browser-use agent."""
        try:
            from browser_use import Agent
            from browser_use.agent.views import AgentSettings
            
            llm_instance = self._get_llm_instance()
            
            # Task description that encourages exploration and documentation
            task_description = (
                f"🔍 EXPLORATORY QA TESTING: Systematically explore {url} to discover and document functionality. "
                f"Interact with different UI elements, test form inputs, navigate pages, and document your findings. "
                f"Focus on discovering what the application can do and how it behaves with different inputs. "
                f"Continue exploring different areas until max_steps is reached."
            )
            
            # Configure agent settings
            agent_settings = AgentSettings(
                use_thinking=True,
                max_history_size=max_steps,
                disable_vision=False
            )
            
            # Create agent with system prompt override (not replacement)
            agent = Agent(
                task=task_description,
                llm=llm_instance,
                browser_session=browser_session,
                extend_system_message=EXPLORATORY_QA_OVERRIDE,  # Override instead of replace
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
            
            # Run with proper hook registration and explicit step tracking
            print(f"🚀 Starting exploration with {max_steps} max steps")
            print(f"🎯 Hook registered: {exploratory_step_hook.__name__}")
            
            await agent.run(
                max_steps=max_steps,
                on_step_end=exploratory_step_hook
            )
            
            print(f"🏁 Exploration completed, accumulated {len(test_accumulator)} steps")
            
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
            
            # Convert step to test format
            test_step_data = {
                'step_number': len(current_scenario) + 1,
                'action_type': step.get('action_type', 'unknown'),
                'description': step.get('action_description', 'Unknown action'),
                'selector': step.get('selector_info', 'body'),
                'input_data': step.get('input_data'),
                'expected_result': self._generate_expected_result_from_ai_data(step),
                'actual_result': None,
                'page_url': step.get('page_url', ''),
                'timestamp': step.get('timestamp', datetime.now().isoformat()),
                'ai_observations': step.get('ai_observations'),
                'ai_extracted_content': step.get('ai_extracted_content')
            }
            
            current_scenario.append(test_step_data)
            current_url = step_url
        
        # Add final scenario
        if current_scenario:
            scenarios.append(self._create_scenario_from_steps(
                current_scenario, scenario_count, current_url
            ))
        
        return scenarios
    
    def _create_scenario_from_steps(self, steps: List[Dict], scenario_num: int, url: str) -> Dict:
        """Create a test scenario from a group of steps."""
        scenario_name = f"Exploratory Scenario {scenario_num}"
        
        # Try to generate a more meaningful name based on actions
        action_types = [step['action_type'] for step in steps]
        if 'click' in action_types and 'type' in action_types:
            scenario_name = f"Form Interaction Scenario {scenario_num}"
        elif 'navigate' in action_types:
            scenario_name = f"Navigation Scenario {scenario_num}"
        elif 'click' in action_types:
            scenario_name = f"UI Interaction Scenario {scenario_num}"
        
        return {
            'scenario_id': f"exploratory_{scenario_num:03d}",
            'scenario_name': scenario_name,
            'steps': steps,
            'url': url,
            'total_steps': len(steps),
            'ai_insights': self._extract_ai_insights_from_steps(steps),
            'discovered_elements': self._extract_discovered_elements_from_steps(steps),
            'coverage_metrics': {
                'total_interactions': len(steps),
                'unique_elements': len(set(step['selector'] for step in steps)),
                'action_diversity': len(set(step['action_type'] for step in steps))
            }
        }
    
    def _generate_expected_result_from_ai_data(self, step: Dict) -> str:
        """Generate expected result based on AI observations and action type."""
        action_type = step.get('action_type', 'unknown')
        ai_observations = step.get('ai_observations', [])
        
        # Use AI observations if available
        if ai_observations:
            return f"Expected behavior based on AI observation: {', '.join(ai_observations)}"
        
        # Fallback to generic expected results
        if action_type == 'navigate':
            return "Page loads successfully with expected content"
        elif action_type == 'click':
            return "Element responds to click and triggers intended action"
        elif action_type == 'type':
            return "Input field accepts text entry and validates format"
        elif action_type == 'extract':
            return "Data extraction completes with structured content"
        else:
            return f"{action_type.title()} action completes successfully"
    
    def _extract_ai_insights_from_steps(self, steps: List[Dict]) -> List[str]:
        """Extract AI insights from step data."""
        insights = []
        
        for step in steps:
            if step.get('ai_observations'):
                insights.extend(step['ai_observations'])
            
            # Extract insights from AI extracted content
            if step.get('ai_extracted_content'):
                insights.append(f"Content extracted: {step['ai_extracted_content'][:100]}...")
        
        return list(set(insights))  # Remove duplicates
    
    def _extract_discovered_elements_from_steps(self, steps: List[Dict]) -> List[Dict]:
        """Extract discovered elements from steps."""
        elements = []
        seen_selectors = set()
        
        for step in steps:
            selector = step.get('selector', '')
            if selector and selector not in seen_selectors:
                elements.append({
                    "selector": selector,
                    "action_type": step.get('action_type', 'unknown'),
                    "page_url": step.get('page_url', '')
                })
                seen_selectors.add(selector)
        
        return elements
    
    def _generate_summary(self, raw_steps: List[Dict]) -> Dict:
        """Generate exploration summary from raw steps."""
        if not raw_steps:
            return self._generate_empty_summary()
        
        pages_visited = len(set(step.get('page_url', '') for step in raw_steps))
        elements_discovered = len(set(step.get('selector_info', '') for step in raw_steps if step.get('selector_info')))
        action_types = [step.get('action_type', '') for step in raw_steps]
        
        return {
            "pages_visited": pages_visited,
            "elements_discovered": elements_discovered,
            "total_interactions": len(raw_steps),
            "action_breakdown": {action: action_types.count(action) for action in set(action_types)},
            "ai_insights_generated": sum(1 for step in raw_steps if step.get('ai_observations')),
            "session_id": self.session_id
        }
    
    def _generate_empty_summary(self) -> Dict:
        """Generate empty summary for failed explorations."""
        return {
            "pages_visited": 0,
            "elements_discovered": 0,
            "total_interactions": 0,
            "action_breakdown": {},
            "ai_insights_generated": 0,
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
        generator = ExploratoryQAGenerator()
        
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