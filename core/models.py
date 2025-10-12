"""Data models and configuration for the capacitance monitor application."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, Field, field_validator


@dataclass
class Sample:
    """A single measurement sample (capacitance or resistance)."""
    
    timestamp: datetime
    t_seconds: float  # Time since start of measurement
    capacitance_farads: Optional[float] = None  # Raw capacitance value in farads
    resistance_ohms: Optional[float] = None  # Raw resistance value in ohms
    
    @property
    def value(self) -> float:
        """Get the measurement value (capacitance or resistance)."""
        if self.capacitance_farads is not None:
            return self.capacitance_farads
        elif self.resistance_ohms is not None:
            return self.resistance_ohms
        else:
            raise ValueError("Sample has no measurement value")


class AppConfig(BaseModel):
    """Application configuration with validation."""
    
    # Instrument settings
    use_mock_instrument: bool = False
    visa_resource: Optional[str] = None
    
    # UI settings
    time_window_seconds: float = 60.0
    y_scale_auto: bool = True
    y_scale_min: float = 0.0
    y_scale_max: float = 1e-9  # 1 nF default
    sample_period_ms: int = 100
    
    # Measurement settings
    measurement_mode: str = "capacitance"  # "capacitance" or "resistance"
    autorange_enabled: bool = True
    manual_range_farads: float = 1e-9  # 1 nF default
    manual_range_ohms: float = 1e3  # 1 kΩ default
    
    # Display settings
    capacitance_unit: str = "auto"  # auto, pF, nF, µF, F
    resistance_unit: str = "auto"  # auto, mΩ, Ω, kΩ, MΩ
    
    # AI settings
    openai_api_key: Optional[str] = None
    ai_enabled: bool = False
    
    @field_validator("sample_period_ms")
    @classmethod
    def validate_sample_period(cls, v: int) -> int:
        """Validate sample period is within reasonable bounds."""
        if not 50 <= v <= 2000:
            raise ValueError("Sample period must be between 50 and 2000 ms")
        return v
    
    @field_validator("time_window_seconds")
    @classmethod
    def validate_time_window(cls, v: float) -> float:
        """Validate time window is positive."""
        if v <= 0:
            raise ValueError("Time window must be positive")
        return v
    
    @field_validator("measurement_mode")
    @classmethod
    def validate_measurement_mode(cls, v: str) -> str:
        """Validate measurement mode is supported."""
        valid_modes = ["capacitance", "resistance"]
        if v not in valid_modes:
            raise ValueError(f"Measurement mode must be one of {valid_modes}")
        return v
    
    @field_validator("capacitance_unit")
    @classmethod
    def validate_capacitance_unit(cls, v: str) -> str:
        """Validate capacitance unit is supported."""
        valid_units = ["auto", "pF", "nF", "µF", "F"]
        if v not in valid_units:
            raise ValueError(f"Capacitance unit must be one of {valid_units}")
        return v
    
    @field_validator("resistance_unit")
    @classmethod
    def validate_resistance_unit(cls, v: str) -> str:
        """Validate resistance unit is supported."""
        valid_units = ["auto", "mΩ", "Ω", "kΩ", "MΩ"]
        if v not in valid_units:
            raise ValueError(f"Resistance unit must be one of {valid_units}")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AppConfig:
        """Create config from dictionary."""
        return cls(**data)
    
    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> AppConfig:
        """Load configuration from JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            # Return default config if file doesn't exist or is invalid
            return cls()


class MeasurementMetadata(BaseModel):
    """Metadata for a measurement session."""
    
    start_time: datetime
    end_time: Optional[datetime] = None
    sample_count: int = 0
    sample_period_ms: int
    measurement_mode: str = "capacitance"  # "capacitance" or "resistance"
    autorange_enabled: bool
    manual_range_farads: Optional[float] = None
    manual_range_ohms: Optional[float] = None
    instrument_type: str  # "keithley2110" or "mock"
    visa_resource: Optional[str] = None
    soft_error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for CSV header."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MeasurementMetadata:
        """Create metadata from dictionary."""
        return cls(**data)


def sample_to_dataframe(samples: List[Sample]) -> pd.DataFrame:
    """Convert list of samples to pandas DataFrame."""
    if not samples:
        return pd.DataFrame(columns=["timestamp_iso8601", "t_seconds", "capacitance_F", "resistance_Ohm"])
    
    data = {
        "timestamp_iso8601": [s.timestamp.isoformat() for s in samples],
        "t_seconds": [s.t_seconds for s in samples],
        "capacitance_F": [s.capacitance_farads if s.capacitance_farads is not None else 0.0 for s in samples],
        "resistance_Ohm": [s.resistance_ohms if s.resistance_ohms is not None else 0.0 for s in samples],
    }
    return pd.DataFrame(data)


def dataframe_to_samples(df: pd.DataFrame) -> List[Sample]:
    """Convert pandas DataFrame to list of samples."""
    samples = []
    for _, row in df.iterrows():
        timestamp = datetime.fromisoformat(row["timestamp_iso8601"])
        
        # Handle both old (capacitance only) and new (both types) CSV formats
        capacitance_farads = None
        resistance_ohms = None
        
        if "capacitance_F" in row and row["capacitance_F"] != 0.0:
            capacitance_farads = float(row["capacitance_F"])
        
        if "resistance_Ohm" in row and row["resistance_Ohm"] != 0.0:
            resistance_ohms = float(row["resistance_Ohm"])
        
        sample = Sample(
            timestamp=timestamp,
            t_seconds=float(row["t_seconds"]),
            capacitance_farads=capacitance_farads,
            resistance_ohms=resistance_ohms,
        )
        samples.append(sample)
    return samples
