# TRAE Agent Usage Guide

This guide covers how to use the TRAE agent for software engineering tasks, configuration, and advanced features.

## Using Agent on Specific Repository Path

### Command Line Usage

You can specify the repository path using the `--working-dir` flag:

```bash
# Run on specific repository
uv run trae-cli run "Add unit tests for the utils module" --working-dir /path/to/your/repo

# Interactive mode with custom directory
uv run trae-cli interactive --working-dir /path/to/project
```

### Interactive Mode Directory Selection

In interactive mode, you'll be prompted for the working directory:

```bash
uv run trae-cli interactive
# You'll see: "Working Directory: " prompt
# Enter: /path/to/your/repo
```

### Configuration File

You can also set the working directory in your `trae_config.json`:

```json
{
  "working_dir": "/path/to/your/repo",
  "default_provider": "anthropic",
  "max_steps": 20
}
```

## API Key and Base URL Configuration

### Environment Variables

Set API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google Gemini
export GOOGLE_API_KEY="your-google-api-key"

# OpenRouter
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Azure OpenAI
export AZURE_API_KEY="your-azure-api-key"
export AZURE_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/"

# Doubao (Volces)
export DOUBAO_API_KEY="your-doubao-api-key"
export DOUBAO_BASE_URL="https://ark.cn-beijing.volces.com/api/v3/"

# Ollama (local)
export OLLAMA_BASE_URL="http://localhost:11434/v1"
```

### Configuration File

Configure in `trae_config.json`:

```json
{
  "model_providers": {
    "openai": {
      "api_key": "your-openai-api-key",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-4o"
    },
    "anthropic": {
      "api_key": "your-anthropic-api-key",
      "base_url": "https://api.anthropic.com",
      "model": "claude-sonnet-4-20250514"
    },
    "google": {
      "api_key": "your-google-api-key",
      "model": "gemini-2.5-flash"
    },
    "openrouter": {
      "api_key": "your-openrouter-api-key",
      "base_url": "https://openrouter.ai/api/v1",
      "model": "openai/gpt-4o"
    },
    "doubao": {
      "api_key": "your-doubao-api-key",
      "base_url": "https://ark.cn-beijing.volces.com/api/v3/",
      "model": "doubao-seed-1.6"
    }
  }
}
```

### Command Line Override

Override configuration via CLI:

```bash
# Use specific API key
uv run trae-cli run "Create a Python script" --api-key "your-api-key"

# Use custom base URL
uv run trae-cli run "Write tests" --model-base-url "https://custom-api.com/v1"

# Specify provider and model
uv run trae-cli run "Refactor code" --provider anthropic --model claude-sonnet-4-20250514
```

## Adding New Tools/MCPs

### Tool Architecture

Tools are Python classes that inherit from the `Tool` base class:

```python
from trae_agent.tools.base import Tool, ToolParameter

class MyCustomTool(Tool):
    def get_name(self) -> str:
        return "my_custom_tool"
    
    def get_description(self) -> str:
        return "Description of what this tool does"
    
    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="param1",
                type="string",
                description="Description of parameter 1"
            ),
            ToolParameter(
                name="param2",
                type="integer",
                description="Description of parameter 2"
            )
        ]
    
    async def execute(self, arguments):
        # Your tool logic here
        param1 = arguments.get("param1")
        param2 = arguments.get("param2")
        # ... implementation
        return ToolExecResult(output="Success result")
```

### Registering New Tools

1. **Create the tool file** in `trae_agent/tools/`:

   ```python
   # trae_agent/tools/my_custom_tool.py
   from .base import Tool, ToolParameter, ToolExecResult
   
   class MyCustomTool(Tool):
       # ... implementation
   ```

2. **Register the tool** in `trae_agent/tools/__init__.py`:

   ```python
   from .my_custom_tool import MyCustomTool
   
   tools_registry["my_custom_tool"] = MyCustomTool
   ```

3. **Add to imports** in `trae_agent/tools/__init__.py`:

   ```python
   __all__ = [
       "MyCustomTool",
       # ... other tools
   ]
   ```

### MCP (Model Context Protocol) Integration

The agent can be extended to support MCP servers:

1. **Create MCP client wrapper**:

   ```python
   class MCPTool(Tool):
       def __init__(self, mcp_server_url: str):
           super().__init__()
           self.mcp_server_url = mcp_server_url
   
       async def execute(self, arguments):
           # Implement MCP protocol communication
           pass
   ```

2. **Dynamic tool loading** from MCP configuration:

   ```python
   # Load tools from MCP server configuration
   def load_mcp_tools(mcp_config):
       tools = []
       for server in mcp_config.get("servers", []):
           # Register MCP tools as Trae tools
           tools.append(MCPTool(server["url"]))
       return tools
   ```

## Process Stopping Mechanism

### Graceful Shutdown

The agent supports several stopping mechanisms:

1. **Keyboard Interrupt** (`Ctrl+C`):
   - Stops current task execution
   - Saves partial trajectory
   - Returns to command line

2. **Timeout**:
   - Each tool execution has a 120-second timeout
   - Overall task respects `max_steps` limit

3. **Task Completion**:
   - Agent calls `task_done` tool when finished
   - Saves final trajectory
   - Exits cleanly

### Interactive Mode Commands

In interactive mode:

```bash
# Stop current task execution
Ctrl+C

# Exit interactive mode
type: exit
or
type: quit

# Force stop
type: Ctrl+D (EOF)
```

### Programmatic Stopping

```python
# In your code
import asyncio
from trae_agent.agent import TraeAgent

async def run_with_timeout(agent, task, timeout=300):
    try:
        result = await asyncio.wait_for(
            agent.execute_task(),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        print("Task timed out")
        return None
```

## Exporting Reasoning Traces/Trajectories

### Automatic Trajectory Recording

All agent executions automatically record detailed trajectories:

```bash
# Basic execution - auto-generates filename
uv run trae-cli run "Create a Python script"
# Saves: trajectory_20250612_220546.json

# Custom filename
uv run trae-cli run "Debug the auth module" --trajectory-file debug_session.json
```

### Trajectory File Structure

JSON file contains:

- **Task description**
- **LLM interactions** (messages, responses, tool calls)
- **Agent steps** (state transitions, reflections)
- **Execution metrics** (timestamps, token usage)
- **Final result**

### Programmatic Export

```python
from trae_agent.agent import TraeAgent

# Create agent
agent = TraeAgent(config)

# Set up trajectory recording
trajectory_path = agent.setup_trajectory_recording("my_analysis.json")

# Run task
agent.new_task("Analyze this codebase", task_args)
await agent.execute_task()

print(f"Trajectory saved to: {trajectory_path}")
```

### Trajectory Analysis

```python
import json

def analyze_trajectory(trajectory_file):
    with open(trajectory_file) as f:
        data = json.load(f)
    
    print(f"Task: {data['task']}")
    print(f"Duration: {data['execution_time']}s")
    print(f"Steps: {len(data['agent_steps'])}")
    print(f"LLM calls: {len(data['llm_interactions'])}")
    
    # Analyze tool usage
    tools_used = {}
    for step in data['agent_steps']:
        for tool_call in step.get('tool_calls', []):
            tool_name = tool_call['name']
            tools_used[tool_name] = tools_used.get(tool_name, 0) + 1
    
    print("Tools used:", tools_used)
```

## Runtime Metrics Information

### Available Metrics

The trajectory file provides comprehensive runtime metrics:

#### Time Metrics

- **Start time**: ISO timestamp when execution began
- **End time**: ISO timestamp when execution completed
- **Execution time**: Total duration in seconds
- **Step timestamps**: Precise timing for each agent step

#### Token Usage

- **Input tokens**: Tokens sent to LLM
- **Output tokens**: Tokens received from LLM
- **Cache tokens**: Cached token usage (Anthropic-specific)
- **Reasoning tokens**: Model reasoning tokens (when available)
- **Total tokens**: Sum of all tokens used

#### Cost Calculation

```python
def calculate_cost(trajectory_file, model_pricing):
    """Calculate approximate cost from trajectory data."""
    with open(trajectory_file) as f:
        data = json.load(f)
    
    total_input_tokens = 0
    total_output_tokens = 0
    
    for interaction in data['llm_interactions']:
        usage = interaction['response']['usage']
        total_input_tokens += usage.get('input_tokens', 0)
        total_output_tokens += usage.get('output_tokens', 0)
    
    model = data['model']
    pricing = model_pricing.get(model, {'input': 0.0015, 'output': 0.002})
    
    input_cost = (total_input_tokens / 1000) * pricing['input']
    output_cost = (total_output_tokens / 1000) * pricing['output']
    
    return {
        'model': model,
        'input_tokens': total_input_tokens,
        'output_tokens': total_output_tokens,
        'total_cost': input_cost + output_cost,
        'input_cost': input_cost,
        'output_cost': output_cost
    }

# Example usage
pricing = {
    'gpt-4o': {'input': 0.005, 'output': 0.015},
    'claude-sonnet-4-20250514': {'input': 0.003, 'output': 0.015},
    'gemini-2.5-flash': {'input': 0.00015, 'output': 0.0006}
}

metrics = calculate_cost("trajectory_20250612_220546.json", pricing)
print(f"Total cost: ${metrics['total_cost']:.4f}")
```

### Real-time Metrics Display

During execution, the agent displays:

- Current step number
- Tool being executed
- Progress indicators
- Final summary with trajectory file location

### Monitoring Multiple Runs

```bash
# Create metrics dashboard
cat > monitor_runs.sh << 'EOF'
#!/bin/bash
for file in trajectory_*.json; do
    echo "=== $file ==="
    python3 -c "
import json
with open('$file') as f:
    data = json.load(f)
print(f'Task: {data[\"task\"][:50]}...')
print(f'Time: {data[\"execution_time\"]}s')
print(f'Success: {data[\"success\"]}')
print()
"
done
EOF

chmod +x monitor_runs.sh
./monitor_runs.sh
```

## Quick Start Examples

### Basic Task

```bash
# Setup environment
uv venv
uv sync --all-extras

# Run on current repo
uv run trae-cli run "Add comprehensive tests for the utils module"

# Run on specific repo
uv run trae-cli run "Implement user authentication" --working-dir /path/to/webapp

# Run with specific provider
uv run trae-cli run "Optimize database queries" --provider google --model gemini-2.5-pro
```

### Advanced Usage

```bash
# Run with custom config and trajectory
uv run trae-cli run "Refactor the API layer" \
  --working-dir ./my-project \
  --config-file custom_config.json \
  --trajectory-file refactor_trace.json \
  --max-steps 50

# Interactive session
uv run trae-cli interactive \
  --provider anthropic \
  --model claude-sonnet-4-20250514 \
  --trajectory-file interactive_session.json
```

### Configuration Management

```bash
# Check current configuration
uv run trae-cli show-config

# Show available tools
uv run trae-cli tools
```
