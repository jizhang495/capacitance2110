"""Main window for the capacitance monitor application."""

import logging
from pathlib import Path
from typing import Optional

import appdirs
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget, QCheckBox, QComboBox,
    QGroupBox, QGridLayout, QDoubleSpinBox, QStatusBar, QToolBar,
)

from core import AppConfig, MeasurementController, format_capacitance, get_typical_ranges
from instruments import Keithley2110, MockInstrument
from .plot_widget import PlotWidget
from .chat_widget import ChatWidget
from ai import AIAssistant, MeasurementTools


class MainWindow(QMainWindow):
    """Main window for the capacitance monitor application."""
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self._config = config
        self._logger = logging.getLogger(__name__)
        
        # Application state
        self._controller: Optional[MeasurementController] = None
        self._current_instrument: Optional[Keithley2110 | MockInstrument] = None
        self._is_measuring = False
        
        # AI assistant components
        self._ai_tools: Optional[MeasurementTools] = None
        self._ai_assistant: Optional[AIAssistant] = None
        self._chat_widget: Optional[ChatWidget] = None
        
        # UI components
        self._plot_widget: Optional[PlotWidget] = None
        self._status_bar: Optional[QStatusBar] = None
        
        # Control widgets
        self._start_button: Optional[QPushButton] = None
        self._stop_button: Optional[QPushButton] = None
        self._save_button: Optional[QPushButton] = None
        self._load_button: Optional[QPushButton] = None
        self._clear_button: Optional[QPushButton] = None
        
        # Settings widgets
        self._time_window_combo: Optional[QComboBox] = None
        self._time_window_spin: Optional[QDoubleSpinBox] = None
        self._y_auto_check: Optional[QCheckBox] = None
        self._y_min_spin: Optional[QDoubleSpinBox] = None
        self._y_max_spin: Optional[QDoubleSpinBox] = None
        self._autorange_check: Optional[QCheckBox] = None
        self._manual_range_combo: Optional[QComboBox] = None
        self._sample_period_spin: Optional[QSpinBox] = None
        self._unit_combo: Optional[QComboBox] = None
        
        # Status labels
        self._connection_label: Optional[QLabel] = None
        self._last_reading_label: Optional[QLabel] = None
        self._sample_rate_label: Optional[QLabel] = None
        self._range_label: Optional[QLabel] = None
        self._error_count_label: Optional[QLabel] = None
        
        # AI control widgets
        self._ai_enabled_check: Optional[QCheckBox] = None
        self._ai_api_key_button: Optional[QPushButton] = None
        
        # Setup UI
        self._setup_ui()
        self._setup_controller()
        self._setup_ai_assistant()
        self._load_config()
        
        # Update timer for status bar
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)  # Update every second
    
    def _setup_ui(self) -> None:
        """Setup the main window UI."""
        self.setWindowTitle("Capacitance Monitor - Keithley 2110")
        self.setGeometry(100, 25, 1200, 790)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create left panel with plot and chat
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Create plot area
        self._plot_widget = PlotWidget()
        left_layout.addWidget(self._plot_widget, 3)  # 3/4 of left space
        
        # Create chat widget
        self._chat_widget = ChatWidget()
        left_layout.addWidget(self._chat_widget, 1)  # 1/4 of left space
        
        main_layout.addWidget(left_panel, 2)  # 2/3 of total space
        
        # Create control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel, 1)  # 1/3 of total space
        
        # Create toolbar
        self._create_toolbar()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Start/Stop buttons
        self._start_button = QPushButton("Start")
        self._start_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self._start_button.clicked.connect(self._on_start_clicked)
        toolbar.addWidget(self._start_button)
        
        self._stop_button = QPushButton("Stop")
        self._stop_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        self._stop_button.clicked.connect(self._on_stop_clicked)
        self._stop_button.setEnabled(False)
        toolbar.addWidget(self._stop_button)
        
        toolbar.addSeparator()
        
        # File operations
        self._save_button = QPushButton("Save CSV")
        self._save_button.clicked.connect(self._on_save_clicked)
        toolbar.addWidget(self._save_button)
        
        self._load_button = QPushButton("Load CSV")
        self._load_button.clicked.connect(self._on_load_clicked)
        toolbar.addWidget(self._load_button)
        
        self._clear_button = QPushButton("Clear")
        self._clear_button.clicked.connect(self._on_clear_clicked)
        toolbar.addWidget(self._clear_button)
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel widget."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Time window controls
        time_group = QGroupBox("Time Window")
        time_layout = QGridLayout(time_group)
        
        self._time_window_combo = QComboBox()
        self._time_window_combo.addItems(["10 s", "60 s", "5 min", "All", "Custom"])
        self._time_window_combo.currentTextChanged.connect(self._on_time_window_changed)
        time_layout.addWidget(QLabel("Preset:"), 0, 0)
        time_layout.addWidget(self._time_window_combo, 0, 1)
        
        self._time_window_spin = QDoubleSpinBox()
        self._time_window_spin.setRange(1.0, 3600.0)
        self._time_window_spin.setValue(60.0)
        self._time_window_spin.setSuffix(" s")
        self._time_window_spin.valueChanged.connect(self._on_time_window_spin_changed)
        time_layout.addWidget(QLabel("Custom:"), 1, 0)
        time_layout.addWidget(self._time_window_spin, 1, 1)
        
        layout.addWidget(time_group)
        
        # Y-axis controls
        y_group = QGroupBox("Y-Axis Scale")
        y_layout = QGridLayout(y_group)
        
        self._y_auto_check = QCheckBox("Auto Scale")
        self._y_auto_check.setChecked(True)
        self._y_auto_check.toggled.connect(self._on_y_auto_toggled)
        y_layout.addWidget(self._y_auto_check, 0, 0, 1, 2)
        
        self._y_min_spin = QDoubleSpinBox()
        self._y_min_spin.setRange(-1e-3, 1e-3)
        self._y_min_spin.setValue(0.0)
        self._y_min_spin.setDecimals(12)
        self._y_min_spin.setEnabled(False)
        self._y_min_spin.valueChanged.connect(self._on_y_scale_changed)
        y_layout.addWidget(QLabel("Min:"), 1, 0)
        y_layout.addWidget(self._y_min_spin, 1, 1)
        
        self._y_max_spin = QDoubleSpinBox()
        self._y_max_spin.setRange(-1e-3, 1e-3)
        self._y_max_spin.setValue(1e-9)
        self._y_max_spin.setDecimals(12)
        self._y_max_spin.setEnabled(False)
        self._y_max_spin.valueChanged.connect(self._on_y_scale_changed)
        y_layout.addWidget(QLabel("Max:"), 2, 0)
        y_layout.addWidget(self._y_max_spin, 2, 1)
        
        layout.addWidget(y_group)
        
        # Instrument selection
        instrument_group = QGroupBox("Instrument Selection")
        instrument_layout = QGridLayout(instrument_group)
        
        self._instrument_type_combo = QComboBox()
        self._instrument_type_combo.addItems(["Mock Instrument", "Keithley 2110"])
        self._instrument_type_combo.currentTextChanged.connect(self._on_instrument_type_changed)
        instrument_layout.addWidget(QLabel("Type:"), 0, 0)
        instrument_layout.addWidget(self._instrument_type_combo, 0, 1)
        
        self._resource_combo = QComboBox()
        self._resource_combo.setEditable(True)  # Allow manual entry
        self._resource_combo.currentTextChanged.connect(self._on_resource_changed)
        instrument_layout.addWidget(QLabel("Resource:"), 1, 0)
        instrument_layout.addWidget(self._resource_combo, 1, 1)
        
        self._refresh_resources_button = QPushButton("Refresh")
        self._refresh_resources_button.clicked.connect(self._refresh_resources)
        instrument_layout.addWidget(self._refresh_resources_button, 1, 2)
        
        self._debug_resources_button = QPushButton("Debug")
        self._debug_resources_button.clicked.connect(self._debug_resources)
        instrument_layout.addWidget(self._debug_resources_button, 1, 3)
        
        self._test_connection_button = QPushButton("Test")
        self._test_connection_button.clicked.connect(self._test_connection)
        instrument_layout.addWidget(self._test_connection_button, 2, 1)
        
        layout.addWidget(instrument_group)
        
        # Range controls
        range_group = QGroupBox("Measurement Range")
        range_layout = QGridLayout(range_group)
        
        self._autorange_check = QCheckBox("Autorange")
        self._autorange_check.setChecked(True)
        self._autorange_check.toggled.connect(self._on_autorange_toggled)
        range_layout.addWidget(self._autorange_check, 0, 0, 1, 2)
        
        self._manual_range_combo = QComboBox()
        self._populate_range_combo()
        self._manual_range_combo.setEnabled(False)
        self._manual_range_combo.currentTextChanged.connect(self._on_manual_range_changed)
        range_layout.addWidget(QLabel("Manual Range:"), 1, 0)
        range_layout.addWidget(self._manual_range_combo, 1, 1)
        
        layout.addWidget(range_group)
        
        # Sample rate controls
        rate_group = QGroupBox("Sample Rate")
        rate_layout = QGridLayout(rate_group)
        
        self._sample_period_spin = QSpinBox()
        self._sample_period_spin.setRange(50, 2000)
        self._sample_period_spin.setValue(100)
        self._sample_period_spin.setSuffix(" ms")
        self._sample_period_spin.valueChanged.connect(self._on_sample_period_changed)
        rate_layout.addWidget(QLabel("Period:"), 0, 0)
        rate_layout.addWidget(self._sample_period_spin, 0, 1)
        
        layout.addWidget(rate_group)
        
        # Units controls
        unit_group = QGroupBox("Display Units")
        unit_layout = QGridLayout(unit_group)
        
        self._unit_combo = QComboBox()
        self._unit_combo.addItems(["auto", "pF", "nF", "µF", "F"])
        self._unit_combo.setCurrentText("auto")
        self._unit_combo.currentTextChanged.connect(self._on_unit_changed)
        unit_layout.addWidget(QLabel("Unit:"), 0, 0)
        unit_layout.addWidget(self._unit_combo, 0, 1)
        
        layout.addWidget(unit_group)
        
        # AI Assistant controls
        ai_group = QGroupBox("AI Assistant")
        ai_layout = QGridLayout(ai_group)
        
        self._ai_enabled_check = QCheckBox("Enable AI Assistant")
        self._ai_enabled_check.setChecked(False)
        self._ai_enabled_check.toggled.connect(self._on_ai_enabled_toggled)
        ai_layout.addWidget(self._ai_enabled_check, 0, 0, 1, 2)
        
        self._ai_api_key_button = QPushButton("Set API Key")
        self._ai_api_key_button.clicked.connect(self._on_set_api_key_clicked)
        self._ai_api_key_button.setEnabled(False)
        ai_layout.addWidget(self._ai_api_key_button, 1, 0, 1, 2)
        
        layout.addWidget(ai_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        
        # Connection status
        self._connection_label = QLabel("Disconnected")
        self._status_bar.addWidget(self._connection_label)
        
        # Last reading
        self._last_reading_label = QLabel("Last: --")
        self._status_bar.addWidget(self._last_reading_label)
        
        # Sample rate
        self._sample_rate_label = QLabel("Rate: -- Hz")
        self._status_bar.addWidget(self._sample_rate_label)
        
        # Range mode
        self._range_label = QLabel("Range: --")
        self._status_bar.addWidget(self._range_label)
        
        # Error count
        self._error_count_label = QLabel("Errors: 0")
        self._status_bar.addWidget(self._error_count_label)
    
    def _setup_controller(self) -> None:
        """Setup the measurement controller."""
        self._controller = MeasurementController(self._config)
        
        # Connect signals
        self._controller.new_sample.connect(self._on_new_sample)
        self._controller.status_changed.connect(self._on_status_changed)
        self._controller.connection_changed.connect(self._on_connection_changed)
        self._controller.error_occurred.connect(self._on_error_occurred)
        self._controller.data_cleared.connect(self._on_data_cleared)
    
    def _setup_ai_assistant(self) -> None:
        """Setup the AI assistant."""
        # Create AI tools
        self._ai_tools = MeasurementTools(self._controller, self._config)
        
        # Create AI assistant (will automatically load API key from .env file)
        self._ai_assistant = AIAssistant(self._ai_tools)
        
        # Connect chat widget signals
        if self._chat_widget:
            self._chat_widget.message_sent.connect(self._on_chat_message_sent)
        
        # Connect AI assistant signals
        self._ai_assistant.message_received.connect(self._on_ai_message_received)
        self._ai_assistant.error_occurred.connect(self._on_ai_error_occurred)
        self._ai_assistant.tool_executed.connect(self._on_ai_tool_executed)
        
        # Connect AI tools signals
        self._ai_tools.measurement_started.connect(self._on_ai_measurement_started)
        self._ai_tools.measurement_stopped.connect(self._on_ai_measurement_stopped)
        self._ai_tools.data_exported.connect(self._on_ai_data_exported)
    
    def _load_config(self) -> None:
        """Load configuration into UI widgets."""
        # Time window
        if self._config.time_window_seconds == 10:
            self._time_window_combo.setCurrentText("10 s")
        elif self._config.time_window_seconds == 60:
            self._time_window_combo.setCurrentText("60 s")
        elif self._config.time_window_seconds == 300:
            self._time_window_combo.setCurrentText("5 min")
        else:
            self._time_window_combo.setCurrentText("Custom")
            self._time_window_spin.setValue(self._config.time_window_seconds)
        
        # Y-axis scale
        self._y_auto_check.setChecked(self._config.y_scale_auto)
        self._y_min_spin.setValue(self._config.y_scale_min)
        self._y_max_spin.setValue(self._config.y_scale_max)
        self._y_min_spin.setEnabled(not self._config.y_scale_auto)
        self._y_max_spin.setEnabled(not self._config.y_scale_auto)
        
        # Instrument settings
        if self._config.use_mock_instrument:
            self._instrument_type_combo.setCurrentText("Mock Instrument")
        else:
            self._instrument_type_combo.setCurrentText("Keithley 2110")
        
        # Set resource string
        if self._config.visa_resource:
            self._resource_combo.setCurrentText(self._config.visa_resource)
        
        # Range settings
        self._autorange_check.setChecked(self._config.autorange_enabled)
        self._manual_range_combo.setEnabled(not self._config.autorange_enabled)
        
        # Sample period
        self._sample_period_spin.setValue(self._config.sample_period_ms)
        
        # Units
        self._unit_combo.setCurrentText(self._config.capacitance_unit)
        
        # AI settings
        self._ai_enabled_check.setChecked(self._config.ai_enabled)
        self._ai_api_key_button.setEnabled(self._config.ai_enabled)
        
        # Check if API key is available from .env file
        import os
        if os.getenv("OPENAI_API_KEY"):
            self._config.openai_api_key = os.getenv("OPENAI_API_KEY")
            if self._ai_assistant and self._config.ai_enabled:
                self._ai_assistant.set_api_key(self._config.openai_api_key)
                # Show message in chat that API key was loaded
                if self._chat_widget:
                    self._chat_widget.add_message("AI Assistant", "OpenAI API key loaded from .env file. I'm ready to help!", False)
        
        # Initialize resource list
        self._refresh_resources()
    
    def _populate_range_combo(self) -> None:
        """Populate the manual range combo box."""
        ranges = get_typical_ranges("nF")
        for range_val in ranges:
            self._manual_range_combo.addItem(f"{range_val:.0f} nF")
    
    def _on_start_clicked(self) -> None:
        """Handle start button click."""
        try:
            # Create instrument based on current selection
            if self._instrument_type_combo.currentText() == "Mock Instrument":
                self._current_instrument = MockInstrument()
                self._config.use_mock_instrument = True
                self._config.visa_resource = None
            else:
                self._current_instrument = Keithley2110()
                self._config.use_mock_instrument = False
                self._config.visa_resource = self._resource_combo.currentText()
            
            # Set instrument in AI tools
            if self._ai_tools:
                self._ai_tools.set_instrument(self._current_instrument)
            
            # Start measurement
            self._controller.start_measurement(self._current_instrument)
            
            # Update UI
            self._start_button.setEnabled(False)
            self._stop_button.setEnabled(True)
            self._is_measuring = True
            
            # Save config
            self._save_config()
            
        except Exception as e:
            self._logger.error(f"Failed to start measurement: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start measurement:\n{e}")
    
    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self._controller.stop_measurement()
        
        # Update UI
        self._start_button.setEnabled(True)
        self._stop_button.setEnabled(False)
        self._is_measuring = False
    
    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        if not self._controller or self._controller.get_sample_count() == 0:
            QMessageBox.warning(self, "Warning", "No data to save")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                self._controller.save_data(Path(filepath))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save data:\n{e}")
    
    def _on_load_clicked(self) -> None:
        """Handle load button click."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load CSV", "", "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                self._controller.load_data(Path(filepath))
                # Update plot with overlay data
                overlay_data = self._controller.get_overlay_data()
                if overlay_data:
                    self._plot_widget.set_overlay_data(overlay_data, Path(filepath).stem)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data:\n{e}")
    
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        reply = QMessageBox.question(
            self, "Clear Data", "Are you sure you want to clear all data?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._controller.clear_data()
            # Note: _on_data_cleared will be called automatically by the controller signal
    
    def _on_time_window_changed(self, text: str) -> None:
        """Handle time window combo change."""
        if text == "10 s":
            self._set_time_window(10.0)
        elif text == "60 s":
            self._set_time_window(60.0)
        elif text == "5 min":
            self._set_time_window(300.0)
        elif text == "All":
            self._set_time_window(3600.0)  # 1 hour
        # Custom is handled by spin box
    
    def _on_time_window_spin_changed(self, value: float) -> None:
        """Handle time window spin box change."""
        self._time_window_combo.setCurrentText("Custom")
        self._set_time_window(value)
    
    def _set_time_window(self, seconds: float) -> None:
        """Set the time window."""
        self._config.time_window_seconds = seconds
        self._plot_widget.set_time_window(seconds)
        self._save_config()
    
    def _on_y_auto_toggled(self, checked: bool) -> None:
        """Handle Y-axis auto scale toggle."""
        self._config.y_scale_auto = checked
        self._y_min_spin.setEnabled(not checked)
        self._y_max_spin.setEnabled(not checked)
        
        if checked:
            self._plot_widget.set_y_scale(True)
        else:
            self._plot_widget.set_y_scale(False, self._y_min_spin.value(), self._y_max_spin.value())
        
        self._save_config()
    
    def _on_y_scale_changed(self) -> None:
        """Handle Y-axis scale change."""
        if not self._y_auto_check.isChecked():
            self._config.y_scale_min = self._y_min_spin.value()
            self._config.y_scale_max = self._y_max_spin.value()
            self._plot_widget.set_y_scale(False, self._config.y_scale_min, self._config.y_scale_max)
            self._save_config()
    
    def _on_autorange_toggled(self, checked: bool) -> None:
        """Handle autorange toggle."""
        self._config.autorange_enabled = checked
        self._manual_range_combo.setEnabled(not checked)
        
        # Update controller if measuring
        if self._controller:
            self._controller.update_config(self._config)
        
        self._save_config()
    
    def _on_manual_range_changed(self, text: str) -> None:
        """Handle manual range change."""
        # Parse range value from text (e.g., "1 nF" -> 1e-9 F)
        try:
            value_str, unit = text.split()
            if unit == "nF":
                range_farads = float(value_str) * 1e-9
            elif unit == "µF":
                range_farads = float(value_str) * 1e-6
            elif unit == "pF":
                range_farads = float(value_str) * 1e-12
            else:
                range_farads = float(value_str)
            
            self._config.manual_range_farads = range_farads
            
            # Update controller if measuring
            if self._controller:
                self._controller.update_config(self._config)
            
            self._save_config()
            
        except Exception as e:
            self._logger.error(f"Failed to parse range value: {e}")
    
    def _on_sample_period_changed(self, value: int) -> None:
        """Handle sample period change."""
        self._config.sample_period_ms = value
        
        # Update controller if measuring
        if self._controller:
            self._controller.update_config(self._config)
        
        self._save_config()
    
    def _on_unit_changed(self, unit: str) -> None:
        """Handle unit change."""
        self._config.capacitance_unit = unit
        self._plot_widget.set_capacitance_unit(unit)
        self._save_config()
    
    def _on_ai_enabled_toggled(self, checked: bool) -> None:
        """Handle AI enabled toggle."""
        self._config.ai_enabled = checked
        self._ai_api_key_button.setEnabled(checked)
        
        if checked and self._config.openai_api_key:
            self.set_ai_api_key(self._config.openai_api_key)
        elif not checked:
            self.set_ai_api_key("")
        
        self._save_config()
    
    def _on_set_api_key_clicked(self) -> None:
        """Handle set API key button click."""
        from PySide6.QtWidgets import QInputDialog
        
        current_key = self._config.openai_api_key or ""
        api_key, ok = QInputDialog.getText(
            self, 
            "Set OpenAI API Key", 
            "Enter your OpenAI API key:",
            text=current_key
        )
        
        if ok and api_key:
            self._config.openai_api_key = api_key
            self.set_ai_api_key(api_key)
            self._save_config()
        elif ok and not api_key:
            # Clear the key
            self._config.openai_api_key = None
            self.set_ai_api_key("")
            self._save_config()
    
    def _on_instrument_type_changed(self, instrument_type: str) -> None:
        """Handle instrument type change."""
        if instrument_type == "Mock Instrument":
            self._config.use_mock_instrument = True
            self._config.visa_resource = None
            self._resource_combo.setEnabled(False)
            self._refresh_resources_button.setEnabled(False)
        else:
            self._config.use_mock_instrument = False
            self._resource_combo.setEnabled(True)
            self._refresh_resources_button.setEnabled(True)
            self._refresh_resources()
        
        self._save_config()
    
    def _on_resource_changed(self, resource: str) -> None:
        """Handle resource string change."""
        if not self._config.use_mock_instrument:
            self._config.visa_resource = resource
            self._save_config()
    
    def _refresh_resources(self) -> None:
        """Refresh the list of available VISA resources."""
        if self._config.use_mock_instrument:
            return
        
        try:
            # Use static method to get resources without creating instance
            resources = Keithley2110.get_available_resources_static()
            
            # Clear current items
            self._resource_combo.clear()
            
            # Add available resources
            if resources:
                for resource in resources:
                    self._resource_combo.addItem(resource)
                
                # Set current resource if it's in the list
                if self._config.visa_resource and self._config.visa_resource in resources:
                    self._resource_combo.setCurrentText(self._config.visa_resource)
                elif resources:
                    # Set to first available resource
                    self._resource_combo.setCurrentText(resources[0])
                    self._config.visa_resource = resources[0]
            else:
                # No resources found, add placeholder
                self._resource_combo.addItem("No VISA resources found")
                self._resource_combo.setCurrentText("No VISA resources found")
                self._config.visa_resource = None
            
            self._logger.info(f"Found {len(resources) if resources else 0} VISA resources")
            
        except Exception as e:
            self._logger.error(f"Failed to refresh VISA resources: {e}")
            # Add error message to combo
            self._resource_combo.clear()
            self._resource_combo.addItem(f"Error: {str(e)}")
            self._resource_combo.setCurrentText(f"Error: {str(e)}")
    
    def _debug_resources(self) -> None:
        """Debug VISA resource discovery and show detailed information."""
        if self._config.use_mock_instrument:
            QMessageBox.information(self, "Debug Info", "Mock instrument selected - no VISA resources needed.")
            return
        
        debug_info = []
        debug_info.append("=== VISA Resource Debug Information ===\n")
        
        try:
            # Check VISA backend
            import pyvisa
            debug_info.append(f"PyVISA version: {pyvisa.__version__}")
            
            # Try to create resource manager
            try:
                rm = pyvisa.ResourceManager()
                debug_info.append(f"VISA backend: {rm.visalib}")
            except Exception as e:
                debug_info.append(f"Failed to create ResourceManager: {e}")
                QMessageBox.warning(self, "Debug Info", "\n".join(debug_info))
                return
            
            # List all resources
            try:
                all_resources = rm.list_resources()
                debug_info.append(f"\nAll VISA resources found: {len(all_resources)}")
                for i, resource in enumerate(all_resources, 1):
                    debug_info.append(f"  {i}. {resource}")
            except Exception as e:
                debug_info.append(f"Failed to list resources: {e}")
            
            # Try to identify Keithley devices
            debug_info.append(f"\nKeithley 2110 specific search:")
            keithley_resources = []
            for resource in all_resources:
                if "2110" in resource.upper() or "KEITHLEY" in resource.upper():
                    keithley_resources.append(resource)
                    debug_info.append(f"  Found Keithley device: {resource}")
            
            if not keithley_resources:
                debug_info.append("  No Keithley 2110 devices found")
                debug_info.append("\nTroubleshooting suggestions:")
                debug_info.append("1. Check if instrument is powered on")
                debug_info.append("2. Verify USB/network connection")
                debug_info.append("3. Install appropriate VISA backend:")
                debug_info.append("   - Windows: NI-VISA or pyvisa-py")
                debug_info.append("   - Linux: pyvisa-py")
                debug_info.append("4. Check device manager (Windows) for USB devices")
                debug_info.append("5. Try different USB cable/port")
            
            # Test connection to first Keithley device
            if keithley_resources:
                test_resource = keithley_resources[0]
                debug_info.append(f"\nTesting connection to: {test_resource}")
                try:
                    instrument = rm.open_resource(test_resource)
                    instrument.timeout = 2000  # 2 second timeout
                    idn = instrument.query("*IDN?")
                    debug_info.append(f"  Connection successful!")
                    debug_info.append(f"  Instrument ID: {idn.strip()}")
                    instrument.close()
                except Exception as e:
                    debug_info.append(f"  Connection failed: {e}")
            
        except Exception as e:
            debug_info.append(f"Debug failed: {e}")
        
        # Show debug information
        debug_text = "\n".join(debug_info)
        QMessageBox.information(self, "VISA Debug Information", debug_text)
        
        # Also log to file
        self._logger.info("VISA Debug Information:\n" + debug_text)
    
    def _test_connection(self) -> None:
        """Test connection to the selected instrument."""
        if self._config.use_mock_instrument:
            QMessageBox.information(self, "Connection Test", "Mock instrument selected - no connection test needed.")
            return
        
        resource = self._resource_combo.currentText()
        if not resource or resource in ["No VISA resources found", "Error:"]:
            QMessageBox.warning(self, "Connection Test", "Please select a valid VISA resource first.")
            return
        
        try:
            # Create temporary instrument instance for testing
            temp_instrument = Keithley2110()
            temp_instrument.open(resource)
            
            # Try to get identification
            idn = temp_instrument.get_identification()
            temp_instrument.close()
            
            QMessageBox.information(
                self, 
                "Connection Test", 
                f"Connection successful!\n\nResource: {resource}\nInstrument ID: {idn}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Connection Test Failed", 
                f"Failed to connect to instrument:\n\nResource: {resource}\nError: {e}\n\nTroubleshooting:\n1. Check if instrument is powered on\n2. Verify USB/network connection\n3. Try refreshing the resource list\n4. Check VISA backend installation"
            )
            self._logger.error(f"Connection test failed for {resource}: {e}")
    
    def _on_new_sample(self, timestamp, capacitance_farads: float) -> None:
        """Handle new sample from controller."""
        from core.models import Sample
        
        # Create sample object
        sample = Sample(
            timestamp=timestamp,
            t_seconds=(timestamp - self._controller._start_time).total_seconds() if self._controller._start_time else 0,
            capacitance_farads=capacitance_farads,
        )
        
        # Add to plot
        self._plot_widget.add_sample(sample)
    
    def _on_status_changed(self, message: str) -> None:
        """Handle status change from controller."""
        self._status_bar.showMessage(message, 3000)  # Show for 3 seconds
    
    def _on_connection_changed(self, connected: bool) -> None:
        """Handle connection change from controller."""
        if connected:
            self._connection_label.setText("Connected")
            self._connection_label.setStyleSheet("color: green")
        else:
            self._connection_label.setText("Disconnected")
            self._connection_label.setStyleSheet("color: red")
    
    def _on_error_occurred(self, error_message: str) -> None:
        """Handle error from controller."""
        self._logger.error(f"Controller error: {error_message}")
        QMessageBox.warning(self, "Error", error_message)
    
    def _on_data_cleared(self) -> None:
        """Handle data cleared from controller."""
        self._plot_widget.clear_all_data()
    
    def _update_status(self) -> None:
        """Update status bar information."""
        if self._controller:
            # Update sample rate
            if self._is_measuring:
                sample_rate = 1000.0 / self._config.sample_period_ms
                self._sample_rate_label.setText(f"Rate: {sample_rate:.1f} Hz")
            else:
                self._sample_rate_label.setText("Rate: -- Hz")
            
            # Update range mode
            if self._config.autorange_enabled:
                self._range_label.setText("Range: AUTO")
            else:
                range_val, unit, _ = format_capacitance(self._config.manual_range_farads)
                self._range_label.setText(f"Range: {range_val:.1f} {unit}")
            
            # Update error count
            error_count = self._controller.get_soft_error_count()
            self._error_count_label.setText(f"Errors: {error_count}")
    
    def _save_config(self) -> None:
        """Save current configuration."""
        try:
            from path import get_config_directory
            config_dir = get_config_directory()
            config_file = config_dir / "config.json"
            self._config.save_to_file(config_file)
        except Exception as e:
            self._logger.error(f"Failed to save config: {e}")
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Stop measurement if running
        if self._is_measuring:
            self._controller.stop_measurement()
        
        # Cleanup controller
        if self._controller:
            self._controller.cleanup()
        
        # Save config
        self._save_config()
        
        event.accept()
    
    def _on_chat_message_sent(self, message: str) -> None:
        """Handle chat message sent."""
        if self._ai_assistant:
            # Disable input while processing
            self._chat_widget.set_input_enabled(False)
            
            # Send message to AI assistant
            self._ai_assistant.send_message(message)
    
    def _on_ai_message_received(self, message: str) -> None:
        """Handle AI message received."""
        if self._chat_widget:
            self._chat_widget.add_message("AI Assistant", message, False)
            # Re-enable input
            self._chat_widget.set_input_enabled(True)
            self._chat_widget.focus_input()
    
    def _on_ai_error_occurred(self, error_message: str) -> None:
        """Handle AI error."""
        if self._chat_widget:
            self._chat_widget.add_message("AI Assistant", f"Error: {error_message}", False)
            # Re-enable input
            self._chat_widget.set_input_enabled(True)
            self._chat_widget.focus_input()
    
    def _on_ai_tool_executed(self, tool_name: str, result_message: str) -> None:
        """Handle AI tool execution."""
        self._logger.info(f"AI tool executed: {tool_name} - {result_message}")
    
    def _on_ai_measurement_started(self) -> None:
        """Handle AI-triggered measurement start."""
        # Update UI state
        self._start_button.setEnabled(False)
        self._stop_button.setEnabled(True)
        self._is_measuring = True
    
    def _on_ai_measurement_stopped(self) -> None:
        """Handle AI-triggered measurement stop."""
        # Update UI state
        self._start_button.setEnabled(True)
        self._stop_button.setEnabled(False)
        self._is_measuring = False
    
    def _on_ai_data_exported(self, filepath: str) -> None:
        """Handle AI-triggered data export."""
        self._logger.info(f"AI exported data to: {filepath}")
    
    def set_ai_api_key(self, api_key: str) -> None:
        """Set the OpenAI API key for the AI assistant."""
        if self._ai_assistant:
            self._ai_assistant.set_api_key(api_key)
            if api_key:
                self._chat_widget.add_message("AI Assistant", "OpenAI API key set successfully. I'm ready to help!", False)
            else:
                self._chat_widget.add_message("AI Assistant", "OpenAI API key cleared. AI features are disabled.", False)
