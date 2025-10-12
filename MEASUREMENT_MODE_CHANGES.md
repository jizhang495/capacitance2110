# Measurement Mode Selection Feature

## Summary

Added a measurement mode selection dropdown to allow users to switch between capacitance and resistance measurements. The UI dynamically updates units, graph labels, and range controls based on the selected mode.

## Changes Made

### 1. Instrument Classes (`instruments/`)
- **base.py**: Added abstract methods for resistance measurement
  - `initialize_resistance_mode()` - Initialize instrument for resistance measurement
  - `read_resistance()` - Read resistance value in ohms
  - `set_manual_range_resistance(range_ohms)` - Set manual resistance range
  - `set_manual_range_capacitance(range_farads)` - Renamed from `set_manual_range` for clarity

- **keithley2110.py**: Implemented resistance measurement support
  - Added `initialize_resistance_mode()` using SCPI command `:FUNC "RES"`
  - Added `read_resistance()` to read resistance values
  - Added `set_manual_range_resistance()` for resistance ranges
  - Kept backward compatibility with `set_manual_range()`

- **mock.py**: Added resistance simulation
  - Added `_generate_resistance_signal()` for synthetic resistance data
  - Added baseline resistance support (default 1 kΩ)
  - Added `set_baseline_resistance()` method
  - Implemented all resistance-related methods

### 2. Core Modules (`core/`)
- **models.py**: Updated data models
  - Modified `Sample` dataclass to support both capacitance and resistance
    - `capacitance_farads: Optional[float]`
    - `resistance_ohms: Optional[float]`
    - Added `value` property to get active measurement
  - Updated `AppConfig` with:
    - `measurement_mode: str` ("capacitance" or "resistance")
    - `manual_range_ohms: float` for resistance ranges
    - `resistance_unit: str` ("auto", "mΩ", "Ω", "kΩ", "MΩ")
  - Updated `MeasurementMetadata` to store measurement mode
  - Updated CSV import/export to handle both measurement types

- **units.py**: Added resistance formatting functions
  - `format_resistance(value_ohms, unit)` - Format resistance for display
  - `parse_resistance_string(value_str, unit)` - Parse resistance strings
  - `get_typical_resistance_ranges(unit)` - Get standard resistance ranges

- **controller.py**: Updated for dual-mode support
  - `VISAWorker` initializes instrument based on measurement mode
  - Reads capacitance or resistance based on mode
  - Sets appropriate manual range based on mode
  - Creates correct sample type in `_on_sample_acquired()`

### 3. UI Components (`ui/`)
- **plot_widget.py**: Dynamic plot labeling
  - Added `set_measurement_mode(mode)` method
  - Added `_update_plot_labels()` to change axis labels and title
  - Plot automatically clears when switching modes
  - Extracts correct value from samples based on mode

- **main_window.py**: Added measurement mode controls
  - Added **Measurement Mode** dropdown with "Capacitance" and "Resistance" options
  - Updated window title to "Measurement Monitor - Keithley 2110"
  - `_on_measurement_mode_changed()` handles mode switching:
    - Prompts user if measurement is running
    - Updates range combo box for new mode
    - Updates units combo box for new mode
    - Updates plot widget
    - Clears data when switching
  - Updated `_populate_range_combo()` to show ranges for current mode
  - Updated `_update_unit_combo()` to show units for current mode
  - Updated status display to show correct range units

## How to Use

### Starting a Measurement

1. **Select Measurement Mode**
   - Choose "Capacitance" or "Resistance" from the Measurement Mode dropdown
   - If a measurement is running, you'll be prompted to stop it first

2. **Configure Settings**
   - For **Capacitance Mode**:
     - Units: auto, pF, nF, µF, F
     - Ranges: 1 pF to 1 mF
   - For **Resistance Mode**:
     - Units: auto, mΩ, Ω, kΩ, MΩ
     - Ranges: 100 Ω to 100 MΩ

3. **Select Instrument**
   - Choose "Mock Instrument" for testing
   - Choose "Keithley 2110" for real hardware

4. **Start Measurement**
   - Click "Start" button
   - Graph will update in real-time
   - Y-axis label changes based on mode:
     - Capacitance mode: "Capacitance vs Time"
     - Resistance mode: "Resistance vs Time"

### Switching Modes

1. Select the new mode from the dropdown
2. If measuring, click "Yes" to stop current measurement
3. Data will be cleared when switching modes
4. Configure new settings if needed
5. Click "Start" to begin new measurement

## Testing

### Test with Mock Instrument

1. **Capacitance Mode**:
   ```
   1. Select "Mock Instrument"
   2. Select "Capacitance" mode
   3. Click "Start"
   4. Observe capacitance values around 1 nF with noise and drift
   ```

2. **Resistance Mode**:
   ```
   1. Select "Mock Instrument"
   2. Select "Resistance" mode
   3. Click "Start"
   4. Observe resistance values around 1 kΩ with noise and drift
   ```

3. **Mode Switching**:
   ```
   1. Start measurement in Capacitance mode
   2. Switch to Resistance mode
   3. Confirm the prompt to stop measurement
   4. Verify graph clears and y-axis label updates
   5. Start new measurement in Resistance mode
   ```

### Test with Keithley 2110

1. Connect Keithley 2110 DMM via USB
2. Select "Keithley 2110" instrument type
3. Refresh and select appropriate VISA resource
4. Test connection
5. Follow same test procedure as above

## Configuration

The configuration is saved to `config/config.json` and includes:
- `measurement_mode`: Current mode ("capacitance" or "resistance")
- `capacitance_unit`: Display unit for capacitance
- `resistance_unit`: Display unit for resistance
- `manual_range_farads`: Manual range for capacitance
- `manual_range_ohms`: Manual range for resistance

## Notes

- Data is saved in CSV format with both capacitance and resistance columns
- Old CSV files (capacitance only) can still be loaded
- The plot widget automatically adjusts axis labels and units
- Range controls dynamically update based on measurement mode
- Mock instrument generates realistic signals for both modes

