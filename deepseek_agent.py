import os
import json
import subprocess
from openai import OpenAI

# 1. LLM Client & API Configuration
# Initialize with DeepSeek API Base URL and fetch API Key securely
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    print("WARNING: DEEPSEEK_API_KEY environment variable not set. Please export it.")

client = OpenAI(
    api_key=api_key or "your-api-key-here",
    base_url="https://api.deepseek.com"
)
MODEL = "deepseek-chat"

# 2. Embedded System Instructions (Brain Directives)
SYSTEM_PROMPT = """You are Jarvis, the central reasoning engine of an autonomous AI assistant.
Directives:
1. Multi-Step Decomposition: Break down user goals into logical, sequential steps before execution.
2. Autonomous Tool Calling: Trigger available tools (system commands, file I/O, web utilities) using valid JSON arguments.
3. Self-Healing & Error Handling: If a tool returns an error or failure, analyze the output trace, adjust parameters or commands, and retry independently.
4. Unsupervised Execution: Continue the Thought -> Action -> Observation cycle autonomously without prompting the user for intermediate confirmations.
5. Final Delivery: Provide a clean, structured summary once all sub-tasks are fully resolved."""

# 3. Execution Architecture & Tools (Python subprocess & os)
def execute_command(command: str) -> str:
    """Execute a system shell command and return its output."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        return output if output.strip() else "[Command completed successfully with no output]"
    except Exception as e:
        return f"Command execution failed: {str(e)}"

def read_file(filepath: str) -> str:
    """Read the contents of a local file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"File read error: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Write text content to a local file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {filepath}."
    except Exception as e:
        return f"File write error: {str(e)}"

# OpenAI-Compatible Tool Function Schemas
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a system shell command (Windows CMD/PowerShell) and return its output. Use for environment checks, file management, scripts execution, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents from a file on the local file system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute or relative path to the file."
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file on the local file system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute or relative path to the file."
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write."
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    }
]

# Mapping tool names to actual Python functions
AVAILABLE_FUNCTIONS = {
    "execute_command": execute_command,
    "read_file": read_file,
    "write_file": write_file
}

class AutonomousAgent:
    def __init__(self, max_steps=15):
        # Initialize conversation with the core system prompt
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.max_steps = max_steps

    def run(self, user_prompt: str) -> str:
        """The core ReAct Loop (Reasoning + Acting)"""
        self.messages.append({"role": "user", "content": user_prompt})
        step = 0
        
        while step < self.max_steps:
            print(f"\n[Cycle {step + 1}/{self.max_steps}] Thinking...")
            
            try:
                # 1. Ask DeepSeek for the next action or final answer
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    tools=TOOLS,
                    tool_choice="auto"
                )
            except Exception as e:
                return f"API Connection Error: {e}"

            message = response.choices[0].message
            # We MUST append the assistant's message back to the context history exactly as provided
            self.messages.append(message)
            
            # 2. Check if the model wants to call tools
            if getattr(message, 'tool_calls', None):
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    
                    print(f"🔧 Triggering Tool: {function_name}")
                    print(f"   Args: {json.dumps(function_args)}")
                    
                    function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
                    if function_to_call:
                        # 3. Execute the tool autonomously
                        try:
                            function_response = function_to_call(**function_args)
                        except Exception as e:
                            function_response = f"Execution crash: {str(e)}"
                    else:
                        function_response = f"Error: Tool '{function_name}' does not exist."
                        
                    # Truncate output for terminal printing safety, but keep full output for model
                    print(f"   Result: {str(function_response)[:200]}...\n")
                    
                    # 4. Feed the tool output back into the message history for the next iteration
                    self.messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(function_response)
                        }
                    )
            else:
                # 5. Final Delivery - No more tool calls requested
                print("🏁 Task Completed autonomously.")
                return message.content
                
            step += 1
            
        print("\n[!] Maximum step safety limit reached.")
        return "Task halted: Max execution limit reached to prevent infinite loops."

if __name__ == "__main__":
    print("="*50)
    print(" Jarvis DeepSeek Autonomous Core (ReAct Engine)")
    print("="*50)
    print("Type 'exit' to terminate.\n")
    
    agent = AutonomousAgent(max_steps=15)
    
    while True:
        try:
            user_input = input("USER > ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue
                
            final_response = agent.run(user_input)
            print(f"\nJARVIS > {final_response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nTerminating process...")
            break
