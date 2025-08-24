# Feature Implementation Plan: Hook Integration for Test Case Extraction and Injection

## Current State Analysis

✅ **DONE - Enhanced System Prompt**: The `exploratory_qa_system_prompt.md` has been enhanced with comprehensive test case generation guidelines that instruct the AI to output structured JSON containing:

- `"test_cases"`: 8-10 complete Gherkin test scenarios per step
- `"incomplete_test_cases"`: Incomplete scenarios with [INCOMPLETE] markers

✅ **DONE - AI Output Structure**: The AI now responds with the expected JSON format including test case fields.

## Missing Implementation

🔧 **NEEDED - Hook Function**: The `exploratory_step_hook` is referenced in `exploratory_qa_generator.py` but not implemented.

🔧 **NEEDED - Incremental File Saving**: Mechanism to save test cases step-by-step to files.

🔧 **NEEDED - Incomplete Test Injection**: Hook to inject incomplete test cases back into AI context before each step.

## Core Problem to Solve

Based on the browser-use data management analysis and current codebase state, we need to implement three specific components:

1. **Extract test cases from AI JSON responses** via `on_step_end` hook
2. **Save test cases incrementally** to files as exploration progresses
3. **Inject incomplete test cases** via `on_step_start` hook to guide next actions

## Implementation Plan

### Phase 1: Missing Hook Implementation ⚠️ CRITICAL

**Problem**: `exploratory_qa_generator.py` line 199 references `exploratory_step_hook` but the function doesn't exist.

**Solution**: Implement the missing hook function to extract test cases from AI responses.

```python
# Missing hook function to implement in exploratory_qa_generator.py
async def exploratory_step_hook(agent):
    """Extract test cases from AI model output and save incrementally."""
    global test_accumulator

    try:
        # Access latest step from agent history (per browser-use patterns)
        if agent.history.history:
            last_step = agent.history.history[-1]

            # Extract from model_output JSON (AI's structured response)
            if hasattr(last_step, 'model_output') and last_step.model_output:
                test_data = {
                    'step_number': last_step.metadata.step_number,
                    'url': last_step.state.url,
                    'timestamp': last_step.timestamp,
                    'test_cases': getattr(last_step.model_output, 'test_cases', ''),
                    'incomplete_test_cases': getattr(last_step.model_output, 'incomplete_test_cases', '')
                }

                # Add to global accumulator
                test_accumulator.append(test_data)

                # Save incrementally to file
                save_test_cases_incrementally(test_data)

    except Exception as e:
        print(f"Hook error (non-blocking): {e}")
```

### Phase 2: Incremental File Management

**Problem**: Need to save test cases step-by-step as exploration progresses.

**Solution**: Simple file append mechanism that updates a cumulative JSON file.

```python
def save_test_cases_incrementally(test_data):
    """Save test cases to file after each step."""
    import json
    from pathlib import Path

    # Create output directory
    output_dir = Path("./outputs/test_cases")
    output_dir.mkdir(parents=True, exist_ok=True)

    # File naming with session ID
    session_file = output_dir / f"test_cases_{session_id}.json"

    # Load existing or create new
    if session_file.exists():
        with open(session_file, 'r') as f:
            all_data = json.load(f)
    else:
        all_data = {"session_id": session_id, "steps": []}

    # Append new step data
    all_data["steps"].append(test_data)
    all_data["total_steps"] = len(all_data["steps"])

    # Save back to file
    with open(session_file, 'w') as f:
        json.dump(all_data, f, indent=2)

    print(f"💾 Saved test cases from step {test_data['step_number']}")
```

### Phase 3: Incomplete Test Case Injection

**Problem**: Need to inject incomplete test cases back into AI context before each step.

**Solution**: Use `on_step_start` hook to modify agent context with incomplete test cases.

```python
# Global queue for incomplete test cases
incomplete_test_cases_queue = []

async def on_step_start_hook(agent):
    """Inject incomplete test cases into AI context before step."""
    global incomplete_test_cases_queue

    if incomplete_test_cases_queue:
        # Format incomplete cases for injection
        incomplete_text = format_incomplete_cases(incomplete_test_cases_queue)

        # Inject into agent context (extend system message)
        inject_context = f"""
<incomplete_test_cases>
{incomplete_text}
</incomplete_test_cases>
"""

        # Add to agent's message context
        if hasattr(agent, 'message_manager'):
            agent.message_manager.add_system_context(inject_context)

        print(f"🔄 Injected {len(incomplete_test_cases_queue)} incomplete test cases")

def update_incomplete_queue(test_data):
    """Update incomplete test cases queue from latest step."""
    global incomplete_test_cases_queue

    # Parse incomplete test cases from AI response
    if test_data.get('incomplete_test_cases'):
        new_incomplete = parse_incomplete_test_cases(test_data['incomplete_test_cases'])
        incomplete_test_cases_queue.extend(new_incomplete)

        # Keep queue manageable (last 10 incomplete cases)
        incomplete_test_cases_queue = incomplete_test_cases_queue[-10:]
```

## Integration with Existing System

### Step 1: Add Missing Hook Function

Add to `exploratory_qa_generator.py` (before the ExploratoryQAGenerator class):

```python
# Global variables for test case management
test_accumulator = []
incomplete_test_cases_queue = []

async def exploratory_step_hook(agent):
    """Extract test cases from AI responses - MISSING FUNCTION"""
    global test_accumulator, incomplete_test_cases_queue

    try:
        if agent.history.history:
            last_step = agent.history.history[-1]

            # Extract test cases from AI model_output (JSON response with plain text Gherkin)
            if hasattr(last_step, 'model_output') and last_step.model_output:

                # Extract plain text Gherkin from AI response fields
                test_cases_gherkin = getattr(last_step.model_output, 'test_cases', '')
                incomplete_cases_gherkin = getattr(last_step.model_output, 'incomplete_test_cases', '')

                test_data = {
                    'step_number': last_step.metadata.step_number,
                    'url': last_step.state.url,
                    'test_cases': test_cases_gherkin,  # Plain text Gherkin scenarios
                    'incomplete_test_cases': incomplete_cases_gherkin,  # Plain text with [INCOMPLETE] markers
                    'timestamp': datetime.now().isoformat()
                }

                test_accumulator.append(test_data)

                # Save complete test cases as .feature files
                save_test_cases_incrementally(test_data)

                # Update incomplete test cases queue (keep in memory)
                update_incomplete_queue(test_data)

                # Count scenarios for logging
                complete_count = len(test_cases_gherkin.split('\n\n')) if test_cases_gherkin.strip() else 0
                incomplete_count = len(incomplete_cases_gherkin.split('\n\n')) if incomplete_cases_gherkin.strip() else 0

                print(f"✅ Step {test_data['step_number']}: {complete_count} complete + {incomplete_count} incomplete test scenarios")

    except Exception as e:
        print(f"Hook error: {e}")
```

### Step 2: Add Gherkin File Management Functions

```python
def save_test_cases_incrementally(test_data):
    """Save complete test cases as Gherkin .feature files."""
    from pathlib import Path
    from datetime import datetime

    output_dir = Path("./outputs/test_cases")
    output_dir.mkdir(parents=True, exist_ok=True)

file_path = output_dir / f"test_cases_{session_id}.json"

    # Load existing data or create new
    if file_path.exists():
        with open(file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {"steps": []}

    # Append new step
    data["steps"].append(test_data)

    # Save back
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


        print(f"💾 Saved {feature_file.name}")

        # Also append to cumulative feature file
        cumulative_file = output_dir / f"all_test_cases_{session_id}.feature"
        with open(cumulative_file, 'a', encoding='utf-8') as f:
            f.write(f"\n# --- Step {step_num} ---\n")
            f.write(test_cases_text)
            f.write("\n\n")

def update_incomplete_queue(test_data):
    """Update incomplete test cases queue (keep in memory)."""
    global incomplete_test_cases_queue

    # Extract incomplete test cases (plain text Gherkin with [INCOMPLETE] markers)
    incomplete_text = test_data.get('incomplete_test_cases', '')
    if incomplete_text and '[INCOMPLETE]' in incomplete_text:

        # Store incomplete cases for injection
        incomplete_test_cases_queue.append({
            'text': incomplete_text,
            'from_step': test_data['step_number'],
            'url': test_data['url'],
            'timestamp': test_data['timestamp']
        })

        # Keep only last 5 incomplete cases to avoid context overflow
        incomplete_test_cases_queue = incomplete_test_cases_queue[-5:]

        # Optionally save incomplete cases to separate file for debugging
        save_incomplete_cases_debug()

def save_incomplete_cases_debug():
    """Save incomplete cases to debug file (optional)."""
    global incomplete_test_cases_queue

    if incomplete_test_cases_queue:
        debug_file = Path("./outputs/test_cases/incomplete_cases_debug.txt")
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("# Current Incomplete Test Cases Queue\n\n")
            for i, case in enumerate(incomplete_test_cases_queue):
                f.write(f"## From Step {case['from_step']} - {case['url']}\n")
                f.write(f"Generated: {case['timestamp']}\n\n")
                f.write(case['text'])
                f.write("\n\n" + "="*50 + "\n\n")
```

### Step 3: Add Injection Hook with Test Case Reinforcement

```python
async def on_step_start_hook(agent):
    """Inject incomplete test cases and reinforce test case generation requirements."""
    global incomplete_test_cases_queue

    # Reinforcement message for test case generation
    reinforcement_msg = """
🔥 CRITICAL REMINDER: Generate 8-10 comprehensive test cases in your response!

Your JSON response MUST include:
- "test_cases": 8-10 complete Gherkin scenarios (plain text, double newline separated)
- "incomplete_test_cases": Incomplete scenarios with [INCOMPLETE] markers

Do NOT skip test case generation - it is a primary objective!
"""

    if incomplete_test_cases_queue:
        incomplete_text = '\n\n'.join([case['text'] for case in incomplete_test_cases_queue])

        # Injection with reinforcement
        injection = f"""
{reinforcement_msg}

<incomplete_test_cases>
Priority: Complete these incomplete test cases when your actions provide the missing information:

{incomplete_text}
</incomplete_test_cases>
"""
    else:
        injection = reinforcement_msg

    # TODO: Figure out how to inject this into agent context
    print(f"🔄 Injecting test case reinforcement + {len(incomplete_test_cases_queue)} incomplete cases")
```

### Step 4: Update Agent Creation

Modify `_run_exploration` method in ExploratoryQAGenerator:

```python
async def _run_exploration(self, agent, max_steps: int):
    """Run exploration with dual hooks."""
    try:
        print(f"🚀 Starting exploration with test case extraction")

        await agent.run(
            max_steps=max_steps,
            on_step_start=on_step_start_hook,    # Inject incomplete cases
            on_step_end=exploratory_step_hook     # Extract test cases
        )

        print(f"🏁 Completed. Generated {len(test_accumulator)} test case steps")

    except Exception as e:
        print(f"Error during exploration: {e}")
```

## Key Implementation Points

### Browser-Use Integration Notes

**From the data management analysis**, the correct patterns are:

1. **Hook signatures**: `async def hook_name(agent): ...` with no return values
2. **Agent history access**: `agent.history.history[-1]` for latest step
3. **Model output access**: `last_step.model_output.test_cases` (AI's JSON response)
4. **State access**: `last_step.state.url` for current page URL

### System Message Integration

The enhanced system prompt is already configured to output:

```json
{
  "test_cases": "8-10 complete Gherkin test scenarios discovered during this step, covering different aspects of the page functionality. Format as plain text with multiple scenarios separated by double newlines.",
  "incomplete_test_cases": "Incomplete Gherkin scenarios that need additional information, with brief descriptions of what's missing. Use [INCOMPLETE] markers and include missing_info explanations."
}
```

**Key Format Details:**

- `test_cases`: Plain text Gherkin scenarios separated by double newlines (`\n\n`)
- `incomplete_test_cases`: Plain text Gherkin with `[INCOMPLETE]` and `[NEEDS VERIFICATION]` markers
- Both fields contain raw Gherkin text, not JSON structures

So the hook extracts these plain text fields and saves complete test cases as `.feature` files.

### Incomplete Test Case Injection Challenge

**Problem**: How to inject incomplete test cases into AI context before each step?

**Research needed**:

- How does browser-use handle dynamic system message modification?
- Can we extend the `message_manager` to add context?
- Alternative: Use the `extend_system_message` parameter with dynamic content?

**Simple approach**: Store incomplete cases in agent memory/file system and let AI read them via file operations.

## Implementation Timeline (Simple Experimental Approach)

### Week 1: Core Hook Implementation

- [ ] Add missing `exploratory_step_hook` function to extract test cases from AI JSON
- [ ] Implement basic incremental file saving (JSON append)
- [ ] Test that test cases are being extracted and saved correctly

### Week 2: Incomplete Test Case Management

- [ ] Add incomplete test case queue management
- [ ] Research browser-use context injection mechanisms
- [ ] Implement simple injection approach (file-based or extend_system_message)
- [ ] Test complete workflow with incomplete case injection

### Week 3: Integration & Validation

- [ ] Test with real websites (saucedemo.com)
- [ ] Validate test case quality and completeness
- [ ] Fix any issues with hook execution or file saving
- [ ] Document usage and results

## Research Questions for Browser-Use Integration

**Before implementing, need to research:**

1. **Context Injection**: How to dynamically modify agent context between steps?

   - Can we extend `message_manager` to add context?
   - Does `extend_system_message` support dynamic content?
   - Alternative: Write incomplete cases to files and let AI read them?

2. **Model Output Structure**: Verify AI response format matches expectations:

   - Does `last_step.model_output.test_cases` exist?
   - Is it a string or structured data?
   - How are JSON parsing errors handled?

3. **Hook Execution Order**: Confirm hook timing:
   - When exactly does `on_step_start` vs `on_step_end` execute?
   - Is agent state fully updated in `on_step_end`?
   - Can hooks modify agent state for next step?

## Expected Output Files

After implementation, the system will generate:

```
./outputs/test_cases/
├── test_cases_20241201_143022.txt  # Cumulative test cases
├── incomplete_cases_queue.txt      # Current incomplete test cases
└── session_summary.json             # Final summary stats
```

**Example .feature file content:**

```gherkin

Scenario: Login with valid credentials
  Given the login page is displayed
  When the user enters valid credentials
  And clicks the login button
  Then the user should be redirected to the dashboard

Scenario: Login with invalid credentials
  Given the login page is displayed
  When the user enters invalid credentials
  And clicks the login button
  Then an error message should be displayed
```

**Incomplete cases (kept in memory + debug file):**

```gherkin
Scenario: [INCOMPLETE] Verify logout functionality
  Given the user is logged in
  When the user clicks the logout button
  Then [NEEDS VERIFICATION] the user should be logged out
  And [NEEDS VERIFICATION] redirected to login page

Missing info: Need to complete login flow first to test logout functionality.
```

## Conclusion

This plan focuses on the **three critical missing components**:

1. ✅ **Enhanced System Prompt** - Already implemented in your commit
2. 🔧 **Missing Hook Function** - `exploratory_step_hook` needs implementation
3. 🔧 **Incomplete Test Injection** - Research needed for browser-use context modification

The approach is experimental and simple, avoiding over-architecture while providing the core functionality needed for AI-driven test case generation with incremental file management and incomplete test case feedback loops.
