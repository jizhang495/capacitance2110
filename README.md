# Capacitance Monitor for Keithley 2110 DMM

A Python desktop application for continuous capacitance measurement using the Keithley 2110 DMM via SCPI and pyVISA, with a LabVIEW-like dashboard using pyqtgraph.

## Features

- **Real-time capacitance measurement** with live plotting
- **Start/Stop controls** with thread-safe operation
- **Interactive plot controls** (time window, Y-axis scaling)
- **Manual/Auto range** selection
- **Sample rate control** (50-2000 ms)
- **CSV data export/import** for analysis and overlay
- **Mock instrument** for offline development and testing
- **Configuration persistence** across sessions
- **Comprehensive error handling** and logging

## Requirements

- Python 3.10+
- PySide6 (Qt6 GUI framework)
- pyqtgraph (real-time plotting)
- pyvisa (instrument communication)
- pandas (CSV I/O)
- pydantic (configuration validation)
- numpy (numerical operations)

## Installation

### Quick Start (Recommended)

1. **Clone or download** the project files to your local directory.

2. **Run the setup script**:
   ```bash
   # Windows
   setup.bat
   
   # Unix-like systems (Linux/macOS)
   make setup
   ```

3. **Run the application**:
   ```bash
   # Windows
   run.bat --mock
   
   # Unix-like systems
   make run-mock
   ```

### Manual Installation

1. **Install uv** (if not already installed):
   ```bash
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Unix-like systems
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set up the environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # Unix-like systems
   # or
   .venv\Scripts\activate     # Windows
   
   uv pip install -e ".[dev]"
   ```

3. **For real instrument communication**, install a VISA backend:
   - **Windows**: Install NI-VISA or pyvisa-py
   - **Linux**: Install pyvisa-py or system VISA
   - **macOS**: Install pyvisa-py or system VISA

## Driver Installation

Before using the application with a real Keithley 2110, install the required drivers:

### Required Drivers

1. **Keithley IVI COM Driver** (Required):
   - Download from: [Keithley 2100-2110 IVI COM Driver](https://www.tek.com/en/support/software/driver/2100-2110-ivi-com-driver-version-102)
   - Check for latest version when downloading
   - Install before connecting the instrument

2. **IVI Shared Components** (Required):
   - Download from: [IVI Foundation Shared Components](https://www.ivifoundation.org/Shared-Components/default.html)
   - Required for IVI COM driver functionality

3. **NI-VISA** (Recommended):
   - Download from: [NI-VISA Driver](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html#570633)
   - Current version: 2025 Q3
   - Provides robust VISA backend support

### Installation Order
1. Install IVI Shared Components first
2. Install Keithley IVI COM Driver
3. Install NI-VISA (optional but recommended)
4. Restart your computer
5. Connect the Keithley 2110

## Quick Start

### Windows
```bash
# Run with mock instrument (recommended for testing)
run.bat --mock

# Run with real Keithley 2110 (instrument selection via GUI)
run.bat

# Run with debug logging
run.bat --mock --debug

# Development mode (includes tests)
run-dev.bat
```

### Unix-like Systems (Linux/macOS)
```bash
# Run with mock instrument (recommended for testing)
make run-mock

# Run with real Keithley 2110 (instrument selection via GUI)
make run

# Run with debug logging
make run ARGS="--mock --debug"

# Development mode (includes tests)
make run-dev
```

### Direct Python Execution
```bash
# Activate virtual environment first
source .venv/bin/activate  # Unix-like systems
# or
.venv\Scripts\activate     # Windows

# Then run directly
python app.py --mock
python app.py  # Instrument selection via GUI
python app.py --mock --debug
```

## Usage

### Main Interface

1. **Instrument Selection**:
   - **Type**: Choose between "Mock Instrument" (for testing) or "Keithley 2110" (real hardware)
   - **Resource**: Dropdown list of available VISA resources (auto-detected)
   - **Refresh**: Button to scan for newly connected instruments
   - **Manual Entry**: Resource field is editable for custom VISA strings

2. **Start/Stop Measurement**: Use the green Start button to begin measurement, red Stop button to halt.

3. **Time Window Control**: 
   - Select preset windows (10s, 60s, 5min, All)
   - Use custom time window with the spinbox

4. **Y-Axis Scaling**:
   - Enable "Auto Scale" for automatic Y-axis adjustment
   - Disable for manual min/max control

5. **Measurement Range**:
   - Enable "Autorange" for automatic range selection
   - Disable to set manual range from dropdown

6. **Sample Rate**: Adjust measurement period (50-2000 ms)

7. **Display Units**: Choose capacitance units (auto, pF, nF, µF, F)

### Instrument Selection Workflow

1. **For Testing/Development**:
   - Select "Mock Instrument" from the Type dropdown
   - Resource field will be disabled
   - Click Start to begin measurement with synthetic data

2. **For Real Hardware**:
   - Select "Keithley 2110" from the Type dropdown
   - Click "Refresh" to scan for connected instruments
   - Select the appropriate resource from the dropdown
   - If your instrument doesn't appear, you can manually type the VISA resource string
   - Click Start to begin measurement

3. **Common VISA Resource Formats**:
   - USB: `USB0::0x05E6::0x2110::XXXX::INSTR`
   - TCP/IP: `TCPIP0::192.168.1.100::INSTR`
   - GPIB: `GPIB0::1::INSTR`

### Data Management

- **Save CSV**: Export current measurement data with metadata
- **Load CSV**: Import previous measurements for overlay comparison
- **Clear**: Remove all current and overlay data

### Status Bar Information

- **Connection Status**: Shows instrument connection state
- **Last Reading**: Most recent capacitance value with units
- **Sample Rate**: Effective measurement frequency
- **Range Mode**: Current range setting (AUTO/MANUAL)
- **Error Count**: Number of soft errors encountered

## Configuration

The application automatically saves configuration to:
- **Windows**: `%APPDATA%/capacitance-monitor/config.json`
- **Linux**: `~/.config/capacitance-monitor/config.json`
- **macOS**: `~/Library/Application Support/capacitance-monitor/config.json`

Configuration includes:
- Instrument settings (mock/real, VISA resource)
- UI preferences (time window, Y-scale, units)
- Measurement parameters (sample rate, range settings)

## SCPI Commands

The application uses standard SCPI commands for the Keithley 2110. Key commands include:

```scpi
:FUNC "CAP"                    # Set to capacitance function
:CAP:RANG:AUTO ON|OFF         # Enable/disable autorange
:CAP:RANG <value>             # Set manual range (in farads)
:READ?                        # Read capacitance value
:SYST:REM                     # Remote control mode
:SYST:LOC                     # Local control mode
```

**Note**: SCPI commands may need adjustment based on the actual Keithley 2110 manual. Check the comments in `instruments/keithley2110.py` for command details.

## File Formats

### CSV Export Format

```csv
# Capacitance Measurement Data
# Generated: 2023-01-01T12:00:00
# Instrument: keithley2110
# Resource: USB0::0x05E6::0x2110::XXXX::INSTR
# Sample Period: 100 ms
# Autorange: True
# Sample Count: 1000
# Soft Errors: 0
#
timestamp_iso8601,t_seconds,capacitance_F
2023-01-01T12:00:00,0.0,1.000000000000e-09
2023-01-01T12:00:00.1,0.1,1.010000000000e-09
...
```

## Development

### Available Scripts

#### Windows Batch Files
- `setup.bat` - Initial setup and dependency installation
- `run.bat` - Run the application with various options
- `run-dev.bat` - Run in development mode with tests

#### Unix-like Systems (Makefile)
- `make setup` - Initial setup and dependency installation
- `make run-mock` - Run with mock instrument
- `make run ARGS="..."` - Run with custom arguments
- `make run-dev` - Run in development mode
- `make test` - Run tests only
- `make clean` - Clean up virtual environment

### Project Structure

```
keithley-cap-monitor/
├── app.py                     # Main entry point
├── setup.bat                  # Windows setup script
├── run.bat                    # Windows run script
├── run-dev.bat                # Windows development script
├── Makefile                   # Unix-like systems makefile
├── pyproject.toml             # Project configuration
├── requirements.txt           # Legacy requirements file
├── core/                      # Core application logic
│   ├── controller.py          # Measurement controller & worker thread
│   ├── models.py              # Data models & configuration
│   ├── io_csv.py              # CSV I/O utilities
│   └── units.py               # Unit conversion utilities
├── instruments/               # Instrument abstraction
│   ├── base.py                # Abstract instrument interface
│   ├── keithley2110.py        # Keithley 2110 implementation
│   └── mock.py                # Mock instrument for testing
├── ui/                        # User interface
│   ├── main_window.py         # Main window implementation
│   └── plot_widget.py         # Plot widget for data visualization
├── tests/                     # Unit tests
│   ├── test_units.py          # Unit conversion tests
│   ├── test_csv.py            # CSV I/O tests
│   └── test_controller.py     # Controller tests
└── README.md                  # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_units.py

# Run with coverage
pytest --cov=core --cov=instruments --cov=ui
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

## Troubleshooting

### Driver Installation Issues

**Problem**: Keithley 2110 shown with an exclamation mark in Device Manager

**Solutions**:
1. **Install Keithley IVI COM Driver** (Required):
   - Download from: [Keithley 2100-2110 IVI COM Driver](https://www.tek.com/en/support/software/driver/2100-2110-ivi-com-driver-version-102)
   - Check for latest version when downloading
   - Install before connecting the instrument

2. **Install IVI Shared Components** (Required):
   - Download from: [IVI Foundation Shared Components](https://www.ivifoundation.org/Shared-Components/default.html)
   - Required for IVI COM driver functionality

3. **Install NI-VISA** (Recommended):
   - Download from: [NI-VISA Driver](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html#570633)
   - Current version: 2025 Q3
   - Provides robust VISA backend support

4. **Alternative**: Use Ethernet connection (no drivers needed)

### Instrument Not Found

**Problem**: "No VISA resources found" or instrument doesn't appear in dropdown

**Solutions**:
1. **Use the Debug button** in the Instrument Selection panel to get detailed information
2. **Check VISA backend installation**:
   ```bash
   # Windows
   pip install pyvisa-py
   # or install NI-VISA from National Instruments
   
   # Linux
   pip install pyvisa-py
   ```
3. **Verify instrument connection**:
   - Ensure instrument is powered on
   - Check USB cable and port
   - Try different USB cable/port
   - Check device manager (Windows) for USB devices
4. **Use the Test button** to verify connection to selected resource
5. **Manual resource entry**: Type the VISA resource string manually if auto-detection fails

### VISA Backend Issues

**Problem**: "Could not locate a VISA implementation. Install either the IVI binary or pyvisa-py"

**Solution**: Install pyvisa-py backend:
```bash
# Windows (using the provided script)
install_visa.bat

# Or manually
uv pip install pyvisa-py
```

**Quick Test**: Use the Debug button in the application to check VISA backend status and available resources.

### USB Permission Issues (Linux)

**Problem**: "Permission denied" when accessing USB device
**Solution**: Add user to dialout group:
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Connection Timeout

**Problem**: Instrument connection times out
**Solutions**:
1. Check VISA resource string
2. Verify instrument is powered on
3. Check USB/network connection
4. Try different VISA backend

### Performance Issues

**Problem**: UI becomes unresponsive during measurement
**Solutions**:
1. Increase sample period (reduce measurement frequency)
2. Reduce time window
3. Disable auto Y-scale
4. Close other applications

### Mock Instrument

If you encounter issues with real hardware, always test with the mock instrument first:
```bash
python app.py --mock
```

The mock instrument generates realistic capacitance data with:
- Baseline capacitance (1 nF default)
- Slow drift over time
- Random noise (10% of baseline)
- Optional step changes for testing

### Debug Tools

The application includes several debug tools to help troubleshoot connection issues:

1. **Debug Button**: Shows detailed VISA backend information and all available resources
2. **Test Button**: Tests connection to the selected instrument
3. **Refresh Button**: Rescans for available VISA resources
4. **Mock Instrument**: Built-in testing mode for development
5. **Log Files**: Check the application log files for detailed error information

**Usage**: Use the Debug and Test buttons in the Instrument Selection panel to troubleshoot connection issues.

## Future Enhancements

The following features are planned for future versions:

- **Low-pass filter toggle** for noise reduction
- **Annotation markers** for marking events
- **PNG export** for plot images
- **SQLite session logging** for long-term data storage
- **Multiple instrument support** for simultaneous measurements
- **Custom SCPI command interface** for advanced users
- **Data analysis tools** (statistics, FFT, etc.)

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with Keithley Instruments' software licensing terms when using with their hardware.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the application logs in the user log directory
3. Test with mock instrument to isolate hardware issues
4. Verify SCPI commands match your Keithley 2110 manual

## Contributing

Please ensure:
- Code follows the existing style (black formatting)
- Tests pass for new functionality
- Documentation is updated
- Type hints are provided for new functions
