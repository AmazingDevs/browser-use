Project Brief: Experimental QA Test Case Generator POC

Primary Objective

Create a minimal proof-of-concept that extends browser-use to act as a Senior QA Engineer performing exploratory testing on web applications, automatically generating test cases with steps and
selectors.

Core Requirements

1. Simplicity First

- Build a minimal experimental script (1-2 files maximum)
- Focus only on core functionality
- This is a POC, not a production system

2. Key Deliverables

The agent must extract and document:

- Test cases: Meaningful scenarios discovered during exploration
- Test steps: Detailed, reproducible actions for each test case
- Selectors: Playwright-compatible selectors for each element
- Assertions: Expected outcomes and validation points

3. Technical Integration

- Reference /workspace/.plan/basic_test_generator.py ONLY to understand browser connection setup
- Study /workspace/.findings/browser-use-data-management-analysis.md for deep understanding of browser-use context management
- Priority: Use Playwright selectors for element identification
- Leverage browser-use's state management for test data extraction

4. Behavioral Modifications

- CRITICAL: Override browser-use's default goal-oriented behavior
- The agent should:
  - Analyze current page state at EACH step
  - Generate test cases incrementally during exploration
  - Produce intermediate results continuously
  - Build multiple test cases per session
- Modify browser-use's system prompts to support exploratory testing

5. Architecture Guidelines

- This is an experimental script/POC - keep it minimal
- 1-2 Python files maximum
- Basic validation with simple tests
- Type hints where helpful

Research Requirements

Before implementation, analyze:

- Browser-use context and state management (from the analysis document)
- DOM interaction mechanisms
- Prompt engineering for exploratory behavior

Deliverable: Simple PRD

Create a concise PRD at .plan-2/prd.md covering:

1. Goal: What this POC demonstrates
2. Approach: How it modifies browser-use behavior
3. Technical Design: Simple architecture (1-2 components)
4. Success Criteria: What constitutes a working POC

Remember: This is a proof-of-concept experiment. Keep everything minimal and focused on demonstrating the core capability of exploratory test generation.
