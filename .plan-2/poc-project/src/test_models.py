"""
Test Models for Exploratory QA Test Case Generation

This module contains data structures and utilities for test case representation,
selector extraction, and output formatting for the exploratory QA POC.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Union
import json
import re
from datetime import datetime


@dataclass
class ExploratoryTestStep:
    """
    Represents a single step in an exploratory test case.
    
    Captures detailed information about user interactions including
    selectors, input data, and expected results for reproducibility.
    """
    step_number: int
    action_type: str  # click, type, navigate, scroll, verify, hover, select
    description: str
    selector: str  # Playwright-compatible selector
    input_data: Optional[str] = None
    expected_result: str = ""
    actual_result: Optional[str] = None
    page_url: str = ""
    screenshot_ref: Optional[str] = None
    timestamp: Optional[str] = None
    assertions: Optional[List[str]] = None
    
    def __post_init__(self):
        """Post-initialization validation and defaults"""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if self.assertions is None:
            self.assertions = []
            
        # Validate action_type
        valid_actions = {
            'click', 'type', 'navigate', 'scroll', 'verify', 
            'hover', 'select', 'wait', 'check', 'uncheck',
            'upload', 'download', 'drag', 'drop'
        }
        if self.action_type not in valid_actions:
            print(f"Warning: Unknown action type '{self.action_type}'. Valid types: {valid_actions}")


@dataclass
class ExploratoryTestCase:
    """
    Represents a complete test scenario discovered during exploration.
    
    Contains multiple steps that form a logical test workflow,
    along with metadata about discovered elements and coverage.
    """
    test_id: str
    scenario_name: str
    steps: List[ExploratoryTestStep]
    discovered_elements: List[Dict[str, Any]]  # Elements found during exploration
    edge_cases: List[str] = None
    coverage_metrics: Dict[str, Any] = None
    priority: str = "medium"  # low, medium, high, critical
    tags: List[str] = None
    estimated_duration: Optional[int] = None  # seconds
    preconditions: List[str] = None
    
    def __post_init__(self):
        """Post-initialization validation and defaults"""
        if self.edge_cases is None:
            self.edge_cases = []
            
        if self.coverage_metrics is None:
            self.coverage_metrics = {
                "pages_covered": 0,
                "elements_interacted": 0,
                "forms_tested": 0,
                "navigation_paths": 0
            }
            
        if self.tags is None:
            self.tags = []
            
        if self.preconditions is None:
            self.preconditions = []
    
    def add_step(self, step: ExploratoryTestStep) -> None:
        """Add a step to the test case"""
        self.steps.append(step)
        
    def get_total_steps(self) -> int:
        """Get total number of steps in this test case"""
        return len(self.steps)
    
    def get_unique_pages(self) -> List[str]:
        """Get list of unique pages visited in this test case"""
        return list(set(step.page_url for step in self.steps if step.page_url))


class SelectorExtractor:
    """
    Extract Playwright-compatible selectors from browser-use DOM state.
    
    Implements multiple selector strategies with priority ordering
    for maximum reliability and maintainability.
    """
    
    # Selector priority order as specified in PRD
    SELECTOR_STRATEGIES = [
        'data_testid',
        'id_attribute', 
        'text_content',
        'css_selector',
        'xpath_fallback'
    ]
    
    @staticmethod
    def extract_selector_from_dom_state(dom_state: Any) -> Optional[str]:
        """
        Extract the best available selector from agent's DOM state.
        
        Args:
            dom_state: Browser DOM state from agent history
            
        Returns:
            Playwright-compatible selector string or None if extraction fails
        """
        try:
            if not hasattr(dom_state, 'dom_elements') or not dom_state.dom_elements:
                return SelectorExtractor._fallback_selector_from_state(dom_state)
                
            # Get the most recently interacted element or first available
            target_element = SelectorExtractor._get_target_element(dom_state.dom_elements)
            
            if not target_element:
                return None
                
            # Try each selector strategy in priority order
            for strategy in SelectorExtractor.SELECTOR_STRATEGIES:
                selector = SelectorExtractor._apply_strategy(strategy, target_element)
                if selector:
                    return selector
                    
            return None
            
        except Exception as e:
            print(f"Error extracting selector from DOM state: {e}")
            return None
    
    @staticmethod
    def _get_target_element(dom_elements: List[Any]) -> Optional[Any]:
        """Get the target element for selector extraction"""
        try:
            # Prefer elements that were recently interacted with
            for element in dom_elements:
                if hasattr(element, 'is_active') and element.is_active:
                    return element
                    
            # Fallback to first interactive element
            for element in dom_elements:
                if hasattr(element, 'is_interactive') and element.is_interactive:
                    return element
                    
            # Last resort: return first element
            return dom_elements[0] if dom_elements else None
            
        except Exception:
            return dom_elements[0] if dom_elements else None
    
    @staticmethod
    def _apply_strategy(strategy: str, element: Any) -> Optional[str]:
        """Apply a specific selector strategy to an element"""
        try:
            if strategy == 'data_testid':
                return SelectorExtractor._extract_data_testid(element)
            elif strategy == 'id_attribute':
                return SelectorExtractor._extract_id_attribute(element)
            elif strategy == 'text_content':
                return SelectorExtractor._extract_text_content(element)
            elif strategy == 'css_selector':
                return SelectorExtractor._build_css_selector(element)
            elif strategy == 'xpath_fallback':
                return SelectorExtractor._build_xpath_selector(element)
                
        except Exception as e:
            print(f"Strategy {strategy} failed: {e}")
            
        return None
    
    @staticmethod
    def _extract_data_testid(element: Any) -> Optional[str]:
        """Extract data-testid selector (highest priority)"""
        try:
            if hasattr(element, 'attributes') and element.attributes:
                testid = element.attributes.get('data-testid')
                if testid:
                    # Sanitize testid value
                    clean_testid = re.sub(r'[^\w\-_]', '', testid)
                    return f"[data-testid='{clean_testid}']"
        except Exception:
            pass
        return None
    
    @staticmethod
    def _extract_id_attribute(element: Any) -> Optional[str]:
        """Extract ID attribute selector"""
        try:
            if hasattr(element, 'attributes') and element.attributes:
                element_id = element.attributes.get('id')
                if element_id and element_id.strip():
                    # Sanitize ID value
                    clean_id = re.sub(r'[^\w\-_]', '', element_id)
                    return f"#{clean_id}"
        except Exception:
            pass
        return None
    
    @staticmethod
    def _extract_text_content(element: Any) -> Optional[str]:
        """Extract text-based selector"""
        try:
            if hasattr(element, 'text') and element.text:
                text = element.text.strip()
                if text and len(text) <= 50:  # Reasonable text length
                    # Escape quotes and limit length for safety
                    clean_text = text.replace("'", "\\'").replace('"', '\\"')[:50]
                    return f"text='{clean_text}'"
        except Exception:
            pass
        return None
    
    @staticmethod
    def _build_text_selector(text: str) -> Optional[str]:
        """Build text-based selector from text content"""
        try:
            if text and text.strip():
                clean_text = text.strip()[:50]  # Limit length
                # Escape quotes for selector safety
                clean_text = clean_text.replace("'", "\\'").replace('"', '\\"')
                return f"text='{clean_text}'"
        except Exception:
            pass
        return None
    
    @staticmethod
    def _build_css_selector(element: Any) -> Optional[str]:
        """Build CSS selector combination"""
        try:
            parts = []
            
            # Start with tag name
            if hasattr(element, 'tag_name') and element.tag_name:
                parts.append(element.tag_name.lower())
            
            # Add classes (limit to 2 most specific)
            if hasattr(element, 'attributes') and element.attributes:
                attrs = element.attributes
                if 'class' in attrs and attrs['class']:
                    classes = attrs['class'].split()[:2]  # Limit for stability
                    for cls in classes:
                        clean_class = re.sub(r'[^\w\-_]', '', cls)
                        if clean_class:
                            parts.append(f".{clean_class}")
            
            return ''.join(parts) if parts else None
            
        except Exception:
            return None
    
    @staticmethod
    def _build_xpath_selector(element: Any) -> Optional[str]:
        """Build XPath selector as last resort"""
        try:
            # Try to get xpath from element if available
            if hasattr(element, 'xpath') and element.xpath:
                return element.xpath
                
            # Build simple xpath based on tag and attributes
            if hasattr(element, 'tag_name'):
                tag = element.tag_name.lower()
                xpath_parts = [f"//{tag}"]
                
                if hasattr(element, 'attributes') and element.attributes:
                    attrs = element.attributes
                    # Prefer id, then class, then text
                    if 'id' in attrs:
                        clean_id = re.sub(r'[^\w\-_]', '', attrs['id'])
                        xpath_parts.append(f"[@id='{clean_id}']")
                    elif 'class' in attrs:
                        clean_class = re.sub(r'[^\w\-_\s]', '', attrs['class']).strip()
                        if clean_class:
                            xpath_parts.append(f"[@class='{clean_class}']")
                
                return ''.join(xpath_parts)
                
        except Exception:
            pass
        return None
    
    @staticmethod
    def _fallback_selector_from_state(dom_state: Any) -> Optional[str]:
        """Generate fallback selector when dom_elements is not available"""
        try:
            # Handle None input or invalid types
            if dom_state is None or isinstance(dom_state, (str, int, float, bool, list)):
                return None
                
            # Try to extract from URL or other state information
            if hasattr(dom_state, 'url') and dom_state.url:
                # Create a generic body selector for the page
                return "body"
                
            # Last resort - use html tag only for proper objects
            if hasattr(dom_state, '__dict__'):
                return "html"
            
            return None
            
        except Exception:
            return None


class TestCaseFormatter:
    """
    Format test cases for various output formats including
    executable Playwright scripts and structured JSON.
    """
    
    def __init__(self):
        self.indent = "  "  # 2 spaces for indentation
    
    def to_playwright_script(self, test_case: ExploratoryTestCase) -> str:
        """
        Generate executable Playwright test code from test case.
        
        Args:
            test_case: ExploratoryTestCase to convert
            
        Returns:
            Complete Playwright test script as string
        """
        try:
            script_lines = []
            
            # Add imports and test setup
            script_lines.extend([
                "import asyncio",
                "from playwright.async_api import async_playwright",
                "",
                "async def test_" + test_case.scenario_name.lower().replace(' ', '_').replace('-', '_') + "(page):",
                f"    \"\"\"Test: {test_case.scenario_name}\"\"\"",
            ])
            
            # Add preconditions as comments
            if test_case.preconditions:
                script_lines.append(f"    # Preconditions:")
                for precondition in test_case.preconditions:
                    script_lines.append(f"    # - {precondition}")
                script_lines.append("")
            
            # Convert each step to Playwright code
            for step in test_case.steps:
                step_code = self._convert_step_to_playwright(step)
                if step_code:
                    script_lines.extend(step_code)
                    script_lines.append("")  # Empty line between steps
            
            # Add edge case tests as comments
            if test_case.edge_cases:
                script_lines.extend([
                    f"    # Edge cases to consider:",
                    *[f"    # - {case}" for case in test_case.edge_cases]
                ])
            
            return "\n".join(script_lines)
            
        except Exception as e:
            return f"// Error generating Playwright script: {e}\n// Test case: {test_case.scenario_name}"
    
    def _convert_step_to_playwright(self, step: ExploratoryTestStep) -> List[str]:
        """Convert a single test step to Playwright code lines"""
        try:
            lines = []
            
            # Add step comment
            lines.append(f"    # Step {step.step_number}: {step.description}")
            
            # Generate action code based on action type
            if step.action_type == 'navigate':
                if step.page_url:
                    lines.append(f"    await page.goto('{step.page_url}')")
                elif step.input_data:
                    lines.append(f"    await page.goto('{step.input_data}')")
                    
            elif step.action_type == 'click':
                lines.append(f"    await page.click('{step.selector}')")
                
            elif step.action_type == 'type':
                if step.input_data:
                    # Clear field first, then type
                    lines.extend([
                        f"    await page.fill('{step.selector}', '')",
                        f"    await page.type('{step.selector}', '{step.input_data}')"
                    ])
                else:
                    lines.append(f"    await page.type('{step.selector}', 'test_data')")
                    
            elif step.action_type == 'hover':
                lines.append(f"    await page.hover('{step.selector}')")
                
            elif step.action_type == 'scroll':
                lines.append(f"    await page.locator('{step.selector}').scroll_into_view_if_needed()")
                
            elif step.action_type == 'select':
                if step.input_data:
                    lines.append(f"    await page.select_option('{step.selector}', '{step.input_data}')")
                else:
                    lines.append(f"    await page.select_option('{step.selector}', index=0)")
                    
            elif step.action_type == 'check':
                lines.append(f"    await page.check('{step.selector}')")
                
            elif step.action_type == 'uncheck':
                lines.append(f"    await page.uncheck('{step.selector}')")
                
            elif step.action_type == 'wait':
                lines.append(f"    await page.wait_for_selector('{step.selector}')")
                
            elif step.action_type == 'verify':
                # Add verification/assertion
                if step.expected_result:
                    if 'visible' in step.expected_result.lower():
                        lines.append(f"    assert await page.locator('{step.selector}').is_visible()")
                    elif 'text' in step.expected_result.lower() and step.input_data:
                        lines.append(f"    assert '{step.input_data}' in await page.locator('{step.selector}').text_content()")
                    else:
                        lines.append(f"    assert await page.locator('{step.selector}').is_visible()")
                else:
                    lines.append(f"    assert await page.locator('{step.selector}').is_visible()")
            
            # Add wait for stability after action
            if step.action_type in ['click', 'type', 'select']:
                lines.append(f"    await page.wait_for_timeout(500)  # Wait for action to complete")
            
            # Add custom assertions if any
            if step.assertions:
                for assertion in step.assertions:
                    lines.append(f"    # Assertion: {assertion}")
                    lines.append(f"    assert await page.locator('{step.selector}').is_visible()")
            
            return lines
            
        except Exception as e:
            return [f"    # Error converting step {step.step_number}: {e}"]
    
    def to_json(self, test_case: ExploratoryTestCase) -> Dict[str, Any]:
        """
        Export test case as structured JSON.
        
        Args:
            test_case: ExploratoryTestCase to convert
            
        Returns:
            Dictionary representation suitable for JSON serialization
        """
        try:
            # Use dataclass conversion but with custom formatting
            result = {
                "metadata": {
                    "test_id": test_case.test_id,
                    "scenario_name": test_case.scenario_name,
                    "priority": test_case.priority,
                    "tags": test_case.tags,
                    "estimated_duration": test_case.estimated_duration,
                    "total_steps": test_case.get_total_steps(),
                    "unique_pages": test_case.get_unique_pages(),
                    "generated_at": datetime.now().isoformat()
                },
                "preconditions": test_case.preconditions,
                "steps": [asdict(step) for step in test_case.steps],
                "discovered_elements": test_case.discovered_elements,
                "edge_cases": test_case.edge_cases,
                "coverage_metrics": test_case.coverage_metrics
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to convert test case to JSON: {e}",
                "test_id": getattr(test_case, 'test_id', 'unknown'),
                "scenario_name": getattr(test_case, 'scenario_name', 'unknown')
            }
    
    def to_json_string(self, test_case: ExploratoryTestCase, indent: int = 2) -> str:
        """Export test case as formatted JSON string"""
        try:
            json_data = self.to_json(test_case)
            return json.dumps(json_data, indent=indent, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"JSON serialization failed: {e}"}, indent=indent)
    
    def batch_to_json(self, test_cases: List[ExploratoryTestCase]) -> Dict[str, Any]:
        """Convert multiple test cases to a batch JSON format"""
        try:
            return {
                "generated_at": datetime.now().isoformat(),
                "total_test_cases": len(test_cases),
                "test_cases": [self.to_json(tc) for tc in test_cases]
            }
        except Exception as e:
            return {
                "error": f"Batch conversion failed: {e}",
                "generated_at": datetime.now().isoformat(),
                "total_test_cases": 0,
                "test_cases": []
            }


# Utility functions for working with test models

def create_test_step(
    step_number: int,
    action_type: str,
    description: str,
    selector: str,
    **kwargs
) -> ExploratoryTestStep:
    """
    Convenience function to create a test step with validation.
    
    Args:
        step_number: Step sequence number
        action_type: Type of action (click, type, etc.)
        description: Human-readable description
        selector: Playwright-compatible selector
        **kwargs: Additional optional fields
        
    Returns:
        ExploratoryTestStep instance
    """
    return ExploratoryTestStep(
        step_number=step_number,
        action_type=action_type,
        description=description,
        selector=selector,
        **kwargs
    )


def create_test_case(
    test_id: str,
    scenario_name: str,
    steps: List[ExploratoryTestStep],
    **kwargs
) -> ExploratoryTestCase:
    """
    Convenience function to create a test case with validation.
    
    Args:
        test_id: Unique identifier for the test
        scenario_name: Human-readable scenario name
        steps: List of test steps
        **kwargs: Additional optional fields
        
    Returns:
        ExploratoryTestCase instance
    """
    return ExploratoryTestCase(
        test_id=test_id,
        scenario_name=scenario_name,
        steps=steps,
        **kwargs
    )


def validate_selector(selector: str) -> bool:
    """
    Validate if a selector string is potentially valid for Playwright.
    
    Args:
        selector: Selector string to validate
        
    Returns:
        True if selector appears valid, False otherwise
    """
    if not selector or not isinstance(selector, str):
        return False
    
    # Basic validation patterns
    valid_patterns = [
        r'^#[\w\-_]+$',  # ID selector
        r'^\[data-testid=',  # data-testid selector
        r'^text=',  # Text selector
        r'^\/\/',  # XPath selector
        r'^[\w\-_]+',  # Tag or class selector
    ]
    
    return any(re.match(pattern, selector.strip()) for pattern in valid_patterns)


def extract_element_info(dom_element: Any) -> Dict[str, Any]:
    """
    Extract useful information from a DOM element for test case generation.
    
    Args:
        dom_element: DOM element from browser state
        
    Returns:
        Dictionary with extracted element information
    """
    try:
        info = {
            "tag_name": getattr(dom_element, 'tag_name', None),
            "attributes": getattr(dom_element, 'attributes', {}),
            "text": getattr(dom_element, 'text', ''),
            "is_interactive": getattr(dom_element, 'is_interactive', False),
            "is_visible": getattr(dom_element, 'is_visible', True),
            "selector_candidates": []
        }
        
        # Generate multiple selector candidates
        extractor = SelectorExtractor()
        for strategy in extractor.SELECTOR_STRATEGIES:
            selector = extractor._apply_strategy(strategy, dom_element)
            if selector:
                info["selector_candidates"].append({
                    "strategy": strategy,
                    "selector": selector
                })
        
        return info
        
    except Exception as e:
        return {"error": f"Failed to extract element info: {e}"}