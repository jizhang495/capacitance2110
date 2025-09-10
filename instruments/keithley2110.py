"""Keithley 2110 DMM implementation for capacitance measurement."""

import logging
from typing import Optional

import pyvisa

from .base import Instrument


class Keithley2110(Instrument):
    """
    Keithley 2110 DMM implementation for capacitance measurement.
    
    Note: SCPI commands may need adjustment based on the actual Keithley 2110 manual.
    The commands used here follow standard SCPI patterns but should be verified.
    """
    
    def __init__(self):
        self._resource_manager: Optional[pyvisa.ResourceManager] = None
        self._instrument: Optional[pyvisa.Resource] = None
        self._resource_string: Optional[str] = None
        self._logger = logging.getLogger(__name__)
    
    def open(self, resource: Optional[str] = None) -> None:
        """Open connection to Keithley 2110."""
        try:
            self._resource_manager = pyvisa.ResourceManager()
            
            if resource:
                self._resource_string = resource
                self._instrument = self._resource_manager.open_resource(resource)
            else:
                # Try to find Keithley 2110 automatically
                resources = self._resource_manager.list_resources()
                keithley_resources = [r for r in resources if "2110" in r.upper()]
                
                if not keithley_resources:
                    raise RuntimeError("No Keithley 2110 found. Available resources: " + str(resources))
                
                self._resource_string = keithley_resources[0]
                self._instrument = self._resource_manager.open_resource(self._resource_string)
            
            # Configure instrument
            self._instrument.timeout = 5000  # 5 second timeout
            self._instrument.read_termination = '\n'
            self._instrument.write_termination = '\n'
            
            # Clear any errors
            self._instrument.write("*CLS")
            
            self._logger.info(f"Connected to Keithley 2110: {self._resource_string}")
            
        except Exception as e:
            self._logger.error(f"Failed to open Keithley 2110: {e}")
            self.close()
            raise
    
    def close(self) -> None:
        """Close connection to Keithley 2110."""
        try:
            if self._instrument:
                # Return to local control
                self._instrument.write(":SYST:LOC")
                self._instrument.close()
                self._instrument = None
            
            if self._resource_manager:
                self._resource_manager.close()
                self._resource_manager = None
            
            self._logger.info("Keithley 2110 connection closed")
            
        except Exception as e:
            self._logger.error(f"Error closing Keithley 2110: {e}")
    
    def initialize_capacitance_mode(self) -> None:
        """Initialize Keithley 2110 for capacitance measurement."""
        if not self._instrument:
            raise RuntimeError("Instrument not connected")
        
        try:
            # Set to remote control
            self._instrument.write(":SYST:REM")
            
            # Set function to capacitance
            # Note: Verify this command in the actual manual
            self._instrument.write(':FUNC "CAP"')
            
            # Set autorange on by default
            self._instrument.write(":CAP:RANG:AUTO ON")
            
            # Set integration time (NPLC) - verify if supported
            # self._instrument.write(":SENS:CAP:NPLC 1")
            
            # Clear any errors
            self._instrument.write("*CLS")
            
            self._logger.info("Keithley 2110 initialized for capacitance measurement")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize capacitance mode: {e}")
            raise
    
    def set_autorange(self, enabled: bool) -> None:
        """Enable or disable autorange."""
        if not self._instrument:
            raise RuntimeError("Instrument not connected")
        
        try:
            if enabled:
                self._instrument.write(":CAP:RANG:AUTO ON")
            else:
                self._instrument.write(":CAP:RANG:AUTO OFF")
            
            self._logger.debug(f"Autorange {'enabled' if enabled else 'disabled'}")
            
        except Exception as e:
            self._logger.error(f"Failed to set autorange: {e}")
            raise
    
    def set_manual_range(self, range_farads: float) -> None:
        """Set manual range for capacitance measurement."""
        if not self._instrument:
            raise RuntimeError("Instrument not connected")
        
        try:
            # Set the range value in farads
            # Note: Verify the exact command format in the manual
            self._instrument.write(f":CAP:RANG {range_farads:.12e}")
            
            self._logger.debug(f"Manual range set to {range_farads:.2e} F")
            
        except Exception as e:
            self._logger.error(f"Failed to set manual range: {e}")
            raise
    
    def set_nplc(self, nplc: float) -> None:
        """Set integration time in Number of Power Line Cycles."""
        if not self._instrument:
            raise RuntimeError("Instrument not connected")
        
        try:
            # Note: Verify if Keithley 2110 supports NPLC setting for capacitance
            # This command may not be supported
            self._instrument.write(f":SENS:CAP:NPLC {nplc}")
            
            self._logger.debug(f"NPLC set to {nplc}")
            
        except Exception as e:
            self._logger.warning(f"NPLC setting may not be supported: {e}")
            # Don't raise exception as this may not be supported
    
    def read_capacitance(self) -> float:
        """Read a single capacitance value."""
        if not self._instrument:
            raise RuntimeError("Instrument not connected")
        
        try:
            # Read capacitance value
            # Note: Verify the exact command in the manual
            response = self._instrument.query(":READ?")
            
            # Parse the response - should be a single float value in farads
            capacitance = float(response.strip())
            
            return capacitance
            
        except Exception as e:
            self._logger.error(f"Failed to read capacitance: {e}")
            raise
    
    def get_identification(self) -> str:
        """Get instrument identification string."""
        if not self._instrument:
            raise RuntimeError("Instrument not connected")
        
        try:
            idn = self._instrument.query("*IDN?")
            return idn.strip()
            
        except Exception as e:
            self._logger.error(f"Failed to get identification: {e}")
            return "Keithley 2110 (Unknown)"
    
    def is_connected(self) -> bool:
        """Check if instrument is connected."""
        return self._instrument is not None and self._resource_manager is not None
    
    @property
    def instrument_type(self) -> str:
        """Get the instrument type identifier."""
        return "keithley2110"
    
    def get_available_resources(self) -> list[str]:
        """Get list of available VISA resources."""
        try:
            if not self._resource_manager:
                self._resource_manager = pyvisa.ResourceManager()
            
            resources = self._resource_manager.list_resources()
            
            # Filter for Keithley 2110 resources if possible
            keithley_resources = []
            for resource in resources:
                # Look for Keithley 2110 in the resource string
                if "2110" in resource.upper() or "KEITHLEY" in resource.upper():
                    keithley_resources.append(resource)
            
            # Return Keithley-specific resources if found, otherwise all resources
            return keithley_resources if keithley_resources else resources
            
        except Exception as e:
            self._logger.error(f"Failed to list VISA resources: {e}")
            return []
    
    @staticmethod
    def get_available_resources_static() -> list[str]:
        """Get list of available VISA resources without creating an instance."""
        try:
            resource_manager = pyvisa.ResourceManager()
            resources = resource_manager.list_resources()
            
            # Filter for Keithley 2110 resources if possible
            keithley_resources = []
            for resource in resources:
                # Look for Keithley 2110 in the resource string
                if "2110" in resource.upper() or "KEITHLEY" in resource.upper():
                    keithley_resources.append(resource)
            
            # If no Keithley-specific resources found, try to identify by VID/PID
            if not keithley_resources:
                for resource in resources:
                    # Keithley 2110 USB VID:PID is 0x05E6:0x2110
                    if "0x05E6" in resource and "0x2110" in resource:
                        keithley_resources.append(resource)
            
            # Return Keithley-specific resources if found, otherwise all resources
            return keithley_resources if keithley_resources else resources
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to list VISA resources: {e}")
            return []
    
    def check_errors(self) -> list[str]:
        """Check for instrument errors."""
        if not self._instrument:
            return []
        
        try:
            errors = []
            while True:
                error = self._instrument.query(":SYST:ERR?")
                if error.strip() == "+0,\"No error\"":
                    break
                errors.append(error.strip())
                if len(errors) > 10:  # Prevent infinite loop
                    break
            
            return errors
            
        except Exception as e:
            self._logger.error(f"Failed to check errors: {e}")
            return [f"Error checking failed: {e}"]
