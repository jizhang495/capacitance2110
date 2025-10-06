# AI Assistant Features

The Capacitance Monitor now includes an AI assistant powered by OpenAI's GPT-4 that can help you control measurements through natural language commands.

## Setup

1. **Install Dependencies**: The AI features require the `openai` package, which is automatically installed with the application.

2. **Get OpenAI API Key**: 
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Create an API key in your account settings
   - Copy the API key for use in the application

3. **Configure AI Assistant**:
   - **Option 1 (Recommended)**: Create a `.env` file in the same directory as `app.py` and add:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
   - **Option 2**: Open the application, go to the control panel, find the "AI Assistant" section, check "Enable AI Assistant", and click "Set API Key"
   - The AI assistant will automatically load the API key from the `.env` file on startup

## Features

### Natural Language Control
The AI assistant understands natural language commands and can execute measurement tasks automatically. You can describe what you want to do in plain English.

### Available Commands

#### Basic Measurement Control
- **"Start measurement"** - Begins capacitance measurement (auto-creates mock instrument if none selected)
- **"Stop measurement"** - Stops current measurement
- **"What's the current status?"** - Shows measurement status and statistics

#### Data Management
- **"Export current data"** - Saves measurement data to CSV
- **"Export data as 'filename'"** - Saves with custom filename
- **"Clear all data"** - Removes all measurement data and completely clears the graph display

#### Automated Tasks
- **"Measure for 5 minutes and export as CSV"** - Starts measurement, waits 5 minutes, stops, and exports data
- **"Run a 10-minute measurement"** - Automated measurement for specified duration
- **"Take a 2-minute sample and save it"** - Short measurement with auto-export

### Example Conversations

```
You: "I want to measure capacitance for 3 minutes and then export the data"

AI Assistant: I'll help you with that! I'll start a measurement for 3 minutes and automatically export the data when it's complete.

✓ schedule_measurement: Measurement scheduled for 3.0 minutes. Will stop at 14:35:42.
```

```
You: "What's the current status?"

AI Assistant: Let me check the current measurement status for you.

✓ get_status: Measurement is running. Samples: 1247, Errors: 0
```

```
You: "Export the current data as 'test_measurement'"

AI Assistant: I'll export the current measurement data with your specified filename.

✓ export_csv: Data exported successfully to /path/to/app/measurements/test_measurement.csv
```

## How It Works

1. **Natural Language Processing**: The AI assistant uses OpenAI's GPT-4o-mini to understand your commands
2. **Tool Calling**: The AI can call specific functions (tools) to control the measurement system
3. **Automated Execution**: Complex tasks like "measure for X minutes and export" are broken down into steps and executed automatically
4. **Real-time Feedback**: You get immediate feedback on what actions are being performed

## Technical Details

### AI Tools Available
- `start_measurement`: Start capacitance measurement
- `stop_measurement`: Stop capacitance measurement
- `export_csv`: Export measurement data to CSV file
- `clear_data`: Clear all measurement data
- `get_status`: Get current measurement status and statistics
- `schedule_measurement`: Start measurement for specified duration with optional auto-export

### Timer System
The AI assistant includes a built-in timer system that can:
- Schedule measurements for specific durations
- Automatically stop measurements after the specified time
- Optionally export data immediately after stopping
- Handle multiple scheduled tasks simultaneously

### Security
- Your OpenAI API key is stored locally in the application configuration
- API calls are made directly to OpenAI's servers
- No measurement data is sent to external services (only your commands)

## Troubleshooting

### AI Assistant Not Responding
- Check that you have a valid OpenAI API key set
- Ensure you have an active internet connection
- Verify that AI Assistant is enabled in the settings

### Commands Not Working
- The AI assistant will automatically create a mock instrument if none is selected
- For real instruments, make sure an instrument is selected and connected
- Check that the measurement system is properly configured
- Try rephrasing your command in simpler terms

### API Key Issues
- Verify your OpenAI API key is correct
- Check that you have sufficient API credits
- Ensure your OpenAI account is active

## File Structure

The application now organizes files in the same directory as `app.py`:

```
capacitance2110/
├── app.py                    # Main application
├── .env                      # Environment variables (API keys)
├── measurements/             # CSV export files
│   └── measurement_*.csv
├── config/                   # Configuration files
│   └── config.json
├── logs/                     # Log files
│   └── capacitance-monitor.log
└── ai/                       # AI assistant modules
    ├── assistant.py
    └── tools.py
```

## Privacy and Data

- **Your measurement data stays local** - only your chat messages are sent to OpenAI
- **API key is stored securely** in your local `.env` file (not shared or uploaded)
- **No personal data is collected** by the application
- **OpenAI usage** is subject to OpenAI's privacy policy and terms of service

## Future Enhancements

Planned improvements include:
- Support for more complex measurement protocols
- Integration with data analysis tools
- Custom command templates
- Batch measurement automation
- Integration with external data analysis workflows
