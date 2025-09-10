"""Mock instrument for testing and development without hardware."""

import logging
import random
import time
from typing import Optional

from .base import Instrument


class MockInstrument(Instrument):
    """
    Mock instrument that generates synthetic capacitance data.
    
    Generates a realistic signal with:
    - Baseline capacitance
    - Slow drift
    - Random noise
    - Optional step changes
    """
    
    def __init__(self, baseline_farads: float = 1e-9, noise_level: float = 0.1):
        """
        Initialize mock instrument.
        
        Args:
            baseline_farads: Baseline capacitance in farads
            noise_level: Noise level as fraction of baseline (0.1 = 10%)
        """
        self._baseline_farads = baseline_farads
        self._noise_level = noise_level
        self._connected = False
        self._autorange_enabled = True
        self._manual_range_farads = 1e-9
        self._nplc = 1.0
        self._start_time = None
        self._step_changes = []  # List of (time_offset, step_size) tuples
        self._logger = logging.getLogger(__name__)
        
        # Initialize random seed for reproducible results
        random.seed(42)
    
    def open(self, resource: Optional[str] = None) -> None:
        """Open mock instrument (no actual connection needed)."""
        self._connected = True
        self._start_time = time.time()
        self._logger.info("Mock instrument opened")
    
    def close(self) -> None:
        """Close mock instrument."""
        self._connected = False
        self._logger.info("Mock instrument closed")
    
    def initialize_capacitance_mode(self) -> None:
        """Initialize mock instrument for capacitance measurement."""
        if not self._connected:
            raise RuntimeError("Mock instrument not connected")
        
        self._logger.info("Mock instrument initialized for capacitance measurement")
    
    def set_autorange(self, enabled: bool) -> None:
        """Enable or disable autorange."""
        self._autorange_enabled = enabled
        self._logger.debug(f"Mock autorange {'enabled' if enabled else 'disabled'}")
    
    def set_manual_range(self, range_farads: float) -> None:
        """Set manual range for capacitance measurement."""
        self._manual_range_farads = range_farads
        self._logger.debug(f"Mock manual range set to {range_farads:.2e} F")
    
    def set_nplc(self, nplc: float) -> None:
        """Set integration time in Number of Power Line Cycles."""
        self._nplc = nplc
        self._logger.debug(f"Mock NPLC set to {nplc}")
    
    def read_capacitance(self) -> float:
        """Read a synthetic capacitance value."""
        if not self._connected:
            raise RuntimeError("Mock instrument not connected")
        
        current_time = time.time()
        elapsed = current_time - self._start_time
        
        # Generate synthetic signal
        capacitance = self._generate_signal(elapsed)
        
        return capacitance
    
    def _generate_signal(self, elapsed_seconds: float) -> float:
        """
        Generate synthetic capacitance signal.
        
        Args:
            elapsed_seconds: Time elapsed since start
            
        Returns:
            Capacitance value in farads
        """
        # Baseline capacitance
        signal = self._baseline_farads
        
        # Add slow drift (exponential approach to new baseline)
        drift_target = self._baseline_farads * 1.1  # 10% increase over time
        drift_factor = 1 - 0.5 * (1 - elapsed_seconds / 300)  # 5-minute time constant
        drift_factor = max(0.5, drift_factor)  # Clamp to reasonable range
        signal += (drift_target - self._baseline_farads) * (1 - drift_factor)
        
        # Add step changes (simulate component changes)
        for step_time, step_size in self._step_changes:
            if elapsed_seconds >= step_time:
                signal += step_size
        
        # Add random noise
        noise_amplitude = signal * self._noise_level
        noise = random.gauss(0, noise_amplitude / 3)  # 3-sigma noise
        signal += noise
        
        # Add periodic variations (simulate temperature effects)
        temp_variation = 0.05 * signal * (1 + 0.1 * elapsed_seconds / 60) * \
                        (1 + 0.2 * (elapsed_seconds % 30) / 30)  # 30-second cycle
        signal += temp_variation * 0.1  # 10% of variation
        
        # Ensure positive value
        signal = max(signal, 1e-15)  # Minimum 1 fF
        
        return signal
    
    def add_step_change(self, time_offset_seconds: float, step_size_farads: float) -> None:
        """
        Add a step change to the signal at a specific time.
        
        Args:
            time_offset_seconds: Time offset from start when step occurs
            step_size_farads: Size of step in farads
        """
        self._step_changes.append((time_offset_seconds, step_size_farads))
        self._logger.debug(f"Added step change: {step_size_farads:.2e} F at {time_offset_seconds}s")
    
    def clear_step_changes(self) -> None:
        """Clear all step changes."""
        self._step_changes.clear()
        self._logger.debug("Cleared all step changes")
    
    def get_identification(self) -> str:
        """Get mock instrument identification string."""
        return "Mock Instrument,Capacitance Monitor,1.0,Simulated"
    
    def is_connected(self) -> bool:
        """Check if mock instrument is connected."""
        return self._connected
    
    @property
    def instrument_type(self) -> str:
        """Get the instrument type identifier."""
        return "mock"
    
    def set_baseline(self, baseline_farads: float) -> None:
        """Set the baseline capacitance value."""
        self._baseline_farads = baseline_farads
        self._logger.debug(f"Mock baseline set to {baseline_farads:.2e} F")
    
    def set_noise_level(self, noise_level: float) -> None:
        """Set the noise level as fraction of baseline."""
        self._noise_level = max(0.0, min(1.0, noise_level))  # Clamp to [0, 1]
        self._logger.debug(f"Mock noise level set to {self._noise_level:.1%}")
    
    def simulate_connection_error(self) -> None:
        """Simulate a connection error for testing."""
        self._connected = False
        self._logger.warning("Mock instrument connection error simulated")
    
    def simulate_read_error(self) -> None:
        """Simulate a read error for testing."""
        if random.random() < 0.1:  # 10% chance of error
            raise RuntimeError("Mock read error")
