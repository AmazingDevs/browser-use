"""
Exploratory QA Test Case Generator V2 - Using Controller and extracted_content

This module implements the ExploratoryQAGenerator using browser-use's Controller pattern
to generate test cases through custom actions and extracted_content.

Key Features:
- Custom Controller with generate_test_cases action
- Test cases returned via ActionResult.extracted_content
- System prompt that instructs AI to use the custom action
- Hooks extract from action results instead of model output
- Full integration with browser-use's architecture
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, field_validator

from browser_use import Agent, Controller, BrowserSession
from browser_use.agent.views import ActionResult
from browser_use.llm import ChatOpenAI, ChatAnthropic


@dataclass
class TestCaseStep:
	"""Data class for individual test case steps."""
	step_number: int
	url: str
	timestamp: str
	test_cases: str  # Plain text Gherkin scenarios
	incomplete_test_cases: str  # Scenarios with [INCOMPLETE] markers
	extracted_content: Optional[str] = None
	action_type: Optional[str] = None


class GenerateTestCasesAction(BaseModel):
	"""Parameters for test case generation action."""
	
	complete_test_cases: str = Field(
		...,
		description="8-10 complete Gherkin test scenarios discovered during this step, covering different aspects of the page functionality. Format as plain text with multiple scenarios separated by double newlines."
	)
	incomplete_test_cases: str = Field(
		default="",
		description="Incomplete Gherkin scenarios that need additional information, with brief descriptions of what's missing. Use [INCOMPLETE] markers and include missing_info explanations."
	)
	
	@field_validator('complete_test_cases')
	def validate_complete_test_cases(cls, v):
		"""Ensure we have substantial test cases."""
		if not v or len(v.strip()) < 50:
			raise ValueError("Complete test cases must contain substantial content (at least 50 characters)")
		return v
	
	@field_validator('incomplete_test_cases')
	def validate_incomplete_test_cases(cls, v):
		"""Validate incomplete test cases format."""
		if v and '[INCOMPLETE]' not in v and v.strip():
			# If there's content but no [INCOMPLETE] marker, add it
			return f"[INCOMPLETE] {v}"
		return v


class TestCaseManager:
	"""Thread-safe manager for test case accumulation and persistence."""
	
	def __init__(self, session_id: str, output_dir: str = "./outputs/test_cases"):
		self.session_id = session_id
		self.output_dir = Path(output_dir)
		self.output_dir.mkdir(parents=True, exist_ok=True)
		
		# State management
		self._accumulated_steps: List[TestCaseStep] = []
		self._incomplete_queue: List[Dict[str, Any]] = []
		self._lock = asyncio.Lock()  # Thread safety
		
		# File paths
		self.session_file = self.output_dir / f"test_cases_{session_id}.json"
		self.cumulative_file = self.output_dir / f"all_test_cases_{session_id}.feature"
		
		print(f"[INFO] TestCaseManager initialized: {self.output_dir}")
	
	async def add_step(self, step_data: TestCaseStep) -> None:
		"""Add a test case step with thread safety."""
		async with self._lock:
			try:
				# Add to accumulator
				self._accumulated_steps.append(step_data)
				
				# Update incomplete queue
				await self._update_incomplete_queue(step_data)
				
				# Save incrementally
				await self._save_step_incrementally(step_data)
				
				complete_count = self._count_scenarios(step_data.test_cases)
				incomplete_count = self._count_scenarios(step_data.incomplete_test_cases)
				print(f"[SUCCESS] Step {step_data.step_number}: Saved {complete_count} complete + {incomplete_count} incomplete scenarios")
				
			except Exception as e:
				print(f"[WARNING] Error adding step {step_data.step_number}: {e}")
	
	async def get_incomplete_cases_for_injection(self) -> str:
		"""Get formatted incomplete test cases for context injection."""
		async with self._lock:
			if not self._incomplete_queue:
				return ""
			
			# Format for injection (limit to last 5 to prevent context overflow)
			recent_incomplete = self._incomplete_queue[-5:]
			
			injection_text = "\n\n".join([
				f"# From Step {case['from_step']} - {case['url']}\n{case['text']}"
				for case in recent_incomplete
				if case.get('text') and '[INCOMPLETE]' in case['text']
			])
			
			return injection_text
	
	async def _update_incomplete_queue(self, step_data: TestCaseStep) -> None:
		"""Update incomplete test cases queue."""
		if step_data.incomplete_test_cases and '[INCOMPLETE]' in step_data.incomplete_test_cases:
			# Add to queue
			self._incomplete_queue.append({
				'text': step_data.incomplete_test_cases,
				'from_step': step_data.step_number,
				'url': step_data.url,
				'timestamp': step_data.timestamp
			})
			
			# Keep only last 10 items to prevent memory growth
			self._incomplete_queue = self._incomplete_queue[-10:]
	
	async def _save_step_incrementally(self, step_data: TestCaseStep) -> None:
		"""Save step data to files with error handling."""
		try:
			# 1. Save to JSON file
			await self._save_json_data(step_data)
			
			# 2. Save complete test cases to .feature file
			if step_data.test_cases and step_data.test_cases.strip():
				await self._save_feature_data(step_data)
				
		except Exception as e:
			print(f"[WARNING] Error saving step {step_data.step_number}: {e}")
	
	async def _save_json_data(self, step_data: TestCaseStep) -> None:
		"""Save to JSON file for complete session data."""
		try:
			# Load existing data
			if self.session_file.exists():
				with open(self.session_file, 'r', encoding='utf-8') as f:
					data = json.load(f)
			else:
				data = {"session_id": self.session_id, "steps": []}
			
			# Add new step
			data["steps"].append(asdict(step_data))
			data["total_steps"] = len(data["steps"])
			data["last_updated"] = datetime.now().isoformat()
			
			# Save back
			with open(self.session_file, 'w', encoding='utf-8') as f:
				json.dump(data, f, indent=2, ensure_ascii=False)
				
		except Exception as e:
			print(f"[WARNING] Error saving JSON: {e}")
	
	async def _save_feature_data(self, step_data: TestCaseStep) -> None:
		"""Append complete test cases to cumulative .feature file."""
		try:
			with open(self.cumulative_file, 'a', encoding='utf-8') as f:
				f.write(f"\n# === Step {step_data.step_number} - {step_data.url} ===\n")
				f.write(f"# Generated: {step_data.timestamp}\n\n")
				f.write(step_data.test_cases)
				f.write("\n\n" + "=" * 80 + "\n")
				
		except Exception as e:
			print(f"[WARNING] Error saving feature file: {e}")
	
	def _count_scenarios(self, gherkin_text: str) -> int:
		"""Count scenarios in Gherkin text."""
		if not gherkin_text or not gherkin_text.strip():
			return 0
		return len([line for line in gherkin_text.split('\n') if line.strip().startswith('Scenario')])
	
	async def get_summary(self) -> Dict[str, Any]:
		"""Get session summary statistics."""
		async with self._lock:
			total_complete = sum(self._count_scenarios(step.test_cases) for step in self._accumulated_steps)
			total_incomplete = len(self._incomplete_queue)
			
			return {
				"session_id": self.session_id,
				"total_steps": len(self._accumulated_steps),
				"total_complete_scenarios": total_complete,
				"total_incomplete_scenarios": total_incomplete,
				"output_files": {
					"json_data": str(self.session_file),
					"feature_file": str(self.cumulative_file)
				}
			}


# Global instance holder for hook access
_test_case_manager: Optional[TestCaseManager] = None
_controller: Optional[Controller] = None


def create_test_generation_controller() -> Controller:
	"""Create a Controller with test generation action."""
	controller = Controller()
	
	@controller.registry.action(
		description='Generate comprehensive test cases for the current page/interaction. MUST be called at each step to document 8-10 test scenarios.',
		param_model=GenerateTestCasesAction,
	)
	async def generate_test_cases(params: GenerateTestCasesAction, browser_session: BrowserSession) -> ActionResult:
		"""
		Generate test cases and return them via extracted_content.
		This is a virtual action that packages test data for the hook to capture.
		"""
		# Package test data for extraction
		test_data = {
			"complete_test_cases": params.complete_test_cases,
			"incomplete_test_cases": params.incomplete_test_cases,
			"timestamp": datetime.now().isoformat()
		}
		
		# Count scenarios for logging
		complete_count = len([line for line in params.complete_test_cases.split('\n') if line.strip().startswith('Scenario')])
		incomplete_count = len([line for line in params.incomplete_test_cases.split('\n') if line.strip().startswith('Scenario') and '[INCOMPLETE]' in line])
		
		memory = f"Generated {complete_count} complete and {incomplete_count} incomplete test scenarios"
		
		# Return in extracted_content for hook to capture
		return ActionResult(
			extracted_content=json.dumps(test_data, ensure_ascii=False),
			long_term_memory=memory
		)
	
	return controller


async def exploratory_step_hook(agent) -> None:
	"""Extract test cases from ActionResult.extracted_content after each step."""
	global _test_case_manager
	
	try:
		if not _test_case_manager:
			print("[WARNING] TestCaseManager not initialized, skipping step hook")
			return
		
		# Access agent history
		if not agent.history or not agent.history.history:
			print("[INFO] No history available yet")
			return
		
		last_step = agent.history.history[-1]
		
		# Look for test generation action in results
		if last_step.result:
			for action_result in last_step.result:
				if action_result.extracted_content:
					try:
						# Check if this is test case data
						data = json.loads(action_result.extracted_content)
						if "complete_test_cases" in data and "incomplete_test_cases" in data:
							# Found test case data
							step_data = TestCaseStep(
								step_number=len(agent.history.history),
								url=getattr(last_step.state, 'url', 'unknown'),
								timestamp=data.get('timestamp', datetime.now().isoformat()),
								test_cases=data["complete_test_cases"],
								incomplete_test_cases=data["incomplete_test_cases"],
								extracted_content=action_result.extracted_content
							)
							
							# Add to manager
							await _test_case_manager.add_step(step_data)
							break  # Found and processed test cases
							
					except json.JSONDecodeError:
						continue  # Not JSON or not test case data
		
	except Exception as e:
		# Non-blocking error handling
		print(f"[WARNING] Hook error (non-critical): {e}")


async def on_step_start_hook(agent) -> None:
	"""Inject incomplete test cases and reinforce test generation before each step."""
	global _test_case_manager
	
	try:
		if not _test_case_manager:
			return
		
		# Get incomplete cases for injection
		incomplete_cases = await _test_case_manager.get_incomplete_cases_for_injection()
		
		if incomplete_cases:
			print(f"[INFO] {len(incomplete_cases.split('Scenario'))-1} incomplete test cases available for completion")
			# Note: Actual injection happens via extend_system_message
		
		
	except Exception as e:
		print(f"[WARNING] Start hook error (non-critical): {e}")


# Enhanced system prompt for action-based test generation
EXPLORATORY_QA_SYSTEM_PROMPT_EXTENSION = """

**CRITICAL TEST GENERATION REQUIREMENT**:
You MUST call the `generate_test_cases` action at EVERY step to document 8-10 comprehensive test scenarios.

Your dual mission:
1. Complete your assigned exploration task efficiently
2. **Generate 8-10 comprehensive test cases per step** using the `generate_test_cases` action

**Test Case Generation Protocol:**
- After performing exploration actions, ALWAYS call `generate_test_cases` as the last action
- Provide 8-10 complete Gherkin scenarios covering:
  - Different UI components and their states
  - User workflows and navigation patterns
  - Form validation and error scenarios
  - Edge cases and boundary conditions
  - Security and accessibility aspects
- Mark incomplete scenarios with [INCOMPLETE] when additional exploration is needed
- Include specific element references and expected outcomes

**Action Sequence Example:**
```json
{
  "action": [
    {"click_element_by_index": {"index": 23}},
    {"input_text": {"index": 45, "text": "test@example.com"}},
    {"generate_test_cases": {
      "complete_test_cases": "Scenario: Valid email submission\\n  Given the email form is displayed\\n  When user enters 'test@example.com'\\n  And clicks submit\\n  Then success message appears\\n\\nScenario: Invalid email format\\n  Given the email form is displayed\\n  When user enters 'invalid-email'\\n  And clicks submit\\n  Then validation error appears\\n\\n[... 6-8 more scenarios ...]",
      "incomplete_test_cases": "Scenario: [INCOMPLETE] Password reset flow\\n  Given user clicks forgot password\\n  When [NEEDS VERIFICATION] reset form appears\\n  Then [INCOMPLETE] email is sent\\n\\nMissing info: Need to explore password reset functionality"
    }}
  ]
}
```

**Remember**: The `generate_test_cases` action is MANDATORY at each step. Failure to generate test cases means the exploration is incomplete.
"""


class ExploratoryQAGenerator:
	"""
	Main class for generating exploratory QA test cases using browser-use with Controller pattern.
	"""
	
	def __init__(self, timeout: int = 300, use_mock_llm: bool = False, **kwargs):
		"""Initialize the exploratory QA generator with Controller."""
		self.explored_elements: Set[str] = set()
		self.timeout = timeout
		self.session_id = str(uuid.uuid4())[:8]
		self.use_mock_llm = use_mock_llm
		
		# Initialize test case manager
		self.test_case_manager = TestCaseManager(self.session_id)
		
		# Create controller with test generation action
		self.controller = create_test_generation_controller()
		
		# Handle any additional kwargs that might be passed
		self.config = kwargs
		
		# Validate and initialize LLM
		try:
			self._llm = self._get_llm_instance()
			self.llm_provider = self._determine_provider_from_model()
		except Exception as e:
			raise ValueError(f"Failed to initialize LLM: {e}")
		
		print(f"[INFO] ExploratoryQAGenerator V2 initialized with Controller pattern")
	
	async def generate_exploratory_tests(self, url: str, max_steps: int = 25) -> Dict[str, Any]:
		"""
		Generate exploratory test cases for a given URL.
		
		Args:
			url: Target URL to explore
			max_steps: Maximum number of exploration steps
			
		Returns:
			Dictionary containing test cases and exploration summary
		"""
		global _test_case_manager, _controller
		browser_session = None
		
		try:
			print(f"[START] Exploratory testing session for: {url}")
			print(f"[CONFIG] Max steps: {max_steps}, Session ID: {self.session_id}")
			
			# Set global references for hook access
			_test_case_manager = self.test_case_manager
			_controller = self.controller
			
			# 1. Initialize browser with proper session management
			browser_session = await self._create_browser_session()
			
			# 2. Create agent with Controller and enhanced prompt
			agent = await self._create_agent(url, browser_session, max_steps)
			
			# 3. Run exploration with hook registration
			await self._run_exploration(agent, max_steps)
			
			# 4. Get final summary
			summary = await self.test_case_manager.get_summary()
			
			print(f"[SUCCESS] Exploration completed successfully")
			print(f"[RESULTS] {summary['total_complete_scenarios']} test scenarios generated across {summary['total_steps']} steps")
			
			return {
				"session_id": self.session_id,
				"url": url,
				"exploration_summary": summary,
				"success": True
			}
			
		except Exception as e:
			print(f"[ERROR] During exploratory testing: {e}")
			return {"error": str(e), "test_cases": [], "total_steps": 0, "success": False}
		finally:
			# Cleanup resources
			await self._cleanup_session(browser_session)
			# Clear global references
			_test_case_manager = None
			_controller = None
	
	async def _create_browser_session(self):
		"""Create browser session with error handling."""
		try:
			from browser_use import BrowserSession, BrowserProfile
			from pathlib import Path
			
			print("[INFO] Creating browser session...")
			
			# Get Chrome path
			default_chrome_paths = [
				'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
				'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
				'/usr/bin/google-chrome',
				'/usr/bin/chromium-browser',
				'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
			]
			
			chromium_path = os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH')
			if not chromium_path:
				for path in default_chrome_paths:
					if os.path.exists(path):
						chromium_path = path
						break
				else:
					chromium_path = '/usr/bin/google-chrome'
			
			headless = os.getenv('POC_HEADLESS', 'true').lower() == 'true'
			
			# Ensure directories exist
			traces_dir = Path("./outputs/traces")
			browser_data_dir = Path("./outputs/browser_data")
			traces_dir.mkdir(parents=True, exist_ok=True)
			browser_data_dir.mkdir(parents=True, exist_ok=True)
			
			# Configure browser profile
			browser_profile = BrowserProfile(
				traces_dir=str(traces_dir),
				user_data_dir=str(browser_data_dir),
				keep_alive=True,
				headless=headless,
				disable_security=False,
				executable_path=chromium_path if os.path.exists(chromium_path) else None,
				chromium_sandbox=False
			)
			
			print(f"[CONFIG] Headless: {headless}, Chrome: {chromium_path if os.path.exists(chromium_path) else 'auto-detect'}")
			
			# Create browser session
			session = BrowserSession(browser_profile=browser_profile)
			
			print("[SUCCESS] Browser session created")
			return session
			
		except Exception as e:
			raise RuntimeError(f"Failed to create browser session: {e}")
	
	async def _create_agent(self, url: str, browser_session, max_steps: int):
		"""Create and configure the browser-use agent with Controller."""
		try:
			from browser_use import Agent
			from browser_use.agent.views import AgentSettings
			
			llm_instance = self._get_llm_instance()
			
			# Task description that encourages systematic exploration
			task_description = (
				f"EXPLORATORY QA TESTING: Systematically explore {url} to discover and document ALL functionality. "
				f"Interact with every UI element, test all forms, navigate all pages, and document your findings. "
				f"CRITICAL: You MUST call generate_test_cases action at EVERY step to document 8-10 test scenarios. "
				f"Continue exploring different areas until max_steps is reached. Do not stop early."
			)
			
			# Get incomplete cases for initial context
			incomplete_cases = await self.test_case_manager.get_incomplete_cases_for_injection()
			
			# Build extended system message with incomplete cases
			extended_message = EXPLORATORY_QA_SYSTEM_PROMPT_EXTENSION
			if incomplete_cases:
				extended_message += f"\n\n<incomplete_test_cases>\nPriority: Complete these incomplete test cases during exploration:\n\n{incomplete_cases}\n</incomplete_test_cases>"
			
			# Configure agent settings
			agent_settings = AgentSettings(
				use_thinking=True,
				max_history_size=max_steps,
				disable_vision=False
			)
			
			# Create agent with Controller
			agent = Agent(
				task=task_description,
				llm=llm_instance,
				controller=self.controller,  # Use our custom controller
				browser_session=browser_session,
				extend_system_message=extended_message,
				agent_settings=agent_settings
			)
			
			print("[SUCCESS] Agent created with test generation controller")
			return agent
			
		except Exception as e:
			raise RuntimeError(f"Failed to create agent: {e}")
	
	async def _run_exploration(self, agent, max_steps: int):
		"""Run the exploration with hook registration."""
		try:
			print(f"[START] Exploration with {max_steps} max steps")
			print("[INFO] Hooks: exploratory_step_hook (extract) + on_step_start_hook (inject)")
			
			# Run with hooks
			await agent.run(
				max_steps=max_steps,
				on_step_start=on_step_start_hook,  # Inject incomplete test cases
				on_step_end=exploratory_step_hook   # Extract test cases from extracted_content
			)
			
			summary = await self.test_case_manager.get_summary()
			print(f"[COMPLETE] Exploration finished: {summary['total_complete_scenarios']} scenarios generated")
			
		except Exception as e:
			print(f"[ERROR] During exploration: {e}")
			# Don't re-raise - we want to process whatever data we collected
	
	def _get_llm_instance(self):
		"""Get properly configured LLM instance."""
		try:
			if self.use_mock_llm:
				return type('MockLLM', (), {})()
			
			# Get configuration from environment variables
			api_key = os.getenv("BROWSER_USE_LLM_API_KEY")
			model = os.getenv("BROWSER_USE_LLM_MODEL")
			base_url = os.getenv("BROWSER_USE_LLM_URL")
			temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
			
			if not model:
				raise ValueError("BROWSER_USE_LLM_MODEL environment variable is required")
			if not api_key:
				raise ValueError("BROWSER_USE_LLM_API_KEY environment variable is required")
			
			# Auto-detect provider from model name
			provider = "anthropic" if "claude" in model.lower() else "openai"
			
			if provider == "anthropic":
				return ChatAnthropic(
					model=model, 
					temperature=temperature, 
					api_key=api_key,
					timeout=600  # 10 minutes timeout
				)
			else:
				return ChatOpenAI(
					model=model,
					base_url=base_url,
					temperature=temperature,
					api_key=api_key,
					timeout=600  # 10 minutes timeout
				)
				
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
				print("[INFO] Browser session closed")
		except Exception as e:
			print(f"[WARNING] Error cleaning up session: {e}")


# Example usage
async def main():
	"""Example usage of ExploratoryQAGenerator V2."""
	try:
		# Initialize the generator
		generator = ExploratoryQAGenerator()
		
		# Run exploratory testing
		result = await generator.generate_exploratory_tests(
			url="https://www.saucedemo.com",
			max_steps=10
		)
		
		# Display results
		if result.get("success"):
			summary = result.get("exploration_summary", {})
			print("\n" + "=" * 60)
			print("EXPLORATION COMPLETE")
			print("=" * 60)
			for key, value in summary.items():
				print(f"{key}: {value}")
		else:
			print(f"\nError: {result.get('error')}")
		
		return result
		
	except Exception as e:
		print(f"Critical error: {e}")
		return {"error": str(e), "success": False}


if __name__ == "__main__":
	# Run the async function
	result = asyncio.run(main())