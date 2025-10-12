"""Plot widget for real-time capacitance data visualization."""

import logging
from typing import List, Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.models import Sample
from core.units import format_capacitance


class PlotWidget(QWidget):
    """Custom plot widget for capacitance data visualization."""
    
    # Signals
    time_window_changed = Signal(float)  # New time window in seconds
    y_scale_changed = Signal(bool, float, float)  # auto, min, max
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        
        # Plot data
        self._current_data: List[Sample] = []
        self._overlay_data: List[Sample] = []
        self._time_window_seconds = 60.0
        self._y_auto_scale = True
        self._y_min = 0.0
        self._y_max = 1e-9
        self._capacitance_unit = "auto"
        self._resistance_unit = "auto"
        self._measurement_mode = "capacitance"  # "capacitance" or "resistance"
        
        # Setup UI
        self._setup_ui()
        
        # Plot items
        self._current_plot_item: Optional[pg.PlotDataItem] = None
        self._overlay_plot_items: List[pg.PlotDataItem] = []
        self._overlay_legend_items: List[pg.LegendItem] = []
        
        # Performance optimization
        self._update_counter = 0
        self._update_interval = 2  # Update plot every N samples
    
    def _setup_ui(self) -> None:
        """Setup the plot widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create plot widget
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setLabel('left', 'Capacitance', units='F')
        self._plot_widget.setLabel('bottom', 'Time', units='s')
        self._plot_widget.setTitle('Capacitance vs Time')
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self._plot_widget.setMouseEnabled(x=True, y=True)
        self._plot_widget.enableAutoRange(axis='x', enable=False)
        self._plot_widget.enableAutoRange(axis='y', enable=True)
        
        # Set initial view
        self._plot_widget.setXRange(0, self._time_window_seconds)
        
        # Add to layout
        layout.addWidget(self._plot_widget)
        
        # Create plot data items
        self._current_plot_item = self._plot_widget.plot(
            pen=pg.mkPen(color='blue', width=2),
            name='Current Session'
        )
        
        # Setup legend
        self._legend = self._plot_widget.addLegend()
        self._legend.addItem(self._current_plot_item, 'Current Session')
    
    def add_sample(self, sample: Sample) -> None:
        """Add a new sample to the current data."""
        self._current_data.append(sample)
        self._update_counter += 1
        
        # Update plot periodically for performance
        if self._update_counter >= self._update_interval:
            self._update_plot()
            self._update_counter = 0
    
    def set_overlay_data(self, samples: List[Sample], name: str = "Overlay") -> None:
        """Set overlay data for comparison."""
        self._overlay_data = samples.copy()
        
        # Create new plot item for overlay
        overlay_item = self._plot_widget.plot(
            pen=pg.mkPen(color='red', width=1, style=Qt.DashLine),
            name=name
        )
        
        # Add to legend
        self._legend.addItem(overlay_item, name)
        
        # Store references
        self._overlay_plot_items.append(overlay_item)
        
        # Update plot
        self._update_plot()
    
    def clear_overlay_data(self) -> None:
        """Clear all overlay data."""
        # Remove plot items
        for item in self._overlay_plot_items:
            self._plot_widget.removeItem(item)
            if item in self._legend.items:
                self._legend.removeItem(item)
        
        self._overlay_plot_items.clear()
        self._overlay_data.clear()
        
        # Update plot
        self._update_plot()
    
    def clear_current_data(self) -> None:
        """Clear current measurement data."""
        # Remove current plot item from display
        if self._current_plot_item is not None:
            self._plot_widget.removeItem(self._current_plot_item)
            if self._current_plot_item in self._legend.items:
                self._legend.removeItem(self._current_plot_item)
            self._current_plot_item = None
        
        # Clear data
        self._current_data.clear()
        
        # Update plot
        self._update_plot()
    
    def clear_all_data(self) -> None:
        """Clear all data and reset the plot completely."""
        # Clear current data
        self.clear_current_data()
        
        # Clear overlay data
        self.clear_overlay_data()
        
        # Reset plot appearance
        self._plot_widget.clear()
        if hasattr(self, '_legend'):
            self._legend.clear()
        
        # Reset plot items
        self._current_plot_item = None
        self._overlay_plot_items.clear()
        self._overlay_legend_items.clear()
    
    def set_time_window(self, seconds: float) -> None:
        """Set the time window for display."""
        self._time_window_seconds = seconds
        self._plot_widget.setXRange(0, seconds)
        self._update_plot()
        self.time_window_changed.emit(seconds)
    
    def set_y_scale(self, auto: bool, min_val: Optional[float] = None, max_val: Optional[float] = None) -> None:
        """Set Y-axis scale."""
        self._y_auto_scale = auto
        
        if not auto and min_val is not None and max_val is not None:
            self._y_min = min_val
            self._y_max = max_val
            self._plot_widget.setYRange(min_val, max_val)
        else:
            self._plot_widget.enableAutoRange(axis='y', enable=True)
        
        self.y_scale_changed.emit(auto, self._y_min, self._y_max)
    
    def set_capacitance_unit(self, unit: str) -> None:
        """Set the capacitance unit for display."""
        self._capacitance_unit = unit
        if self._measurement_mode == "capacitance":
            self._update_plot_labels()
    
    def set_resistance_unit(self, unit: str) -> None:
        """Set the resistance unit for display."""
        self._resistance_unit = unit
        if self._measurement_mode == "resistance":
            self._update_plot_labels()
    
    def set_measurement_mode(self, mode: str) -> None:
        """Set the measurement mode (capacitance or resistance)."""
        self._measurement_mode = mode
        self._update_plot_labels()
        
        # Clear current data when switching modes
        self.clear_all_data()
    
    def _update_plot_labels(self) -> None:
        """Update plot labels based on measurement mode."""
        if self._measurement_mode == "capacitance":
            self._plot_widget.setLabel('left', 'Capacitance', units='F')
            self._plot_widget.setTitle('Capacitance vs Time')
        else:
            self._plot_widget.setLabel('left', 'Resistance', units='Ω')
            self._plot_widget.setTitle('Resistance vs Time')
    
    def _update_plot(self) -> None:
        """Update the plot with current data."""
        try:
            # Update current data plot
            if self._current_data:
                self._update_current_plot()
            
            # Update overlay plots
            if self._overlay_data:
                self._update_overlay_plots()
            
            # Auto-scale Y axis if enabled
            if self._y_auto_scale:
                self._plot_widget.enableAutoRange(axis='y', enable=True)
            
        except Exception as e:
            self._logger.error(f"Error updating plot: {e}")
    
    def _update_current_plot(self) -> None:
        """Update the current data plot."""
        if not self._current_data:
            return
            
        # Ensure plot item is initialized
        if self._current_plot_item is None:
            self._current_plot_item = self._plot_widget.plot(
                pen=pg.mkPen(color='blue', width=2),
                name='Current Session'
            )
            # Re-add to legend if needed
            if hasattr(self, '_legend') and self._legend is not None:
                self._legend.addItem(self._current_plot_item, 'Current Session')
        
        # Filter data within time window
        current_time = self._current_data[-1].t_seconds if self._current_data else 0
        start_time = max(0, current_time - self._time_window_seconds)
        
        # Extract data arrays
        times = []
        values = []
        
        for sample in self._current_data:
            if sample.t_seconds >= start_time:
                times.append(sample.t_seconds)
                # Get the appropriate value based on measurement mode
                if self._measurement_mode == "capacitance" and sample.capacitance_farads is not None:
                    values.append(sample.capacitance_farads)
                elif self._measurement_mode == "resistance" and sample.resistance_ohms is not None:
                    values.append(sample.resistance_ohms)
        
        if times and values:
            # Convert to numpy arrays for performance
            times_array = np.array(times)
            values_array = np.array(values)
            
            # Update plot
            self._current_plot_item.setData(times_array, values_array)
    
    def _update_overlay_plots(self) -> None:
        """Update overlay plots."""
        if not self._overlay_data or not self._overlay_plot_items:
            return
        
        # For simplicity, update the first overlay item
        # In a more sophisticated implementation, you might want to handle multiple overlays
        if len(self._overlay_plot_items) > 0 and self._overlay_plot_items[0] is not None:
            times = []
            values = []
            
            for s in self._overlay_data:
                times.append(s.t_seconds)
                # Get the appropriate value based on measurement mode
                if self._measurement_mode == "capacitance" and s.capacitance_farads is not None:
                    values.append(s.capacitance_farads)
                elif self._measurement_mode == "resistance" and s.resistance_ohms is not None:
                    values.append(s.resistance_ohms)
            
            if times and values:
                times_array = np.array(times)
                values_array = np.array(values)
                self._overlay_plot_items[0].setData(times_array, values_array)
    
    def get_plot_widget(self) -> pg.PlotWidget:
        """Get the underlying pyqtgraph PlotWidget."""
        return self._plot_widget
    
    def export_plot(self, filename: str) -> None:
        """Export plot to image file."""
        try:
            exporter = pg.exporters.ImageExporter(self._plot_widget.plotItem)
            exporter.export(filename)
            self._logger.info(f"Plot exported to {filename}")
        except Exception as e:
            self._logger.error(f"Failed to export plot: {e}")
    
    def reset_view(self) -> None:
        """Reset plot view to default."""
        self._plot_widget.setXRange(0, self._time_window_seconds)
        if self._y_auto_scale:
            self._plot_widget.enableAutoRange(axis='y', enable=True)
        else:
            self._plot_widget.setYRange(self._y_min, self._y_max)
