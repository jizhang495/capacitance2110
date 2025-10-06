"""Example script demonstrating AI assistant usage."""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import AppConfig
from ai import AIAssistant, MeasurementTools
from core.controller import MeasurementController


def main():
    """Demonstrate AI assistant usage."""
    print("AI Assistant Example for Capacitance Monitor")
    print("=" * 50)
    
    # Create configuration
    config = AppConfig()
    
    # Create measurement controller
    controller = MeasurementController(config)
    
    # Create AI tools
    ai_tools = MeasurementTools(controller, config)
    
    # Create AI assistant (without API key for demo)
    ai_assistant = AIAssistant(ai_tools)
    
    print("Available AI Tools:")
    print("-" * 20)
    for tool in ai_tools.get_available_tools():
        print(f"• {tool['name']}: {tool['description']}")
        if tool.get('parameters'):
            print("  Parameters:")
            for param_name, param_info in tool['parameters'].items():
                required = " (required)" if param_info.get('required', False) else ""
                print(f"    - {param_name}: {param_info['description']}{required}")
        print()
    
    print("Example Usage:")
    print("-" * 15)
    print("1. Set your OpenAI API key in the application settings")
    print("2. Enable AI Assistant in the control panel")
    print("3. Try these commands in the chat:")
    print("   • 'Start measurement'")
    print("   • 'Measure for 5 minutes and export as CSV'")
    print("   • 'Stop measurement'")
    print("   • 'Export current data'")
    print("   • 'What's the current status?'")
    print("   • 'Clear all data'")
    print()
    print("The AI will understand natural language and execute the appropriate tools!")


if __name__ == "__main__":
    main()
