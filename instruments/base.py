"""Base instrument interface for measurement devices."""

from abc import ABC, abstractmethod
from typing import Optional


class Instrument(ABC):
    """Abstract base class for measurement instruments."""
    
    @abstractmethod
    def open(self, resource: Optional[str] = None) -> None:
        """
        Open connection to the instrument.
        
        Args:
            resource: VISA resource string (for real instruments) or None (for mock)
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close connection to the instrument."""
        pass
    
    @abstractmethod
    def initialize_capacitance_mode(self) -> None:
        """Initialize the instrument for capacitance measurement."""
        pass
    
    @abstractmethod
    def initialize_resistance_mode(self) -> None:
        """Initialize the instrument for resistance measurement."""
        pass
    
    @abstractmethod
    def set_autorange(self, enabled: bool) -> None:
        """
        Enable or disable autorange.
        
        Args:
            enabled: True to enable autorange, False for manual range
        """
        pass
    
    @abstractmethod
    def set_manual_range_capacitance(self, range_farads: float) -> None:
        """
        Set manual range for capacitance measurement.
        
        Args:
            range_farads: Range value in farads
        """
        pass
    
    @abstractmethod
    def set_manual_range_resistance(self, range_ohms: float) -> None:
        """
        Set manual range for resistance measurement.
        
        Args:
            range_ohms: Range value in ohms
        """
        pass
    
    @abstractmethod
    def set_nplc(self, nplc: float) -> None:
        """
        Set integration time in Number of Power Line Cycles.
        
        Args:
            nplc: Integration time (typically 0.01 to 10)
        """
        pass
    
    @abstractmethod
    def read_capacitance(self) -> float:
        """
        Read a single capacitance value.
        
        Returns:
            Capacitance value in farads
        """
        pass
    
    @abstractmethod
    def read_resistance(self) -> float:
        """
        Read a single resistance value.
        
        Returns:
            Resistance value in ohms
        """
        pass
    
    @abstractmethod
    def get_identification(self) -> str:
        """
        Get instrument identification string.
        
        Returns:
            Instrument identification string
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if instrument is connected.
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def instrument_type(self) -> str:
        """Get the instrument type identifier."""
        pass
