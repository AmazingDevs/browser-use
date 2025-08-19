# Browser_use Architecture Analysis

This document provides a comprehensive analysis of the browser_use codebase architecture, focusing on state management, context handling, and test generation capabilities.

## 1. Browser_use Architecture Analysis

### Agent State Management

The browser_use framework maintains sophisticated state through multiple interconnected components:

#### AgentState Structure
```python
class AgentState(BaseModel):
    """Holds all state information for an Agent"""
    
    agent_id: str = Field(default_factory=uuid7str)
    n_steps: int = 1
    consecutive_failures: int = 0
    last_result: list[ActionResult] | None = None
    last_plan: str | None = None
    last_model_output: AgentOutput | None = None
    paused: bool = False
    stopped: bool = False
    
    message_manager_state: MessageManagerState = Field(default_factory=MessageManagerState)
    file_system_state: FileSystemState | None = None
```

**Key Features:**
- **Persistent State**: Tracks execution progress across steps
- **Error Handling**: Monitors consecutive failures for circuit breaking
- **Control Flow**: Supports pause/resume operations
- **State Recovery**: Can restore from previous checkpoints

#### BrowserStateSummary
```python
@dataclass
class BrowserStateSummary:
    """The summary of the browser's current state designed for an LLM to process"""
    
    dom_state: SerializedDOMState
    url: str
    title: str
    tabs: list[TabInfo]
    screenshot: str | None = field(default=None, repr=False)
    page_info: PageInfo | None = None
    
    # Legacy compatibility
    pixels_above: int = 0
    pixels_below: int = 0
    browser_errors: list[str] = field(default_factory=list)
    is_pdf_viewer: bool = False
    recent_events: str | None = None
```

**Capabilities:**
- **DOM Serialization**: Enhanced DOM tree with clickable elements
- **Visual Context**: Screenshot capture and viewport information
- **Multi-tab Support**: Tab state tracking across browser sessions
- **Error Recovery**: Browser error state monitoring

### Message Management System

The MessageManager handles conversation flow and context optimization:

#### Core Architecture
```python
class MessageManager:
    def __init__(
        self,
        task: str,
        system_message: SystemMessage,
        file_system: FileSystem,
        state: MessageManagerState = MessageManagerState(),
        use_thinking: bool = True,
        max_history_items: int | None = None,
        vision_detail_level: Literal['auto', 'low', 'high'] = 'auto',
    ):
        self.state = state
        self.max_history_items = max_history_items
        self.last_input_messages = []
```

#### Message Flow Control
```python
def create_state_messages(
    self,
    browser_state_summary: BrowserStateSummary,
    model_output: AgentOutput | None = None,
    result: list[ActionResult] | None = None,
    step_info: AgentStepInfo | None = None,
    use_vision=True,
    page_filtered_actions: str | None = None,
):
    """Create single state message with all content"""
    
    # Clear contextual messages from previous steps
    self.state.history.context_messages.clear()
    
    # Update agent history with latest results
    self._update_agent_history_description(model_output, result, step_info)
    
    # Create consolidated state message
    state_message = AgentMessagePrompt(
        browser_state_summary=browser_state_summary,
        agent_history_description=self.agent_history_description,
        task=self.task,
        screenshots=screenshots,
        vision_detail_level=self.vision_detail_level,
    ).get_user_message(use_vision)
```

### DOM Extraction Patterns

Browser_use implements sophisticated DOM processing for LLM consumption:

#### Enhanced DOM Tree Processing
```python
class DOMTreeSerializer:
    """Serializes enhanced DOM trees to string format."""
    
    def serialize_accessible_elements(self) -> tuple[SerializedDOMState, dict[str, float]]:
        # Step 1: Create simplified tree (includes clickable element detection)
        simplified_tree = self._create_simplified_tree(self.root_node)
        
        # Step 2: Optimize tree (remove unnecessary parents)
        optimized_tree = self._optimize_tree(simplified_tree)
        
        # Step 3: Apply bounding box filtering
        if self.enable_bbox_filtering and optimized_tree:
            filtered_tree = self._apply_bounding_box_filtering(optimized_tree)
        
        # Step 4: Assign interactive indices to clickable elements
        self._assign_interactive_indices_and_mark_new_nodes(filtered_tree)
        
        return SerializedDOMState(_root=filtered_tree, selector_map=self._selector_map)
```

#### Clickable Element Detection
```python
class ClickableElementDetector:
    @staticmethod
    def is_interactive(node: EnhancedDOMTreeNode) -> bool:
        """Enhanced interactivity detection with multiple criteria"""
        
        # Primary: Standard interactive tags
        interactive_tags = {
            'button', 'input', 'select', 'textarea', 'a', 'label', 
            'details', 'summary', 'option', 'optgroup'
        }
        if node.tag_name in interactive_tags:
            return True
            
        # Secondary: Interactive attributes and event handlers
        if node.attributes:
            interactive_attributes = {
                'onclick', 'onmousedown', 'onmouseup', 
                'onkeydown', 'onkeyup', 'tabindex'
            }
            if any(attr in node.attributes for attr in interactive_attributes):
                return True
                
        # Tertiary: ARIA roles and accessibility properties
        if node.ax_node and node.ax_node.properties:
            for prop in node.ax_node.properties:
                if prop.name in ['focusable', 'editable', 'settable'] and prop.value:
                    return True
                    
        return False
```

### Screenshot Capture Mechanisms

Browser_use implements efficient screenshot management:

#### Screenshot Service
```python
class ScreenshotService:
    """Simple screenshot storage service that saves screenshots to disk"""
    
    def __init__(self, agent_directory: str | Path):
        self.agent_directory = Path(agent_directory)
        self.screenshots_dir = self.agent_directory / 'screenshots'
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def store_screenshot(self, screenshot_b64: str, step_number: int) -> str:
        """Store screenshot to disk and return the full path"""
        screenshot_filename = f'step_{step_number}.png'
        screenshot_path = self.screenshots_dir / screenshot_filename
        
        screenshot_data = base64.b64decode(screenshot_b64)
        async with await anyio.open_file(screenshot_path, 'wb') as f:
            await f.write(screenshot_data)
            
        return str(screenshot_path)
```

#### Screenshot Integration in Messages
```python
def get_user_message(self, use_vision: bool = True) -> UserMessage:
    """Create message with screenshot context"""
    if use_vision and self.screenshots:
        content_parts = [ContentPartTextParam(text=state_description)]
        
        for i, screenshot in enumerate(self.screenshots):
            label = 'Current screenshot:' if i == len(self.screenshots) - 1 else 'Previous screenshot:'
            content_parts.append(ContentPartTextParam(text=label))
            content_parts.append(
                ContentPartImageParam(
                    image_url=ImageURL(
                        url=f'data:image/png;base64,{screenshot}',
                        detail=self.vision_detail_level
                    )
                )
            )
        return UserMessage(content=content_parts, cache=True)
```

## 2. Context Management Strategies

### Conversation History Management

Browser_use uses a sophisticated history system to maintain context:

#### History Item Structure
```python
class HistoryItem(BaseModel):
    """Represents a single agent history item"""
    
    step_number: int | None = None
    evaluation_previous_goal: str | None = None
    memory: str | None = None
    next_goal: str | None = None
    action_results: str | None = None
    error: str | None = None
    system_message: str | None = None
    
    def to_string(self) -> str:
        """Convert to formatted string for LLM consumption"""
        step_str = f'step_{self.step_number}' if self.step_number else 'step_unknown'
        
        if self.error:
            return f"<{step_str}>\n{self.error}\n</{step_str}>"
        
        content_parts = []
        if self.evaluation_previous_goal:
            content_parts.append(f'Evaluation: {self.evaluation_previous_goal}')
        if self.memory:
            content_parts.append(f'Memory: {self.memory}')
        if self.next_goal:
            content_parts.append(f'Next Goal: {self.next_goal}')
        if self.action_results:
            content_parts.append(self.action_results)
            
        return f"<{step_str}>\n{chr(10).join(content_parts)}\n</{step_str}>"
```

### Token Optimization Techniques

#### History Truncation Strategy
```python
@property
def agent_history_description(self) -> str:
    """Build agent history with intelligent truncation"""
    if self.max_history_items is None:
        return '\n'.join(item.to_string() for item in self.state.agent_history_items)
    
    total_items = len(self.state.agent_history_items)
    
    if total_items <= self.max_history_items:
        return '\n'.join(item.to_string() for item in self.state.agent_history_items)
    
    # Keep first item + recent items with omission marker
    omitted_count = total_items - self.max_history_items
    recent_items_count = self.max_history_items - 1
    
    items_to_include = [
        self.state.agent_history_items[0].to_string(),  # Keep initialization
        f'<sys>[... {omitted_count} previous steps omitted...]</sys>',
    ]
    items_to_include.extend([
        item.to_string() 
        for item in self.state.agent_history_items[-recent_items_count:]
    ])
    
    return '\n'.join(items_to_include)
```

### State Caching Mechanisms

#### Message Caching
```python
class MessageHistory(BaseModel):
    """Efficient message history management"""
    
    system_message: BaseMessage | None = None
    state_message: BaseMessage | None = None  # Cached state message
    context_messages: list[BaseMessage] = Field(default_factory=list)
    
    def get_messages(self) -> list[BaseMessage]:
        """Get all messages in correct order"""
        messages = []
        if self.system_message:
            messages.append(self.system_message)
        if self.state_message:
            messages.append(self.state_message)
        messages.extend(self.context_messages)
        return messages
```

#### State Restoration
```python
def __init__(self, injected_agent_state: AgentState | None = None):
    """Initialize with optional state restoration"""
    self.state = injected_agent_state or AgentState()
    
    # Restore file system from state if available
    if self.state.file_system_state:
        self.file_system = FileSystem.from_state(self.state.file_system_state)
        self.file_system_path = str(self.file_system.base_dir)
    
    # Initialize message manager with restored state
    self._message_manager = MessageManager(
        state=self.state.message_manager_state,
        # ... other parameters
    )
```

### Memory Management Patterns

#### Progressive Context Building
```python
def _update_agent_history_description(
    self,
    model_output: AgentOutput | None = None,
    result: list[ActionResult] | None = None,
    step_info: AgentStepInfo | None = None,
) -> None:
    """Update agent history with smart content accumulation"""
    
    # Reset read-once state
    self.state.read_state_description = ''
    
    # Build incremental action results
    action_results = ''
    for idx, action_result in enumerate(result or []):
        if action_result.include_extracted_content_only_once:
            # Temporary context - cleared after use
            self.state.read_state_description += action_result.extracted_content + '\n'
        
        if action_result.long_term_memory:
            # Persistent memory
            action_results += f'Action {idx + 1}: {action_result.long_term_memory}\n'
        elif action_result.extracted_content and not action_result.include_extracted_content_only_once:
            # Convert to persistent memory
            action_results += f'Action {idx + 1}: {action_result.extracted_content}\n'
    
    # Create history item
    history_item = HistoryItem(
        step_number=step_info.step_number if step_info else None,
        evaluation_previous_goal=model_output.evaluation_previous_goal if model_output else None,
        memory=model_output.memory if model_output else None,
        next_goal=model_output.next_goal if model_output else None,
        action_results=action_results.strip() if action_results else None,
    )
    self.state.agent_history_items.append(history_item)
```

## 3. Test Case Generation Best Practices

### Optimal Prompt Structure

Browser_use uses a structured prompt system optimized for test generation:

#### System Prompt Template
```python
class SystemPrompt:
    def _load_prompt_template(self) -> None:
        """Load appropriate template based on mode"""
        if self.flash_mode:
            template_filename = 'system_prompt_flash.md'
        elif self.use_thinking:
            template_filename = 'system_prompt.md'  
        else:
            template_filename = 'system_prompt_no_thinking.md'
            
        # Format with action descriptions and constraints
        prompt = self.prompt_template.format(max_actions=self.max_actions_per_step)
        
        if self.extend_system_message:
            prompt += f'\n{self.extend_system_message}'
```

#### Agent Message Structure
```python
def _get_agent_state_description(self) -> str:
    """Build comprehensive agent state for test generation"""
    
    step_info_description = f'Step {self.step_info.step_number + 1} of {self.step_info.max_steps}'
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    agent_state = f"""
<user_request>
{self.task}
</user_request>
<file_system>
{self.file_system.describe() if self.file_system else 'No file system available'}
</file_system>
<todo_contents>
{self.file_system.get_todo_contents() if self.file_system else '[Empty]'}
</todo_contents>
<step_info>
{step_info_description}
Current date and time: {time_str}
</step_info>
"""
    
    if self.sensitive_data:
        agent_state += f'<sensitive_data>\n{self.sensitive_data}\n</sensitive_data>\n'
    
    if self.available_file_paths:
        agent_state += '<available_file_paths>\n' + '\n'.join(self.available_file_paths) + '\n</available_file_paths>\n'
    
    return agent_state
```

### JSON Schema Recommendations

#### AgentOutput Schema
```python
class AgentOutput(BaseModel):
    """Structured output for test case generation"""
    
    thinking: str | None = None
    evaluation_previous_goal: str | None = None
    memory: str | None = None
    next_goal: str | None = None
    action: list[ActionModel] = Field(
        ...,
        description='List of actions to execute',
        json_schema_extra={'min_items': 1}
    )
    
    @classmethod
    def model_json_schema(cls, **kwargs):
        """Ensure required fields for test generation"""
        schema = super().model_json_schema(**kwargs)
        schema['required'] = ['evaluation_previous_goal', 'memory', 'next_goal', 'action']
        return schema
    
    @staticmethod
    def type_with_custom_actions(custom_actions: type[ActionModel]) -> type[AgentOutput]:
        """Create dynamic schema with custom actions"""
        return create_model(
            'AgentOutput',
            __base__=AgentOutput,
            action=(
                list[custom_actions],
                Field(..., description='List of actions to execute', json_schema_extra={'min_items': 1})
            )
        )
```

### Multi-step Instruction Formatting

#### Action Sequence Management
```python
async def multi_act(
    self,
    actions: list[ActionModel],
    check_for_new_elements: bool = True,
) -> list[ActionResult]:
    """Execute multiple actions with validation"""
    
    results = []
    
    for i, action in enumerate(actions):
        # Prevent 'done' action in multi-action sequences
        if i > 0 and action.model_dump(exclude_unset=True).get('done'):
            break
            
        # DOM synchronization check after first action
        if action.get_index() is not None and i != 0:
            new_state = await self.browser_session.get_browser_state_summary()
            
            # Detect element changes
            if self._element_changed(action, new_state):
                results.append(ActionResult(
                    extracted_content="Element changed after previous action",
                    include_in_memory=True
                ))
                break
                
        # Execute action with validation
        result = await self.controller.act(
            action=action,
            browser_session=self.browser_session,
            file_system=self.file_system,
            page_extraction_llm=self.settings.page_extraction_llm,
        )
        results.append(result)
        
        if result.is_done or result.error:
            break
            
    return results
```

### Selector Extraction Strategies

#### Enhanced Element Selection
```python
def _assign_interactive_indices_and_mark_new_nodes(self, node: SimplifiedNode | None) -> None:
    """Assign reliable selectors to interactive elements"""
    
    if not node or (hasattr(node, 'excluded_by_parent') and node.excluded_by_parent):
        return
    
    is_interactive = self._is_interactive_cached(node.original_node)
    is_visible = node.original_node.snapshot_node and node.original_node.is_visible
    
    # Only assign index to visible interactive elements
    if is_interactive and is_visible:
        node.interactive_index = self._interactive_counter
        node.original_node.element_index = self._interactive_counter
        self._selector_map[self._interactive_counter] = node.original_node
        self._interactive_counter += 1
        
        # Mark new elements for test case generation
        if self._previous_cached_selector_map:
            previous_ids = {n.backend_node_id for n in self._previous_cached_selector_map.values()}
            if node.original_node.backend_node_id not in previous_ids:
                node.is_new = True
```

## 4. Memory Chunking Approaches

### Sliding Window Context

Browser_use implements intelligent context windowing:

#### Dynamic History Management
```python
class AgentHistoryList(BaseModel, Generic[AgentStructuredOutput]):
    """Manages agent execution history with intelligent chunking"""
    
    def __init__(self, max_history_items: int | None = None):
        self.max_history_items = max_history_items
        
    def add_item(self, history_item: AgentHistory) -> None:
        """Add item with automatic chunking"""
        self.history.append(history_item)
        
        # Apply sliding window if needed
        if self.max_history_items and len(self.history) > self.max_history_items:
            # Keep first item (initialization) + recent items
            kept_items = [self.history[0]] + self.history[-(self.max_history_items-1):]
            self.history = kept_items
```

### Progressive Summarization

#### Context Compression
```python
def _update_agent_history_description(self) -> None:
    """Progressive summarization of agent actions"""
    
    # Compress older action results
    for idx, action_result in enumerate(result or []):
        if action_result.long_term_memory:
            # Persistent memory - keep full detail
            action_results += f'Action {idx + 1}: {action_result.long_term_memory}\n'
        elif action_result.extracted_content:
            # Compress extracted content
            if len(action_result.extracted_content) > 200:
                compressed = action_result.extracted_content[:100] + '...' + action_result.extracted_content[-100:]
                action_results += f'Action {idx + 1}: {compressed}\n'
            else:
                action_results += f'Action {idx + 1}: {action_result.extracted_content}\n'
```

### Checkpoint-based Restoration

#### State Persistence
```python
def save_file_system_state(self) -> None:
    """Save current state for checkpoint restoration"""
    if self.file_system:
        self.state.file_system_state = self.file_system.get_state()
    
def _set_file_system(self, file_system_path: str | None = None) -> None:
    """Restore from checkpoint or initialize new"""
    if self.state.file_system_state:
        # Restore from checkpoint
        self.file_system = FileSystem.from_state(self.state.file_system_state)
        self.file_system_path = str(self.file_system.base_dir)
    else:
        # Initialize new
        self.file_system = FileSystem(file_system_path or self.agent_directory)
        self.state.file_system_state = self.file_system.get_state()
```

### Incremental Accumulation Patterns

#### Smart Content Aggregation
```python
def model_actions(self) -> list[dict]:
    """Incremental action history accumulation"""
    outputs = []
    
    for h in self.history:
        if h.model_output:
            # Guard against missing interacted elements
            interacted_elements = h.state.interacted_element or [None] * len(h.model_output.action)
            
            for action, interacted_element in zip(h.model_output.action, interacted_elements):
                output = action.model_dump(exclude_none=True)
                output['interacted_element'] = interacted_element
                outputs.append(output)
                
    return outputs

def action_history(self) -> list[list[dict]]:
    """Truncated action history for efficient processing"""
    step_outputs = []
    
    for h in self.history:
        step_actions = []
        if h.model_output:
            for action, element, result in zip(h.model_output.action, 
                                               h.state.interacted_element or [], 
                                               h.result):
                action_output = action.model_dump(exclude_none=True)
                action_output['interacted_element'] = element
                # Only keep essential result data
                action_output['result'] = result.long_term_memory if result and result.long_term_memory else None
                step_actions.append(action_output)
        step_outputs.append(step_actions)
        
    return step_outputs
```

## 5. Quality Assurance Techniques

### Preventing Context Degradation

#### Message State Validation
```python
def _filter_sensitive_data(self, message: BaseMessage) -> BaseMessage:
    """Prevent context contamination with sensitive data"""
    
    def replace_sensitive(value: str) -> str:
        if not self.sensitive_data:
            return value
            
        sensitive_values = {}
        for key_or_domain, content in self.sensitive_data.items():
            if isinstance(content, dict):
                for key, val in content.items():
                    if val:
                        sensitive_values[key] = val
            elif content:
                sensitive_values[key_or_domain] = content
        
        # Replace with placeholders
        for key, val in sensitive_values.items():
            value = value.replace(val, f'<secret>{key}</secret>')
        
        return value
    
    # Apply filtering to message content
    if isinstance(message.content, str):
        message.content = replace_sensitive(message.content)
    elif isinstance(message.content, list):
        for i, item in enumerate(message.content):
            if isinstance(item, ContentPartTextParam):
                item.text = replace_sensitive(item.text)
                
    return message
```

### Maintaining Selector Reliability

#### Element Hash Verification
```python
def __hash__(self) -> int:
    """Stable element hashing for reliable selectors"""
    
    # Get parent branch path for stability
    parent_branch_path = self._get_parent_branch_path()
    parent_branch_path_string = '/'.join(parent_branch_path)
    
    # Include attributes for uniqueness
    attributes_string = ''.join(f'{key}={value}' for key, value in self.attributes.items())
    
    # Create stable hash
    combined_string = f'{parent_branch_path_string}|{attributes_string}'
    element_hash = hashlib.sha256(combined_string.encode()).hexdigest()
    
    return int(element_hash[:16], 16)

async def _update_action_indices(
    self,
    historical_element: DOMInteractedElement | None,
    action: ActionModel,
    browser_state_summary: BrowserStateSummary,
) -> ActionModel | None:
    """Update action indices based on current page state"""
    
    if not historical_element or not browser_state_summary.dom_state.selector_map:
        return action
    
    # Find element by hash match
    highlight_index, current_element = next(
        (
            (highlight_index, element)
            for highlight_index, element in browser_state_summary.dom_state.selector_map.items()
            if element.element_hash == historical_element.element_hash
        ),
        (None, None),
    )
    
    if current_element and highlight_index is not None:
        old_index = action.get_index()
        if old_index != highlight_index:
            action.set_index(highlight_index)
            self.logger.info(f'Element moved: updated index {old_index} → {highlight_index}')
        return action
    
    return None  # Element not found
```

### Screenshot Validation

#### Screenshot Integrity
```python
async def _make_history_item(
    self,
    model_output: AgentOutput | None,
    browser_state_summary: BrowserStateSummary,
    result: list[ActionResult],
    metadata: StepMetadata | None = None,
) -> None:
    """Create history item with screenshot validation"""
    
    screenshot_path = None
    if browser_state_summary.screenshot:
        try:
            # Validate screenshot data
            screenshot_data = base64.b64decode(browser_state_summary.screenshot)
            if len(screenshot_data) < 100:  # Minimum viable screenshot size
                self.logger.warning('Screenshot data too small, skipping')
            else:
                screenshot_path = await self.screenshot_service.store_screenshot(
                    browser_state_summary.screenshot, 
                    self.state.n_steps
                )
        except Exception as e:
            self.logger.error(f'Screenshot validation failed: {e}')
            screenshot_path = None
    
    # Create history with validated screenshot
    state_history = BrowserStateHistory(
        url=browser_state_summary.url,
        title=browser_state_summary.title,
        tabs=browser_state_summary.tabs,
        interacted_element=interacted_elements,
        screenshot_path=screenshot_path,
    )
```

### Test Case Completeness Checks

#### Output Validation
```python
class AgentOutput(BaseModel):
    """Validated agent output with completeness checks"""
    
    @model_validator(mode='after')
    def validate_output_completeness(self):
        """Ensure output meets quality standards"""
        
        # Check required fields
        if not self.memory:
            raise ValueError("Memory field is required for context continuity")
            
        if not self.action or len(self.action) == 0:
            raise ValueError("At least one action is required")
            
        # Validate action sequence
        for i, action in enumerate(self.action):
            action_data = action.model_dump(exclude_unset=True)
            if not action_data:
                raise ValueError(f"Action {i} is empty")
                
            # Check for 'done' action placement
            if 'done' in action_data and i < len(self.action) - 1:
                raise ValueError("'done' action must be the last action")
        
        return self

async def get_model_output(self, input_messages: list[BaseMessage]) -> AgentOutput:
    """Get validated model output"""
    
    try:
        response = await self.llm.ainvoke(input_messages, output_format=self.AgentOutput)
        parsed = response.completion
        
        # Enforce action limits
        if len(parsed.action) > self.settings.max_actions_per_step:
            parsed.action = parsed.action[:self.settings.max_actions_per_step]
            
        # Log validation success
        log_response(parsed, self.controller.registry.registry, self.logger)
        
        return parsed
        
    except ValidationError as e:
        self.logger.error(f"Output validation failed: {e}")
        raise
```

## Implementation Recommendations

### For Test Case Generation Systems

1. **Adopt Progressive Context Building**: Use browser_use's incremental memory system for maintaining test context across steps
2. **Implement Smart Selector Management**: Use element hashing for reliable element identification
3. **Use Vision-Text Integration**: Combine screenshots with DOM serialization for comprehensive test understanding
4. **Apply Token Optimization**: Implement sliding window context with intelligent summarization

### For Memory Management

1. **Checkpoint Strategy**: Save state at key decision points for recovery
2. **Content Compression**: Progressively summarize older context while preserving critical information
3. **Cache Invalidation**: Clear temporary context (read_state) while preserving persistent memory
4. **Quality Validation**: Validate all inputs and outputs for consistency

### For Quality Assurance

1. **Multi-layer Validation**: Validate at DOM, action, and output levels
2. **Error Recovery**: Implement graceful degradation when elements change
3. **Context Integrity**: Prevent sensitive data leakage and context contamination
4. **Completeness Checking**: Ensure all required fields are present and valid

This architecture provides a robust foundation for building reliable, context-aware test generation systems that can handle complex browser automation scenarios while maintaining high quality and consistency.