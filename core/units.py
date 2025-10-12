"""Unit conversion and formatting utilities for capacitance and resistance."""

from typing import Tuple


def format_capacitance(value_farads: float, unit: str = "auto") -> Tuple[float, str, float]:
    """
    Format capacitance value for display.
    
    Args:
        value_farads: Capacitance value in farads
        unit: Target unit ("auto", "pF", "nF", "µF", "F")
    
    Returns:
        Tuple of (scaled_value, unit_string, scale_factor)
    """
    if unit == "auto":
        # Auto-select appropriate unit based on magnitude
        abs_value = abs(value_farads)
        
        if abs_value >= 1e-3:  # >= 1 mF
            return value_farads, "F", 1.0
        elif abs_value >= 1e-6:  # >= 1 µF
            return value_farads * 1e6, "µF", 1e-6
        elif abs_value >= 1e-9:  # >= 1 nF
            return value_farads * 1e9, "nF", 1e-9
        else:  # < 1 nF
            return value_farads * 1e12, "pF", 1e-12
    
    elif unit == "F":
        return value_farads, "F", 1.0
    elif unit == "µF":
        return value_farads * 1e6, "µF", 1e-6
    elif unit == "nF":
        return value_farads * 1e9, "nF", 1e-9
    elif unit == "pF":
        return value_farads * 1e12, "pF", 1e-12
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def parse_capacitance_string(value_str: str, unit: str) -> float:
    """
    Parse capacitance string and return value in farads.
    
    Args:
        value_str: String representation of capacitance value
        unit: Unit of the input string ("F", "µF", "nF", "pF")
    
    Returns:
        Capacitance value in farads
    """
    try:
        value = float(value_str)
    except ValueError:
        raise ValueError(f"Invalid capacitance value: {value_str}")
    
    if unit == "F":
        return value
    elif unit == "µF":
        return value * 1e-6
    elif unit == "nF":
        return value * 1e-9
    elif unit == "pF":
        return value * 1e-12
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def get_typical_ranges(unit: str = "nF") -> list[float]:
    """
    Get typical capacitance measurement ranges for the specified unit.
    
    Args:
        unit: Unit for the ranges ("F", "µF", "nF", "pF")
    
    Returns:
        List of typical range values in the specified unit
    """
    # Typical ranges for Keithley 2110 capacitance measurement
    # These are in farads, will be converted to requested unit
    ranges_farads = [
        1e-12,   # 1 pF
        10e-12,  # 10 pF
        100e-12, # 100 pF
        1e-9,    # 1 nF
        10e-9,   # 10 nF
        100e-9,  # 100 nF
        1e-6,    # 1 µF
        10e-6,   # 10 µF
        100e-6,  # 100 µF
        1e-3,    # 1 mF
    ]
    
    if unit == "F":
        return ranges_farads
    elif unit == "µF":
        return [r * 1e6 for r in ranges_farads]
    elif unit == "nF":
        return [r * 1e9 for r in ranges_farads]
    elif unit == "pF":
        return [r * 1e12 for r in ranges_farads]
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def format_resistance(value_ohms: float, unit: str = "auto") -> Tuple[float, str, float]:
    """
    Format resistance value for display.
    
    Args:
        value_ohms: Resistance value in ohms
        unit: Target unit ("auto", "mΩ", "Ω", "kΩ", "MΩ")
    
    Returns:
        Tuple of (scaled_value, unit_string, scale_factor)
    """
    if unit == "auto":
        # Auto-select appropriate unit based on magnitude
        abs_value = abs(value_ohms)
        
        if abs_value >= 1e6:  # >= 1 MΩ
            return value_ohms / 1e6, "MΩ", 1e6
        elif abs_value >= 1e3:  # >= 1 kΩ
            return value_ohms / 1e3, "kΩ", 1e3
        elif abs_value >= 1:  # >= 1 Ω
            return value_ohms, "Ω", 1.0
        else:  # < 1 Ω
            return value_ohms * 1e3, "mΩ", 1e-3
    
    elif unit == "MΩ":
        return value_ohms / 1e6, "MΩ", 1e6
    elif unit == "kΩ":
        return value_ohms / 1e3, "kΩ", 1e3
    elif unit == "Ω":
        return value_ohms, "Ω", 1.0
    elif unit == "mΩ":
        return value_ohms * 1e3, "mΩ", 1e-3
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def parse_resistance_string(value_str: str, unit: str) -> float:
    """
    Parse resistance string and return value in ohms.
    
    Args:
        value_str: String representation of resistance value
        unit: Unit of the input string ("mΩ", "Ω", "kΩ", "MΩ")
    
    Returns:
        Resistance value in ohms
    """
    try:
        value = float(value_str)
    except ValueError:
        raise ValueError(f"Invalid resistance value: {value_str}")
    
    if unit == "MΩ":
        return value * 1e6
    elif unit == "kΩ":
        return value * 1e3
    elif unit == "Ω":
        return value
    elif unit == "mΩ":
        return value * 1e-3
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def get_typical_resistance_ranges(unit: str = "Ω") -> list[float]:
    """
    Get typical resistance measurement ranges for the specified unit.
    
    Args:
        unit: Unit for the ranges ("mΩ", "Ω", "kΩ", "MΩ")
    
    Returns:
        List of typical range values in the specified unit
    """
    # Typical ranges for Keithley 2110 resistance measurement
    # These are in ohms, will be converted to requested unit
    ranges_ohms = [
        100,      # 100 Ω
        1e3,      # 1 kΩ
        10e3,     # 10 kΩ
        100e3,    # 100 kΩ
        1e6,      # 1 MΩ
        10e6,     # 10 MΩ
        100e6,    # 100 MΩ
    ]
    
    if unit == "Ω":
        return ranges_ohms
    elif unit == "kΩ":
        return [r / 1e3 for r in ranges_ohms]
    elif unit == "MΩ":
        return [r / 1e6 for r in ranges_ohms]
    elif unit == "mΩ":
        return [r * 1e3 for r in ranges_ohms]
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def format_frequency(hz: float) -> Tuple[float, str]:
    """
    Format frequency value for display.
    
    Args:
        hz: Frequency in Hz
    
    Returns:
        Tuple of (scaled_value, unit_string)
    """
    if hz >= 1e6:
        return hz / 1e6, "MHz"
    elif hz >= 1e3:
        return hz / 1e3, "kHz"
    else:
        return hz, "Hz"
