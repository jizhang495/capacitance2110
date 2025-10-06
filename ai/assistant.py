"""AI assistant for capacitance monitor with OpenAI integration."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from PySide6.QtCore import QObject, Signal

from .tools import MeasurementTools, ToolResult


class AIAssistant(QObject):
    """AI assistant that can execute measurement tasks through natural language."""
    
    # Signals for UI updates
    message_received = Signal(str)  # AI response message
    tool_executed = Signal(str, str)  # tool_name, result_message
    error_occurred = Signal(str)  # error_message
    
    def __init__(self, tools: MeasurementTools, api_key: Optional[str] = None):
        super().__init__()
        self._tools = tools
        self._logger = logging.getLogger(__name__)
        
        # Sequence confirmation state
        self._pending_sequence = None
        self._waiting_for_confirmation = False
        
        # Initialize OpenAI client
        # Try to get API key from parameter, then from environment variables
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            self._logger.warning("No OpenAI API key found in environment variables. AI features will be disabled.")
            self._logger.info("Please set OPENAI_API_KEY in your .env file or environment variables.")
            self._client = None
        else:
            self._client = OpenAI(api_key=self._api_key)
            self._logger.info("OpenAI API key loaded from environment variables.")
        
        # Connect tool signals
        self._tools.tool_executed.connect(self.tool_executed)
        
        # Conversation history
        self._conversation_history: List[Dict[str, str]] = []
        
        # System prompt
        self._system_prompt = """You are an AI assistant for a capacitance measurement system. You can help users control measurements, export data, and automate tasks.

Available tools:
- start_measurement: Start capacitance measurement (will auto-create mock instrument if none selected)
- stop_measurement: Stop capacitance measurement  
- export_csv: Export measurement data to CSV file
- clear_data: Clear all measurement data
- get_status: Get current measurement status
- schedule_measurement: Start measurement for specified duration with optional auto-export

When users ask to "measure for X time and export as CSV", use the schedule_measurement tool with auto_export=True.

For COMPLEX SEQUENCES (multiple actions with timing), use plan_measurement_sequence and execute_measurement_sequence:
1. Parse the user's request into a sequence of timed actions
2. Present the sequence to the user for confirmation
3. Execute the sequence if confirmed

SEQUENCE FORMAT:
Each step should have: {"action": "action_name", "time_offset": seconds}
Available actions: "start_measurement", "stop_measurement", "export_csv", "clear_data", "wait"

EXAMPLE SEQUENCE:
User: "start measurement and stop in 10 seconds. Then immediately save as csv and start next measurement after 5 seconds. Next measurement lasts 15 seconds, then stop and save as csv."

Parsed sequence:
[
  {"action": "start_measurement", "time_offset": 0},
  {"action": "stop_measurement", "time_offset": 10},
  {"action": "export_csv", "time_offset": 10.1},
  {"action": "wait", "time_offset": 15},
  {"action": "start_measurement", "time_offset": 15},
  {"action": "stop_measurement", "time_offset": 30},
  {"action": "export_csv", "time_offset": 30.1}
]

TIME FORMATS SUPPORTED:
- Seconds: "10 seconds", "30 seconds", "1 minute 30 seconds"
- Minutes: "5 minutes", "10 minutes", "1 hour 30 minutes"
- Hours: "2 hours", "1 hour 15 minutes"
- Combined: "1 hour 30 minutes 45 seconds"

Use duration_seconds for seconds, duration_minutes for minutes. You can combine both (e.g., duration_seconds=30, duration_minutes=5 for 5 minutes 30 seconds).

IMPORTANT: At least one duration parameter must be specified and greater than 0. If a user asks for "0 time" or doesn't specify a duration, ask them to specify a valid duration.

The system can work with both mock instruments (for testing) and real Keithley 2110 instruments. If no instrument is selected, it will automatically use the mock instrument for testing purposes.

Be helpful, clear, and confirm actions before executing them. Always explain what you're doing and provide status updates. Keep responses concise and focused on the task at hand."""
    
    def set_api_key(self, api_key: str) -> None:
        """Set the OpenAI API key."""
        self._api_key = api_key
        if api_key:
            self._client = OpenAI(api_key=api_key)
            self._logger.info("OpenAI API key set successfully")
        else:
            self._client = None
            self._logger.warning("OpenAI API key cleared")
    
    def is_available(self) -> bool:
        """Check if AI assistant is available (has API key)."""
        return self._client is not None
    
    def send_message(self, user_message: str) -> None:
        """Send a message to the AI assistant and get response."""
        if not self.is_available():
            self.error_occurred.emit("AI assistant is not available. Please set your OpenAI API key in settings.")
            return
        
        try:
            # Add user message to history
            self._conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Get AI response
            response = self._get_ai_response()
            
            # Add AI response to history
            self._conversation_history.append({
                "role": "assistant", 
                "content": response
            })
            
            # Emit response
            self.message_received.emit(response)
            
        except Exception as e:
            self._logger.error(f"Error processing message: {e}")
            self.error_occurred.emit(f"Error processing message: {str(e)}")
    
    def _get_ai_response(self) -> str:
        """Get response from OpenAI with tool calling."""
        if not self._client:
            return "AI assistant is not available. Please set your OpenAI API key."
        
        # Prepare messages
        messages = [{"role": "system", "content": self._system_prompt}]
        messages.extend(self._conversation_history)
        
        # Prepare tools for OpenAI
        tools = self._prepare_tools_for_openai()
        
        try:
            # Make API call
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0 # 0.7
            )
            
            message = response.choices[0].message
            
            # Handle tool calls
            if message.tool_calls:
                return self._handle_tool_calls(message.tool_calls)
            else:
                return message.content or "No response received"
                
        except Exception as e:
            self._logger.error(f"OpenAI API error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _prepare_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Prepare tools in OpenAI format."""
        available_tools = self._tools.get_available_tools()
        tools = []
        
        for tool in available_tools:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Add parameters
            for param_name, param_info in tool.get("parameters", {}).items():
                param_def = {
                    "type": param_info["type"],
                    "description": param_info["description"]
                }
                
                # Handle complex types like arrays with items
                if "items" in param_info:
                    param_def["items"] = param_info["items"]
                
                tool_def["function"]["parameters"]["properties"][param_name] = param_def
                
                if param_info.get("required", False):
                    tool_def["function"]["parameters"]["required"].append(param_name)
            
            tools.append(tool_def)
        
        return tools
    
    def _handle_tool_calls(self, tool_calls: List[Any]) -> str:
        """Handle tool calls from OpenAI."""
        results = []
        
        # First, add the assistant's message with tool calls to conversation history
        assistant_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
                for tool_call in tool_calls
            ]
        }
        self._conversation_history.append(assistant_message)
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                self._logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # Execute tool
                result = self._execute_tool(tool_name, tool_args)
                
                # Add tool result to conversation
                self._conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps({
                        "success": result.success,
                        "message": result.message,
                        "data": result.data
                    })
                })
                
                results.append(f"✓ {tool_name}: {result.message}")
                
            except Exception as e:
                self._logger.error(f"Error executing tool {tool_name}: {e}")
                results.append(f"✗ {tool_name}: Error - {str(e)}")
        
        return "\n".join(results)
    
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with given arguments."""
        if not hasattr(self._tools, tool_name):
            return ToolResult(
                success=False,
                message=f"Unknown tool: {tool_name}"
            )
        
        try:
            tool_method = getattr(self._tools, tool_name)
            return tool_method(**tool_args)
        except Exception as e:
            self._logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolResult(
                success=False,
                message=f"Error executing {tool_name}: {str(e)}"
            )
    
    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self._conversation_history.clear()
        self._logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self._conversation_history.copy()
    
    def confirm_sequence_execution(self, sequence: List[Dict[str, Any]], user_message: str) -> None:
        """Ask user to confirm a measurement sequence before execution."""
        # Format the sequence for display
        summary_lines = []
        for step in sequence:
            time_str = self._format_time_offset(step["time_offset"])
            action_str = step["action"]
            if "duration" in step:
                action_str += f" for {step['duration']}"
            summary_lines.append(f"At {time_str} - {action_str}")
        
        summary = "\n".join(summary_lines)
        
        confirmation_message = f"""I've parsed your request into this measurement sequence:

{summary}

Do you want me to proceed with this sequence? (Type 'yes' to confirm or 'no' to cancel)"""
        
        self.message_received.emit(confirmation_message)
        
        # Store the sequence for potential execution
        self._pending_sequence = sequence
        self._waiting_for_confirmation = True
    
    def _format_time_offset(self, seconds: float) -> str:
        """Format time offset in seconds to human readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"
