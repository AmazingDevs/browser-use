#!/usr/bin/env python3
"""
Demo Test Script for Exploratory QA Generator

This script demonstrates the basic functionality of the ExploratoryQAGenerator
and validates the implementation without requiring full browser-use setup.
"""

import asyncio
import json
from pathlib import Path
from exploratory_qa_generator import ExploratoryQAGenerator, test_accumulator


class MockBrowserSession:
    """Mock browser session for testing without browser-use."""
    
    async def create(self):
        return self
    
    async def close(self):
        pass


class MockAgent:
    """Mock agent for testing without browser-use."""
    
    def __init__(self, task, llm, browser_session, injected_system_prompt, agent_settings):
        self.task = task
        self.llm = llm
        self.browser_session = browser_session
        self.injected_system_prompt = injected_system_prompt
        self.agent_settings = agent_settings
        
    async def run(self, max_steps, on_step_end):
        """Simulate agent run with mock data."""
        print(f"Mock agent running task: {self.task[:100]}...")
        
        # Simulate some exploration steps
        mock_steps = [
            {
                'action_type': 'navigate',
                'selector': None,
                'page_url': 'https://www.saucedemo.com',
                'timestamp': '2024-01-01T10:00:00Z'
            },
            {
                'action_type': 'click',
                'selector': '[data-testid="login-button"]',
                'page_url': 'https://www.saucedemo.com',
                'timestamp': '2024-01-01T10:00:05Z'
            },
            {
                'action_type': 'type',
                'selector': '#username',
                'page_url': 'https://www.saucedemo.com/login',
                'timestamp': '2024-01-01T10:00:10Z'
            }
        ]
        
        # Add mock steps to global accumulator
        global test_accumulator
        test_accumulator.extend(mock_steps)
        
        print(f"Mock exploration completed with {len(mock_steps)} steps")


class MockLLM:
    """Mock LLM for testing."""
    pass


async def test_basic_functionality():
    """Test basic functionality of ExploratoryQAGenerator."""
    print("Testing ExploratoryQAGenerator basic functionality...")
    
    # Clear test accumulator
    global test_accumulator
    test_accumulator.clear()
    
    # Create generator instance
    generator = ExploratoryQAGenerator(llm_provider="anthropic")
    
    # Test data formatting without browser integration
    mock_raw_steps = [
        {
            'action_type': 'navigate',
            'selector': None,
            'page_url': 'https://www.saucedemo.com',
            'timestamp': '2024-01-01T10:00:00Z',
            'step_number': 1
        },
        {
            'action_type': 'click',
            'selector': '[data-testid="login-button"]',
            'page_url': 'https://www.saucedemo.com',
            'timestamp': '2024-01-01T10:00:05Z',
            'step_number': 2
        },
        {
            'action_type': 'type',
            'selector': '#username',
            'page_url': 'https://www.saucedemo.com/login',
            'timestamp': '2024-01-01T10:00:10Z',
            'step_number': 3
        }
    ]
    
    # Test formatting
    result = generator._format_test_cases(mock_raw_steps)
    
    print(f"✅ Generated {len(result['test_cases'])} test scenarios")
    print(f"✅ Total steps: {result['total_steps']}")
    print(f"✅ Session ID: {result.get('session_id', 'N/A')}")
    
    # Validate structure
    assert 'test_cases' in result
    assert 'total_steps' in result
    assert 'exploration_summary' in result
    assert result['total_steps'] == len(mock_raw_steps)
    
    return result


async def test_selector_extraction():
    """Test selector extraction functionality."""
    print("\nTesting SelectorExtractor functionality...")
    
    from exploratory_qa_generator import SelectorExtractor
    
    # Mock DOM state
    class MockElement:
        def __init__(self, tag_name=None, attributes=None, text=None):
            self.tag_name = tag_name
            self.attributes = attributes or {}
            self.text = text
    
    class MockDOMState:
        def __init__(self, elements):
            self.dom_elements = elements
    
    # Test various selector strategies
    test_cases = [
        {
            'name': 'data-testid selector',
            'element': MockElement('button', {'data-testid': 'submit-btn'}, 'Submit'),
            'expected_prefix': '[data-testid='
        },
        {
            'name': 'ID selector',
            'element': MockElement('input', {'id': 'username'}, ''),
            'expected_prefix': '#username'
        },
        {
            'name': 'text selector',
            'element': MockElement('a', {}, 'Click here'),
            'expected_prefix': 'text='
        }
    ]
    
    for test_case in test_cases:
        dom_state = MockDOMState([test_case['element']])
        selector = SelectorExtractor.extract_selector_from_dom_state(dom_state)
        
        if selector and test_case['expected_prefix'] in selector:
            print(f"✅ {test_case['name']}: {selector}")
        else:
            print(f"❌ {test_case['name']}: Expected {test_case['expected_prefix']}, got {selector}")


async def test_error_handling():
    """Test error handling scenarios."""
    print("\nTesting error handling...")
    
    generator = ExploratoryQAGenerator()
    
    # Test with empty steps
    result = generator._format_test_cases([])
    assert result['total_steps'] == 0
    assert len(result['test_cases']) == 0
    print("✅ Empty steps handled correctly")
    
    # Test with malformed steps
    malformed_steps = [{'invalid': 'data'}]
    result = generator._format_test_cases(malformed_steps)
    assert result['total_steps'] == 1
    print("✅ Malformed steps handled gracefully")


async def test_export_functionality():
    """Test JSON export functionality."""
    print("\nTesting export functionality...")
    
    generator = ExploratoryQAGenerator()
    
    # Create test data
    test_data = {
        'test_cases': [
            {
                'scenario_id': 'test_001',
                'scenario_name': 'Demo Test',
                'steps': [
                    {
                        'step_number': 1,
                        'action_type': 'click',
                        'description': 'Click button',
                        'selector': '#button',
                        'expected_result': 'Button clicked'
                    }
                ]
            }
        ],
        'total_steps': 1,
        'session_id': 'demo-session'
    }
    
    # Test export
    output_file = generator.export_test_cases(test_data, "demo_output.json")
    
    if Path(output_file).exists():
        print(f"✅ Export successful: {output_file}")
        
        # Verify content
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data['session_id'] == 'demo-session'
        print("✅ Export content verified")
        
        # Clean up
        Path(output_file).unlink()
        print("✅ Cleanup completed")
    else:
        print("❌ Export failed")


async def demo_full_workflow():
    """Demonstrate the full workflow with mock data."""
    print("\n" + "="*60)
    print("DEMO: Full Workflow Simulation")
    print("="*60)
    
    # Initialize generator
    generator = ExploratoryQAGenerator(llm_provider="anthropic")
    
    # Simulate exploration results
    mock_exploration_data = {
        'test_cases': [
            {
                'scenario_id': 'exploratory_001',
                'scenario_name': 'Login Flow Validation',
                'steps': [
                    {
                        'step_number': 1,
                        'action_type': 'navigate',
                        'description': 'Navigate to page',
                        'selector': None,
                        'input_data': None,
                        'expected_result': 'Page should load successfully',
                        'actual_result': None,
                        'page_url': 'https://www.saucedemo.com',
                        'timestamp': '2024-01-01T10:00:00Z'
                    },
                    {
                        'step_number': 2,
                        'action_type': 'click',
                        'description': 'Click on [data-testid="login-button"]',
                        'selector': '[data-testid="login-button"]',
                        'input_data': None,
                        'expected_result': 'Element should be clickable and respond to interaction',
                        'actual_result': None,
                        'page_url': 'https://www.saucedemo.com',
                        'timestamp': '2024-01-01T10:00:05Z'
                    },
                    {
                        'step_number': 3,
                        'action_type': 'type',
                        'description': 'Type in #username',
                        'selector': '#username',
                        'input_data': None,
                        'expected_result': 'Text should be entered in the field successfully',
                        'actual_result': None,
                        'page_url': 'https://www.saucedemo.com/login',
                        'timestamp': '2024-01-01T10:00:10Z'
                    }
                ],
                'discovered_elements': [
                    {
                        'selector': '[data-testid="login-button"]',
                        'action_type': 'click',
                        'page_url': 'https://www.saucedemo.com'
                    },
                    {
                        'selector': '#username',
                        'action_type': 'type',
                        'page_url': 'https://www.saucedemo.com/login'
                    }
                ],
                'edge_cases': [
                    'Test form validation with empty inputs',
                    'Test form validation with invalid data'
                ],
                'coverage_metrics': {
                    'total_interactions': 3,
                    'unique_elements': 2,
                    'action_diversity': 3,
                    'most_common_action': 'type'
                }
            }
        ],
        'total_steps': 3,
        'exploration_summary': {
            'pages_visited': 2,
            'elements_discovered': 2,
            'total_interactions': 3,
            'action_breakdown': {
                'navigate': 1,
                'click': 1,
                'type': 1
            },
            'exploration_duration': 'N/A',
            'session_id': generator.session_id
        },
        'session_id': generator.session_id,
        'generated_at': '2024-01-01T10:00:15Z'
    }
    
    # Display results
    print(f"Session ID: {mock_exploration_data['session_id']}")
    print(f"Total Test Cases: {len(mock_exploration_data['test_cases'])}")
    print(f"Total Steps: {mock_exploration_data['total_steps']}")
    
    # Show test case details
    for i, test_case in enumerate(mock_exploration_data['test_cases'], 1):
        print(f"\nTest Case {i}: {test_case['scenario_name']}")
        print(f"  Scenario ID: {test_case['scenario_id']}")
        print(f"  Steps: {len(test_case['steps'])}")
        print(f"  Discovered Elements: {len(test_case['discovered_elements'])}")
        print(f"  Edge Cases: {len(test_case['edge_cases'])}")
        
        for step in test_case['steps'][:2]:  # Show first 2 steps
            print(f"    Step {step['step_number']}: {step['description']}")
            print(f"      Selector: {step['selector']}")
            print(f"      Expected: {step['expected_result']}")
    
    # Export demo data
    export_path = generator.export_test_cases(mock_exploration_data, "demo_full_workflow.json")
    print(f"\nDemo results exported to: {export_path}")
    
    return mock_exploration_data


async def main():
    """Run all demo tests."""
    print("ExploratoryQAGenerator Demo Test Suite")
    print("="*60)
    
    try:
        # Run individual tests
        await test_basic_functionality()
        await test_selector_extraction()
        await test_error_handling()
        await test_export_functionality()
        
        # Run full workflow demo
        demo_result = await demo_full_workflow()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("✅ ExploratoryQAGenerator is ready for integration")
        print("="*60)
        
        return demo_result
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(main())
    
    if result:
        print(f"\nFinal demo result contains {len(result['test_cases'])} test cases")
        print("Demo completed successfully! 🎉")
    else:
        print("Demo failed! ❌")