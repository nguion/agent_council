# OpenAI Agents SDK with GPT-5.1: Comprehensive Usage Guide

## Overview

The OpenAI Agents SDK is a framework designed to simplify the creation of agentic applications that leverage advanced models like GPT-5.1. It provides tools to integrate models with additional context, web access, reasoning capabilities, and various built-in tools for enhanced functionality.

## Key Features

### 1. Model Integration
- **GPT-5.1 Support**: Full support for GPT-5.1 model with optimized configurations
- **Model Settings**: Configurable reasoning effort levels and text verbosity
- **Extended Capabilities**: Support for multimodal inputs and outputs

### 2. Built-in Tools
- **WebSearchTool**: Enables agents to perform web searches for real-time information
- **File Operations**: Tools for reading, writing, and managing files
- **Code Execution**: Shell and code interpretation capabilities
- **Custom Tools**: Ability to define custom tools for specific use cases

### 3. Reasoning Configuration
- **Reasoning Effort Levels**: 
  - `'none'`: No reasoning (fastest, for latency-sensitive tasks)
  - `'low'`: Low reasoning effort
  - `'medium'`: Medium reasoning effort (balanced)
  - `'high'`: High reasoning effort (most thorough)
- **Default**: GPT-5.1 uses `'none'` by default for quick responses

### 4. Advanced Features
- **Prompt Caching**: Extended prompt caching up to 24 hours for reduced latency and cost
- **Tool Choice Control**: Restrict agents to specific tools for safety and predictability
- **Async Support**: Full async/await support for concurrent operations

## Installation

```bash
pip install openai-agents
```

**Requirements:**
- Python 3.8 or higher
- OpenAI API key
- OpenAI SDK (automatically installed as dependency)

## Basic Usage

### 1. Environment Setup

Create a `.env` file with your OpenAI API key:

```env
OPENAI_API_KEY=your_api_key_here
```

### 2. Simple Agent with Web Access

```python
import os
from dotenv import load_dotenv
from openai_agents import Agent, WebSearchTool, set_default_openai_api

# Load environment variables
load_dotenv()

# Set the OpenAI API key
set_default_openai_api(os.getenv("OPENAI_API_KEY"))

# Create agent with web search capability
agent = Agent(
    name="WebEnabledAgent",
    instructions="You are a helpful assistant with web access and reasoning capabilities.",
    model="gpt-5.1",
    tools=[WebSearchTool()],
    model_settings={
        "reasoning": {"effort": "medium"},
        "text": {"verbosity": "low"}
    }
)

# Run the agent (async)
async def main():
    response = await agent.run("What is the latest news on artificial intelligence?")
    print(response)

import asyncio
asyncio.run(main())
```

## GPT-5.1 Specific Configuration

### Model Settings

```python
model_settings = {
    "reasoning": {
        "effort": "medium"  # Options: 'none', 'low', 'medium', 'high'
    },
    "text": {
        "verbosity": "low"  # Controls response verbosity
    }
}
```

### Important API Differences

**Key differences when using GPT-5.1:**
- Use `max_completion_tokens` instead of `max_tokens`
- Reasoning effort can be set via `model_settings`
- Prompt caching available with `prompt_cache_retention='24h'`

### Example with Full Configuration

```python
from openai_agents import Agent, WebSearchTool, ModelSettings

agent = Agent(
    name="AdvancedAgent",
    model="gpt-5.1",
    instructions="You are an advanced AI assistant with web access and enhanced reasoning.",
    tools=[WebSearchTool()],
    model_settings=ModelSettings(
        reasoning_effort="medium",
        text_verbosity="low"
    )
)
```

## Tool Usage

### Web Search Tool

```python
from openai_agents import WebSearchTool

# Initialize web search tool
web_search = WebSearchTool()

# Add to agent
agent = Agent(
    tools=[web_search],
    # ... other settings
)
```

### Multiple Tools

```python
from openai_agents import Agent, WebSearchTool, FileSearchTool

agent = Agent(
    tools=[
        WebSearchTool(),
        FileSearchTool()
    ],
    # ... other settings
)
```

## Advanced Patterns

### Custom Tools

```python
from openai_agents import Agent, CustomTool

# Define custom tool
custom_tool = CustomTool(
    name="my_tool",
    description="Description of what the tool does"
)

agent = Agent(
    tools=[custom_tool],
    # ... other settings
)
```

### Tool Choice Control

```python
agent = Agent(
    # ... settings ...
    tool_choice={
        "type": "allowed_tools",
        "mode": "auto",
        "tools": [
            {"type": "function", "name": "web_search"},
            {"type": "function", "name": "file_search"}
        ]
    }
)
```

### Prompt Caching

```python
# When making direct API calls (not through Agents SDK)
response = client.chat.completions.create(
    model="gpt-5.1",
    messages=[...],
    prompt_cache_retention='24h'  # Cache prompts for 24 hours
)
```

## Error Handling

```python
from openai import BadRequestError

try:
    response = await agent.run("Your query here")
except BadRequestError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Reasoning Effort Selection**:
   - Use `'none'` for simple, fast queries
   - Use `'medium'` for balanced performance
   - Use `'high'` for complex reasoning tasks

2. **Tool Selection**:
   - Only include tools that are necessary for your use case
   - Use `tool_choice` to restrict available tools for safety

3. **Async Operations**:
   - Always use async/await for agent operations
   - Use `asyncio.run()` or async context managers

4. **Environment Variables**:
   - Never hardcode API keys
   - Use `.env` files with `python-dotenv`

5. **Error Handling**:
   - Always wrap agent calls in try-except blocks
   - Handle rate limits and API errors gracefully

## GPT-5/5.1 Prompting Best Practices

Effective prompting is crucial for leveraging the full capabilities of GPT-5 and GPT-5.1. The following best practices are compiled from OpenAI's official documentation and recommendations.

### 1. Clarity and Specificity

**Be explicit and unambiguous in your prompts.** Provide sufficient context and clearly articulate the desired outcome, format, and any constraints.

**Good Example:**
```
Summarize the following article in three bullet points highlighting the main arguments. 
Focus on the economic implications discussed in paragraphs 2-5.
```

**Poor Example:**
```
Summarize this article.
```

**Key Points:**
- Specify the exact format you want (bullet points, paragraphs, JSON, etc.)
- Include relevant context and constraints
- Define the scope of the task clearly

### 2. Structured Prompting

**Organize prompts into distinct sections** to help the model maintain focus and deliver coherent responses, especially during extended interactions.

**Recommended Structure:**
```
Role: You are an expert in renewable energy.

Objective: Provide an overview of the latest advancements in solar panel technology.

Context: The audience consists of technical professionals with engineering backgrounds.

Instructions: 
- Include recent statistics from 2024
- Compare efficiency rates across different panel types
- Highlight cost-benefit analysis

Format: Present the information in a concise report format with clear sections.

Constraints: Keep the response under 500 words.
```

**Benefits:**
- Helps the model understand its role and purpose
- Maintains focus throughout the conversation
- Makes it easier to refine specific sections

### 3. Reasoning Mode Selection

**Choose the appropriate reasoning effort level** based on your task requirements to optimize response times and accuracy.

**Reasoning Effort Guidelines:**

- **`'none'`**: 
  - Use for: Simple queries, quick responses, low-latency interactions
  - Examples: Simple fact retrieval, basic formatting, straightforward Q&A
  - Performance: Fastest response time

- **`'low'`**: 
  - Use for: Basic analysis, simple problem-solving
  - Examples: Summarization, basic data interpretation
  - Performance: Fast with light reasoning

- **`'medium'`** (Recommended for most cases):
  - Use for: Balanced tasks requiring some analysis
  - Examples: Research summaries, moderate complexity problem-solving
  - Performance: Balanced speed and depth

- **`'high'`**: 
  - Use for: Complex reasoning, multi-step problems, critical analysis
  - Examples: Code review, complex problem-solving, detailed analysis
  - Performance: Slower but most thorough

**Example:**
```python
# For simple queries
model_settings={"reasoning": {"effort": "none"}}

# For complex analysis
model_settings={"reasoning": {"effort": "high"}}
```

### 4. Role Assignment

**Explicitly define the role** you want GPT-5.1 to assume to enhance relevance and precision of responses.

**Good Examples:**
```
"You are a meticulous code-review agent specializing in Python security best practices."

"You are a financial analyst with expertise in cryptocurrency markets."

"You are a technical writer who explains complex concepts in simple terms."
```

**Benefits:**
- Tailors the model's behavior to specific domains
- Improves accuracy and relevance
- Sets appropriate expectations for tone and depth

### 5. Control Output Verbosity

**Specify the desired level of detail** in responses to match your requirements.

**Techniques:**

1. **Explicit Length Instructions:**
   ```
   "Provide a brief summary in two sentences."
   "Write a detailed analysis in 500-700 words."
   ```

2. **Use Verbosity Settings:**
   ```python
   model_settings={
       "text": {"verbosity": "low"}  # Options: 'low', 'medium', 'high'
   }
   ```

3. **Format Specifications:**
   ```
   "Provide a concise bullet-point list."
   "Give a detailed paragraph explanation."
   ```

### 6. Emphasize Persistence and Completeness

**GPT-5.1 may err on the side of conciseness.** Explicitly instruct the model to provide comprehensive responses when necessary.

**Good Practices:**
```
"Provide a complete analysis, ensuring all aspects are covered."

"Think through this problem step-by-step and show your reasoning."

"Be thorough in your explanation, including relevant details and examples."
```

**For Agentic Workflows:**
```
"Continue working on this task until it is fully resolved. Do not stop at partial solutions."
```

### 7. Self-Reflection Techniques

**Encourage the model to evaluate and refine its responses** by prompting it to define quality criteria before generating an answer.

**Example:**
```
"Before responding, outline the key elements of a comprehensive market analysis report. 
Then provide the analysis following that structure."
```

**Benefits:**
- Leads to more thoughtful and structured outputs
- Helps the model self-correct
- Improves consistency and quality

### 8. Metaprompting for Debugging

**Use GPT-5.1 to analyze and improve your prompts** by asking the model to identify ambiguities or errors and suggest refinements.

**Example:**
```
"Review the following prompt for clarity and coherence, and suggest improvements:

[Your original prompt here]

Identify any ambiguities, missing context, or unclear instructions."
```

**Use Cases:**
- Refining complex prompts
- Identifying edge cases
- Improving prompt structure

### 9. Control Agentic Behavior

**Adjust the model's proactivity** by setting clear guidelines on how it should handle tasks, especially in agentic workflows.

**Examples:**
```
"Proceed with the task only after receiving explicit confirmation for each major step."

"Take initiative to complete the task, but ask for clarification if any step is ambiguous."

"Work autonomously but provide status updates every 100 tokens of output."
```

**Key Considerations:**
- Balance between autonomy and control
- Define scope of allowed actions
- Set clear boundaries for tool usage

### 10. Iterative Refinement

**Prompt engineering is an iterative process.** Start with an initial prompt, review the response, and refine based on results.

**Refinement Process:**
1. **Initial Prompt**: Start with a basic version
2. **Review Response**: Analyze what worked and what didn't
3. **Identify Issues**: Note ambiguities, missing context, or format problems
4. **Refine**: Adjust wording, add context, or simplify
5. **Test Again**: Iterate until results meet requirements

**Common Refinements:**
- Adding more specific instructions
- Clarifying format requirements
- Providing examples or templates
- Breaking complex tasks into steps

### 11. Use Descriptive Language for Tone

**Specify the desired tone** using descriptive adjectives to guide the model's style.

**Examples:**
```
"Write in a formal, professional tone suitable for a business proposal."

"Use a friendly, conversational style as if explaining to a friend."

"Maintain a technical, precise tone appropriate for a research paper."
```

### 12. Provide Examples and Templates

**Include examples or templates** in your prompts to guide the desired output format.

**Example:**
```
"Format your response as a JSON object with the following structure:
{
  'summary': 'brief summary here',
  'key_points': ['point1', 'point2', 'point3'],
  'recommendations': ['rec1', 'rec2']
}
"
```

### 13. Handle Multi-Step Tasks

**Break down complex tasks** into clear steps and guide the model through the process.

**Example:**
```
"Complete this task in the following steps:
1. First, analyze the problem and identify key factors
2. Second, research relevant information using web search
3. Third, synthesize findings into a coherent solution
4. Finally, provide recommendations with justification"
```

### 14. Specify Constraints and Boundaries

**Clearly define what the model should and shouldn't do** to prevent unwanted behavior.

**Examples:**
```
"Do not make assumptions about data not provided. Ask for clarification if needed."

"Only use information from the provided sources. Do not add external knowledge."

"Stay within the scope of the question. Do not provide tangential information."
```

### Prompting Checklist

Before sending a prompt to GPT-5.1, verify:

- [ ] Is the task clearly defined?
- [ ] Is the desired format specified?
- [ ] Is the appropriate reasoning effort level set?
- [ ] Is the role/context provided?
- [ ] Are constraints and boundaries defined?
- [ ] Is the tone/style specified?
- [ ] Are examples or templates included (if needed)?
- [ ] Is the prompt structured for clarity?

### References

- [OpenAI Prompt Engineering Best Practices](https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt)
- [GPT-5.1 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5.1_prompting_guide/)
- [GPT-5 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide)
- [Using GPT-5.1 - OpenAI API](https://platform.openai.com/docs/guides/gpt-5)

## Common Use Cases

### 1. Research Assistant
```python
agent = Agent(
    name="ResearchAssistant",
    instructions="You are a research assistant that finds and summarizes information.",
    model="gpt-5.1",
    tools=[WebSearchTool()],
    model_settings={"reasoning": {"effort": "medium"}}
)
```

### 2. Code Assistant
```python
from openai_agents import ShellTool, ApplyPatchTool

agent = Agent(
    name="CodeAssistant",
    instructions="You are a coding assistant that can execute and modify code.",
    model="gpt-5.1",
    tools=[ShellTool(), ApplyPatchTool()],
    model_settings={"reasoning": {"effort": "high"}}
)
```

### 3. Information Retrieval
```python
agent = Agent(
    name="InfoRetriever",
    instructions="Retrieve and summarize information from the web.",
    model="gpt-5.1",
    tools=[WebSearchTool()],
    model_settings={"reasoning": {"effort": "low"}}
)
```

## API Reference Summary

### Agent Class

```python
Agent(
    name: str,
    instructions: str,
    model: str = "gpt-5.1",
    tools: List[Tool] = [],
    model_settings: dict = {},
    tool_choice: dict = None
)
```

### Model Settings Structure

```python
{
    "reasoning": {
        "effort": "none" | "low" | "medium" | "high"
    },
    "text": {
        "verbosity": "low" | "medium" | "high"
    }
}
```

### Common Tools

- `WebSearchTool()`: Web search capabilities
- `FileSearchTool()`: File system search
- `ShellTool()`: Command-line execution
- `ApplyPatchTool()`: File modification
- `CustomTool()`: User-defined tools

## Resources

- **Official Documentation**: [OpenAI Agents SDK](https://platform.openai.com/docs/guides/agents-sdk/)
- **GPT-5.1 Model Docs**: [GPT-5.1 Documentation](https://platform.openai.com/docs/models/gpt-5.1/)
- **AgentKit Introduction**: [Introducing AgentKit](https://openai.com/index/introducing-agentkit/)
- **Video Tutorial**: [How to Build an Agent with the OpenAI Agents SDK](https://www.youtube.com/watch?v=0Z7u6DTDZ8o)

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure `openai-agents` is installed: `pip install openai-agents`
   - Check Python version (3.8+)

2. **API Key Errors**:
   - Verify `.env` file exists and contains `OPENAI_API_KEY`
   - Check that `load_dotenv()` is called before using the key

3. **Model Not Found**:
   - Verify GPT-5.1 is available in your API account
   - Check model name spelling: `"gpt-5.1"`

4. **Tool Errors**:
   - Ensure tools are properly initialized
   - Check tool permissions and availability

5. **Async Errors**:
   - Always use `await` with agent.run()
   - Use `asyncio.run()` for top-level async calls

## Version Information

- **SDK Version**: 0.6.1 (as of latest)
- **OpenAI SDK**: 2.8.0+
- **Python**: 3.8+

---

*Last Updated: Based on latest research and documentation as of 2024*

