"""Measurement controller and worker thread for capacitance monitoring."""

import logging
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, QThread, Signal, QTimer

from .io_csv import save_csv
from .models import AppConfig, MeasurementMetadata, Sample
from instruments import Instrument


class VISAWorker(QThread):
    """
    Worker thread for instrument communication and data acquisition.
    
    This thread handles all instrument I/O to avoid blocking the UI thread.
    """
    
    # Signals for communication with main thread
    sample_acquired = Signal(datetime, float)  # timestamp, capacitance_farads
    error_occurred = Signal(str)  # error_message
    status_changed = Signal(str)  # status_message
    connection_changed = Signal(bool)  # connected
    
    def __init__(self, instrument: Instrument, config: AppConfig):
        super().__init__()
        self._instrument = instrument
        self._config = config
        self._running = False
        self._logger = logging.getLogger(__name__)
        
        # Timing control
        self._sample_period_ms = config.sample_period_ms
        self._last_sample_time = 0.0
        
        # Error tracking
        self._soft_error_count = 0
        self._max_soft_errors = 100  # Stop after this many soft errors
    
    def run(self) -> None:
        """Main worker thread loop."""
        self._logger.info("VISA worker thread started")
        
        try:
            # Open and initialize instrument
            self._instrument.open()
            
            # Initialize based on measurement mode
            if self._config.measurement_mode == "capacitance":
                self._instrument.initialize_capacitance_mode()
            else:
                self._instrument.initialize_resistance_mode()
            
            self.connection_changed.emit(True)
            self.status_changed.emit(f"Connected to instrument ({self._config.measurement_mode} mode)")
            
            # Configure instrument settings
            self._configure_instrument()
            
            # Main acquisition loop
            self._running = True
            start_time = time.time()
            
            while self._running:
                try:
                    current_time = time.time()
                    elapsed_ms = (current_time - self._last_sample_time) * 1000
                    
                    # Check if it's time for next sample
                    if elapsed_ms >= self._sample_period_ms:
                        # Read value based on measurement mode
                        if self._config.measurement_mode == "capacitance":
                            value = self._instrument.read_capacitance()
                        else:
                            value = self._instrument.read_resistance()
                        
                        # Calculate timestamp and elapsed time
                        timestamp = datetime.now()
                        t_seconds = current_time - start_time
                        
                        # Emit sample signal
                        self.sample_acquired.emit(timestamp, value)
                        
                        # Update timing
                        self._last_sample_time = current_time
                    
                    # Small sleep to prevent excessive CPU usage
                    time.sleep(0.001)  # 1 ms
                    
                except Exception as e:
                    self._soft_error_count += 1
                    self._logger.warning(f"Soft error {self._soft_error_count}: {e}")
                    self.error_occurred.emit(f"Read error: {e}")
                    
                    # Stop if too many errors
                    if self._soft_error_count >= self._max_soft_errors:
                        self._logger.error(f"Too many soft errors ({self._soft_error_count}), stopping")
                        self.error_occurred.emit("Too many read errors, stopping acquisition")
                        break
                    
                    # Wait before retrying
                    time.sleep(0.1)
            
        except Exception as e:
            self._logger.error(f"Fatal error in worker thread: {e}")
            self.error_occurred.emit(f"Fatal error: {e}")
            self.connection_changed.emit(False)
        
        finally:
            # Cleanup
            try:
                self._instrument.close()
            except Exception as e:
                self._logger.error(f"Error closing instrument: {e}")
            
            self.connection_changed.emit(False)
            self.status_changed.emit("Disconnected from instrument")
            self._logger.info("VISA worker thread finished")
    
    def stop(self) -> None:
        """Stop the worker thread."""
        self._running = False
        self._logger.info("Stopping VISA worker thread")
    
    def _configure_instrument(self) -> None:
        """Configure instrument settings based on current config."""
        try:
            # Set autorange
            self._instrument.set_autorange(self._config.autorange_enabled)
            
            # Set manual range if not autorange
            if not self._config.autorange_enabled:
                if self._config.measurement_mode == "capacitance":
                    self._instrument.set_manual_range_capacitance(self._config.manual_range_farads)
                else:
                    self._instrument.set_manual_range_resistance(self._config.manual_range_ohms)
            
            # Set NPLC (integration time)
            self._instrument.set_nplc(1.0)  # Default to 1 NPLC
            
        except Exception as e:
            self._logger.warning(f"Failed to configure instrument: {e}")
    
    def update_config(self, config: AppConfig) -> None:
        """Update configuration and reconfigure instrument."""
        self._config = config
        self._sample_period_ms = config.sample_period_ms
        
        if self._instrument.is_connected():
            self._configure_instrument()
    
    def get_soft_error_count(self) -> int:
        """Get the number of soft errors encountered."""
        return self._soft_error_count


class MeasurementController(QObject):
    """
    Main controller for capacitance measurement application.
    
    Manages application state, data buffers, and coordinates between UI and worker thread.
    """
    
    # Signals for UI updates
    new_sample = Signal(datetime, float)  # timestamp, capacitance_farads
    status_changed = Signal(str)  # status_message
    connection_changed = Signal(bool)  # connected
    error_occurred = Signal(str)  # error_message
    data_cleared = Signal()  # when data buffer is cleared
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self._config = config
        self._logger = logging.getLogger(__name__)
        
        # Data storage
        self._samples: deque = deque(maxlen=10000)  # Rolling buffer
        self._overlay_data: List[Sample] = []  # Loaded CSV data for overlay
        
        # Worker thread
        self._worker: Optional[VISAWorker] = None
        self._worker_instrument: Optional[Instrument] = None
        
        # Measurement state
        self._is_measuring = False
        self._start_time: Optional[datetime] = None
        self._metadata: Optional[MeasurementMetadata] = None
        
        # UI update timer
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_ui)
        self._update_timer.start(33)  # ~30 FPS
    
    def start_measurement(self, instrument: Instrument) -> None:
        """Start capacitance measurement."""
        if self._is_measuring:
            self._logger.warning("Measurement already in progress")
            return
        
        try:
            # Store instrument reference
            self._worker_instrument = instrument
            
            # Create and start worker thread
            self._worker = VISAWorker(instrument, self._config)
            self._worker.sample_acquired.connect(self._on_sample_acquired)
            self._worker.error_occurred.connect(self._on_error_occurred)
            self._worker.status_changed.connect(self._on_status_changed)
            self._worker.connection_changed.connect(self._on_connection_changed)
            
            # Start measurement
            self._start_time = datetime.now()
            self._metadata = MeasurementMetadata(
                start_time=self._start_time,
                sample_period_ms=self._config.sample_period_ms,
                measurement_mode=self._config.measurement_mode,
                autorange_enabled=self._config.autorange_enabled,
                manual_range_farads=self._config.manual_range_farads if not self._config.autorange_enabled and self._config.measurement_mode == "capacitance" else None,
                manual_range_ohms=self._config.manual_range_ohms if not self._config.autorange_enabled and self._config.measurement_mode == "resistance" else None,
                instrument_type=instrument.instrument_type,
                visa_resource=getattr(instrument, '_resource_string', None),
            )
            
            self._is_measuring = True
            self._worker.start()
            
            self._logger.info("Measurement started")
            self.status_changed.emit("Measurement started")
            
        except Exception as e:
            self._logger.error(f"Failed to start measurement: {e}")
            self.error_occurred.emit(f"Failed to start measurement: {e}")
    
    def stop_measurement(self) -> None:
        """Stop capacitance measurement."""
        if not self._is_measuring:
            return
        
        try:
            # Stop worker thread
            if self._worker:
                self._worker.stop()
                self._worker.wait(5000)  # Wait up to 5 seconds
                self._worker = None
            
            # Update metadata
            if self._metadata:
                self._metadata.end_time = datetime.now()
                self._metadata.sample_count = len(self._samples)
                if self._worker:
                    self._metadata.soft_error_count = self._worker.get_soft_error_count()
            
            self._is_measuring = False
            self._logger.info("Measurement stopped")
            self.status_changed.emit("Measurement stopped")
            
        except Exception as e:
            self._logger.error(f"Error stopping measurement: {e}")
            self.error_occurred.emit(f"Error stopping measurement: {e}")
    
    def clear_data(self) -> None:
        """Clear all measurement data."""
        self._samples.clear()
        self._overlay_data.clear()
        self._logger.info("Data cleared")
        self.data_cleared.emit()
    
    def save_data(self, filepath: Path) -> None:
        """Save current measurement data to CSV file."""
        if not self._samples:
            raise ValueError("No data to save")
        
        if not self._metadata:
            raise ValueError("No measurement metadata available")
        
        try:
            # Convert deque to list
            samples_list = list(self._samples)
            
            # Update metadata with current sample count
            self._metadata.sample_count = len(samples_list)
            self._metadata.end_time = datetime.now()
            
            # Save to CSV
            save_csv(filepath, samples_list, self._metadata)
            
            self._logger.info(f"Data saved to {filepath}")
            self.status_changed.emit(f"Data saved to {filepath.name}")
            
        except Exception as e:
            self._logger.error(f"Failed to save data: {e}")
            self.error_occurred.emit(f"Failed to save data: {e}")
            raise
    
    def load_data(self, filepath: Path) -> None:
        """Load measurement data from CSV file for overlay."""
        try:
            from core.io_csv import load_csv
            
            samples, metadata = load_csv(filepath)
            self._overlay_data = samples
            
            self._logger.info(f"Loaded {len(samples)} samples from {filepath}")
            self.status_changed.emit(f"Loaded {len(samples)} samples from {filepath.name}")
            
        except Exception as e:
            self._logger.error(f"Failed to load data: {e}")
            self.error_occurred.emit(f"Failed to load data: {e}")
            raise
    
    def update_config(self, config: AppConfig) -> None:
        """Update application configuration."""
        self._config = config
        
        # Update worker thread if running
        if self._worker:
            self._worker.update_config(config)
    
    def get_current_samples(self, time_window_seconds: Optional[float] = None) -> List[Sample]:
        """Get current samples within time window."""
        if not self._samples:
            return []
        
        if time_window_seconds is None:
            return list(self._samples)
        
        # Filter samples within time window
        current_time = time.time()
        start_time = current_time - time_window_seconds
        
        filtered_samples = []
        for sample in self._samples:
            sample_time = (self._start_time.timestamp() + sample.t_seconds) if self._start_time else 0
            if sample_time >= start_time:
                filtered_samples.append(sample)
        
        return filtered_samples
    
    def get_overlay_data(self) -> List[Sample]:
        """Get loaded overlay data."""
        return self._overlay_data.copy()
    
    def is_measuring(self) -> bool:
        """Check if measurement is currently running."""
        return self._is_measuring
    
    def get_metadata(self) -> Optional[MeasurementMetadata]:
        """Get current measurement metadata."""
        return self._metadata
    
    def get_sample_count(self) -> int:
        """Get current number of samples."""
        return len(self._samples)
    
    def get_soft_error_count(self) -> int:
        """Get number of soft errors."""
        if self._worker:
            return self._worker.get_soft_error_count()
        return 0
    
    def _on_sample_acquired(self, timestamp: datetime, value: float) -> None:
        """Handle new sample from worker thread."""
        if not self._start_time:
            return
        
        # Calculate elapsed time
        t_seconds = (timestamp - self._start_time).total_seconds()
        
        # Create sample based on measurement mode
        if self._config.measurement_mode == "capacitance":
            sample = Sample(
                timestamp=timestamp,
                t_seconds=t_seconds,
                capacitance_farads=value,
            )
        else:
            sample = Sample(
                timestamp=timestamp,
                t_seconds=t_seconds,
                resistance_ohms=value,
            )
        
        # Add to buffer
        self._samples.append(sample)
        
        # Emit signal for UI update
        self.new_sample.emit(timestamp, value)
    
    def _on_error_occurred(self, error_message: str) -> None:
        """Handle error from worker thread."""
        self.error_occurred.emit(error_message)
    
    def _on_status_changed(self, status_message: str) -> None:
        """Handle status change from worker thread."""
        self.status_changed.emit(status_message)
    
    def _on_connection_changed(self, connected: bool) -> None:
        """Handle connection change from worker thread."""
        self.connection_changed.emit(connected)
    
    def _update_ui(self) -> None:
        """Periodic UI update (called by timer)."""
        # This method can be used for periodic UI updates
        # Currently, updates are handled by signals from worker thread
        pass
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.stop_measurement()
        self._update_timer.stop()
        
        if self._worker_instrument:
            try:
                self._worker_instrument.close()
            except Exception as e:
                self._logger.error(f"Error closing instrument during cleanup: {e}")
        
        self._logger.info("Controller cleanup completed")
