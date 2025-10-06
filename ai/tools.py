"""AI tools for measurement control and automation."""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PySide6.QtCore import QObject, QTimer, Signal
from pydantic import BaseModel, Field

from core.controller import MeasurementController
from core.models import AppConfig
from instruments import Instrument


class ToolResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class MeasurementTools(QObject):
    """Tools that the AI assistant can use to control measurements."""
    
    # Signals for UI updates
    tool_executed = Signal(str, str)  # tool_name, result_message
    measurement_started = Signal()
    measurement_stopped = Signal()
    data_exported = Signal(str)  # filepath
    
    def __init__(self, controller: MeasurementController, config: AppConfig):
        super().__init__()
        self._controller = controller
        self._config = config
        self._logger = logging.getLogger(__name__)
        
        # Timer for scheduled tasks
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_timeout)
        self._scheduled_tasks: List[Dict[str, Any]] = []
        
        # Sequence management
        self._measurement_sequence: List[Dict[str, Any]] = []
        self._sequence_timer = QTimer()
        self._sequence_timer.timeout.connect(self._execute_sequence_step)
        self._current_sequence_step = 0
        self._sequence_start_time = None
        
        # Current instrument reference
        self._current_instrument: Optional[Instrument] = None
    
    def set_instrument(self, instrument: Instrument) -> None:
        """Set the current instrument for measurements."""
        self._current_instrument = instrument
    
    def _create_instrument_from_config(self) -> None:
        """Auto-create instrument based on current configuration."""
        try:
            if self._config.use_mock_instrument:
                from instruments import MockInstrument
                self._current_instrument = MockInstrument()
                self._logger.info("Auto-created MockInstrument for AI assistant")
            else:
                from instruments import Keithley2110
                self._current_instrument = Keithley2110()
                if self._config.visa_resource:
                    # Note: We don't open the instrument here, that's done by the controller
                    self._current_instrument._resource_string = self._config.visa_resource
                self._logger.info("Auto-created Keithley2110 for AI assistant")
        except Exception as e:
            self._logger.error(f"Failed to auto-create instrument: {e}")
            self._current_instrument = None
    
    def start_measurement(self, **kwargs) -> ToolResult:
        """Start capacitance measurement."""
        try:
            if not self._current_instrument:
                # Auto-create instrument based on configuration
                self._create_instrument_from_config()
                if not self._current_instrument:
                    return ToolResult(
                        success=False,
                        message="No instrument selected and unable to auto-create one. Please select an instrument first."
                    )
            
            if self._controller.is_measuring():
                return ToolResult(
                    success=False,
                    message="Measurement is already running."
                )
            
            self._controller.start_measurement(self._current_instrument)
            self.measurement_started.emit()
            
            return ToolResult(
                success=True,
                message="Measurement started successfully."
            )
            
        except Exception as e:
            self._logger.error(f"Failed to start measurement: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to start measurement: {str(e)}"
            )
    
    def stop_measurement(self, **kwargs) -> ToolResult:
        """Stop capacitance measurement."""
        try:
            if not self._controller.is_measuring():
                return ToolResult(
                    success=False,
                    message="No measurement is currently running."
                )
            
            self._controller.stop_measurement()
            self.measurement_stopped.emit()
            
            return ToolResult(
                success=True,
                message="Measurement stopped successfully."
            )
            
        except Exception as e:
            self._logger.error(f"Failed to stop measurement: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to stop measurement: {str(e)}"
            )
    
    def export_csv(self, filename: Optional[str] = None, **kwargs) -> ToolResult:
        """Export current measurement data to CSV."""
        try:
            if not self._controller.get_sample_count():
                return ToolResult(
                    success=False,
                    message="No data to export. Start a measurement first."
                )
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"measurement_{timestamp}.csv"
            
            # Ensure .csv extension
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            # Create default export directory in app folder
            from path import get_measurements_directory
            export_dir = get_measurements_directory()
            
            filepath = export_dir / filename
            
            self._controller.save_data(filepath)
            self.data_exported.emit(str(filepath))
            
            return ToolResult(
                success=True,
                message=f"Data exported successfully to {filepath}",
                data={"filepath": str(filepath)}
            )
            
        except Exception as e:
            self._logger.error(f"Failed to export CSV: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to export CSV: {str(e)}"
            )
    
    def clear_data(self, **kwargs) -> ToolResult:
        """Clear all measurement data."""
        try:
            self._controller.clear_data()
            
            return ToolResult(
                success=True,
                message="Data cleared successfully."
            )
            
        except Exception as e:
            self._logger.error(f"Failed to clear data: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to clear data: {str(e)}"
            )
    
    def get_status(self, **kwargs) -> ToolResult:
        """Get current measurement status."""
        try:
            is_measuring = self._controller.is_measuring()
            sample_count = self._controller.get_sample_count()
            error_count = self._controller.get_soft_error_count()
            
            status_info = {
                "is_measuring": is_measuring,
                "sample_count": sample_count,
                "error_count": error_count,
                "instrument_connected": self._current_instrument is not None
            }
            
            if is_measuring:
                message = f"Measurement is running. Samples: {sample_count}, Errors: {error_count}"
            else:
                message = f"Measurement is stopped. Total samples: {sample_count}, Errors: {error_count}"
            
            return ToolResult(
                success=True,
                message=message,
                data=status_info
            )
            
        except Exception as e:
            self._logger.error(f"Failed to get status: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to get status: {str(e)}"
            )
    
    def schedule_measurement(self, duration_minutes: float = None, duration_seconds: float = None, auto_export: bool = True, **kwargs) -> ToolResult:
        """Schedule a measurement for a specific duration."""
        try:
            # Calculate total duration in seconds
            total_seconds = 0
            if duration_seconds is not None:
                total_seconds += duration_seconds
            if duration_minutes is not None:
                total_seconds += duration_minutes * 60
            
            # If no duration specified, default to 1 minute
            if total_seconds == 0:
                total_seconds = 60
            
            # Validate duration
            if total_seconds <= 0:
                return ToolResult(
                    success=False,
                    message="Duration must be greater than 0. Please specify a valid duration."
                )
            
            if total_seconds > 86400:  # 24 hours in seconds
                return ToolResult(
                    success=False,
                    message="Duration cannot exceed 24 hours. Please specify a shorter duration."
                )
            
            if self._controller.is_measuring():
                return ToolResult(
                    success=False,
                    message="A measurement is already running. Stop it first."
                )
            
            # Ensure we have an instrument
            if not self._current_instrument:
                self._create_instrument_from_config()
                if not self._current_instrument:
                    return ToolResult(
                        success=False,
                        message="No instrument available. Please select an instrument first."
                    )
            
            # Start measurement
            start_result = self.start_measurement()
            if not start_result.success:
                return start_result
            
            # Schedule stop
            stop_time = datetime.now() + timedelta(seconds=total_seconds)
            
            # Format duration for display
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"
            
            task = {
                "action": "stop_measurement",
                "scheduled_time": stop_time,
                "duration_seconds": total_seconds,
                "duration_str": duration_str
            }
            
            if auto_export:
                task["auto_export"] = True
            
            self._scheduled_tasks.append(task)
            
            # Start timer if not already running
            if not self._timer.isActive():
                self._timer.start(1000)  # Check every second
            
            return ToolResult(
                success=True,
                message=f"Measurement scheduled for {duration_str}. Will stop at {stop_time.strftime('%H:%M:%S')}."
            )
            
        except Exception as e:
            self._logger.error(f"Failed to schedule measurement: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to schedule measurement: {str(e)}"
            )
    
    def _on_timer_timeout(self) -> None:
        """Handle timer timeout for scheduled tasks."""
        current_time = datetime.now()
        completed_tasks = []
        
        for task in self._scheduled_tasks:
            if current_time >= task["scheduled_time"]:
                try:
                    if task["action"] == "stop_measurement":
                        # Stop measurement
                        stop_result = self.stop_measurement()
                        if stop_result.success:
                            self.tool_executed.emit("stop_measurement", stop_result.message)
                        
                        # Auto export if requested
                        if task.get("auto_export", False):
                            export_result = self.export_csv()
                            if export_result.success:
                                self.tool_executed.emit("export_csv", export_result.message)
                    
                    completed_tasks.append(task)
                    
                except Exception as e:
                    self._logger.error(f"Error executing scheduled task: {e}")
                    completed_tasks.append(task)
        
        # Remove completed tasks
        for task in completed_tasks:
            self._scheduled_tasks.remove(task)
        
        # Stop timer if no more tasks
        if not self._scheduled_tasks:
            self._timer.stop()
    
    def plan_measurement_sequence(self, sequence_description: str, **kwargs) -> ToolResult:
        """Plan a sequence of measurement actions based on user description."""
        try:
            # This is a placeholder - the AI will parse the description and create the sequence
            # The actual parsing will be done by the AI assistant
            return ToolResult(
                success=True,
                message=f"Sequence planning requested for: {sequence_description}. Please use execute_measurement_sequence with a parsed sequence.",
                data={"sequence_description": sequence_description}
            )
        except Exception as e:
            self._logger.error(f"Failed to plan sequence: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to plan sequence: {str(e)}"
            )
    
    def execute_measurement_sequence(self, sequence: List[Dict[str, Any]], **kwargs) -> ToolResult:
        """Execute a planned measurement sequence."""
        try:
            if not sequence:
                return ToolResult(
                    success=False,
                    message="No sequence provided to execute."
                )
            
            # Validate sequence
            for i, step in enumerate(sequence):
                if "action" not in step or "time_offset" not in step:
                    return ToolResult(
                        success=False,
                        message=f"Invalid sequence step {i}: missing 'action' or 'time_offset'"
                    )
            
            # Store sequence and reset state
            self._measurement_sequence = sequence.copy()
            self._current_sequence_step = 0
            self._sequence_start_time = datetime.now()
            
            # Start sequence timer (check every 100ms for precision)
            self._sequence_timer.start(100)
            
            # Format sequence summary for user
            summary_lines = []
            for step in sequence:
                time_str = self._format_time_offset(step["time_offset"])
                action_str = step["action"]
                if "duration" in step:
                    action_str += f" for {step['duration']}"
                summary_lines.append(f"At {time_str} - {action_str}")
            
            summary = "\n".join(summary_lines)
            
            return ToolResult(
                success=True,
                message=f"Measurement sequence started:\n{summary}",
                data={"sequence": sequence, "total_steps": len(sequence)}
            )
            
        except Exception as e:
            self._logger.error(f"Failed to execute sequence: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to execute sequence: {str(e)}"
            )
    
    def _execute_sequence_step(self) -> None:
        """Execute the next step in the measurement sequence."""
        if not self._measurement_sequence or self._current_sequence_step >= len(self._measurement_sequence):
            self._sequence_timer.stop()
            return
        
        current_time = datetime.now()
        elapsed_seconds = (current_time - self._sequence_start_time).total_seconds()
        
        # Check if it's time for the next step
        next_step = self._measurement_sequence[self._current_sequence_step]
        target_time = next_step["time_offset"]
        
        if elapsed_seconds >= target_time:
            # Execute the step
            action = next_step["action"]
            
            try:
                if action == "start_measurement":
                    result = self.start_measurement()
                    self.tool_executed.emit("start_measurement", result.message)
                    
                elif action == "stop_measurement":
                    result = self.stop_measurement()
                    self.tool_executed.emit("stop_measurement", result.message)
                    
                elif action == "export_csv":
                    result = self.export_csv()
                    self.tool_executed.emit("export_csv", result.message)
                    
                elif action == "clear_data":
                    result = self.clear_data()
                    self.tool_executed.emit("clear_data", result.message)
                    
                elif action == "wait":
                    # Just wait, no action needed
                    pass
                    
                else:
                    self._logger.warning(f"Unknown sequence action: {action}")
                
                # Move to next step
                self._current_sequence_step += 1
                
            except Exception as e:
                self._logger.error(f"Error executing sequence step {self._current_sequence_step}: {e}")
                self._sequence_timer.stop()
    
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
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools for the AI."""
        return [
            {
                "name": "plan_measurement_sequence",
                "description": "Plan a sequence of measurement actions with timing",
                "parameters": {
                    "sequence_description": {
                        "type": "string",
                        "description": "Description of the measurement sequence to plan",
                        "required": True
                    }
                }
            },
            {
                "name": "execute_measurement_sequence",
                "description": "Execute a planned measurement sequence",
                "parameters": {
                    "sequence": {
                        "type": "array",
                        "description": "Array of measurement actions with timing",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "description": "Action to perform: start_measurement, stop_measurement, export_csv, clear_data, or wait"
                                },
                                "time_offset": {
                                    "type": "number",
                                    "description": "Time offset in seconds from sequence start"
                                },
                                "duration": {
                                    "type": "string",
                                    "description": "Optional duration description for display purposes"
                                }
                            },
                            "required": ["action", "time_offset"]
                        },
                        "required": True
                    }
                }
            },
            {
                "name": "start_measurement",
                "description": "Start capacitance measurement",
                "parameters": {}
            },
            {
                "name": "stop_measurement", 
                "description": "Stop capacitance measurement",
                "parameters": {}
            },
            {
                "name": "export_csv",
                "description": "Export current measurement data to CSV file",
                "parameters": {
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the CSV file (without extension)",
                        "required": False
                    }
                }
            },
            {
                "name": "clear_data",
                "description": "Clear all measurement data",
                "parameters": {}
            },
            {
                "name": "get_status",
                "description": "Get current measurement status and statistics",
                "parameters": {}
            },
            {
                "name": "schedule_measurement",
                "description": "Start a measurement and automatically stop it after specified duration",
                "parameters": {
                    "duration_seconds": {
                        "type": "number",
                        "description": "Duration of measurement in seconds (must be greater than 0, maximum 86400 seconds/24 hours)",
                        "required": False
                    },
                    "duration_minutes": {
                        "type": "number",
                        "description": "Duration of measurement in minutes (must be greater than 0, maximum 1440 minutes/24 hours)",
                        "required": False
                    },
                    "auto_export": {
                        "type": "boolean", 
                        "description": "Whether to automatically export CSV after measurement",
                        "required": False,
                        "default": True
                    }
                }
            }
        ]
