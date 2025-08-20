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

EXPLORATORY_QA_OVERRIDE = """

"""

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
           
            return agent
            
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