"""CSV I/O utilities for saving and loading measurement data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from .models import MeasurementMetadata, Sample


def save_csv(
    filepath: Path,
    samples: List[Sample],
    metadata: MeasurementMetadata,
    include_metadata: bool = True,
) -> None:
    """
    Save measurement data to CSV file.
    
    Args:
        filepath: Path to save the CSV file
        samples: List of measurement samples
        metadata: Measurement session metadata
        include_metadata: Whether to include metadata as CSV header comments
    """
    if not samples:
        raise ValueError("Cannot save empty measurement data")
    
    # Convert samples to DataFrame
    df = pd.DataFrame({
        "timestamp_iso8601": [s.timestamp.isoformat() for s in samples],
        "t_seconds": [s.t_seconds for s in samples],
        "capacitance_F": [s.capacitance_farads for s in samples],
    })
    
    # Create output file
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        if include_metadata:
            # Write metadata as comments
            f.write("# Capacitance Measurement Data\n")
            f.write(f"# Generated: {metadata.start_time.isoformat()}\n")
            f.write(f"# Instrument: {metadata.instrument_type}\n")
            if metadata.visa_resource:
                f.write(f"# Resource: {metadata.visa_resource}\n")
            f.write(f"# Sample Period: {metadata.sample_period_ms} ms\n")
            f.write(f"# Autorange: {metadata.autorange_enabled}\n")
            if metadata.manual_range_farads:
                f.write(f"# Manual Range: {metadata.manual_range_farads} F\n")
            f.write(f"# Sample Count: {metadata.sample_count}\n")
            f.write(f"# Soft Errors: {metadata.soft_error_count}\n")
            f.write("#\n")
        
        # Write CSV data
        df.to_csv(f, index=False, float_format="%.12e")


def load_csv(filepath: Path) -> Tuple[List[Sample], Optional[MeasurementMetadata]]:
    """
    Load measurement data from CSV file.
    
    Args:
        filepath: Path to the CSV file
    
    Returns:
        Tuple of (samples, metadata)
    """
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    # Read CSV file, skipping comment lines
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find start of data (first non-comment line)
    data_start = 0
    metadata_dict = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("#"):
            # Parse metadata from comments
            if ":" in line and not line.startswith("# "):
                key, value = line[1:].split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                
                # Convert known fields
                if key == "generated":
                    try:
                        from datetime import datetime
                        metadata_dict["start_time"] = datetime.fromisoformat(value)
                    except ValueError:
                        pass
                elif key == "instrument":
                    metadata_dict["instrument_type"] = value
                elif key == "resource":
                    metadata_dict["visa_resource"] = value
                elif key == "sample_period":
                    try:
                        metadata_dict["sample_period_ms"] = int(value.replace(" ms", ""))
                    except ValueError:
                        pass
                elif key == "autorange":
                    metadata_dict["autorange_enabled"] = value.lower() == "true"
                elif key == "manual_range":
                    try:
                        metadata_dict["manual_range_farads"] = float(value.replace(" F", ""))
                    except ValueError:
                        pass
                elif key == "sample_count":
                    try:
                        metadata_dict["sample_count"] = int(value)
                    except ValueError:
                        pass
                elif key == "soft_errors":
                    try:
                        metadata_dict["soft_error_count"] = int(value)
                    except ValueError:
                        pass
        else:
            data_start = i
            break
    
    # Read the actual CSV data
    csv_content = "".join(lines[data_start:])
    from io import StringIO
    df = pd.read_csv(StringIO(csv_content))
    
    # Validate required columns
    required_columns = ["timestamp_iso8601", "t_seconds", "capacitance_F"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Convert DataFrame to samples
    samples = []
    for _, row in df.iterrows():
        from datetime import datetime
        timestamp = datetime.fromisoformat(row["timestamp_iso8601"])
        sample = Sample(
            timestamp=timestamp,
            t_seconds=float(row["t_seconds"]),
            capacitance_farads=float(row["capacitance_F"]),
        )
        samples.append(sample)
    
    # Create metadata object if we have enough information
    metadata = None
    if metadata_dict:
        try:
            # Set defaults for missing fields
            metadata_dict.setdefault("start_time", samples[0].timestamp if samples else None)
            metadata_dict.setdefault("end_time", samples[-1].timestamp if samples else None)
            metadata_dict.setdefault("sample_count", len(samples))
            metadata_dict.setdefault("sample_period_ms", 100)
            metadata_dict.setdefault("autorange_enabled", True)
            metadata_dict.setdefault("instrument_type", "unknown")
            metadata_dict.setdefault("soft_error_count", 0)
            
            metadata = MeasurementMetadata(**metadata_dict)
        except Exception:
            # If metadata parsing fails, continue without it
            metadata = None
    
    return samples, metadata


def get_csv_info(filepath: Path) -> dict:
    """
    Get basic information about a CSV file without loading all data.
    
    Args:
        filepath: Path to the CSV file
    
    Returns:
        Dictionary with file information
    """
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    
    # Read first few lines to get metadata
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    info = {
        "filepath": str(filepath),
        "size_bytes": filepath.stat().st_size,
        "instrument_type": "unknown",
        "start_time": None,
        "sample_count": 0,
        "sample_period_ms": 100,
    }
    
    # Parse metadata from comments
    for line in lines[:20]:  # Only check first 20 lines
        line = line.strip()
        if line.startswith("#") and ":" in line:
            key, value = line[1:].split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            
            if key == "instrument":
                info["instrument_type"] = value
            elif key == "generated":
                try:
                    from datetime import datetime
                    info["start_time"] = datetime.fromisoformat(value)
                except ValueError:
                    pass
            elif key == "sample_count":
                try:
                    info["sample_count"] = int(value)
                except ValueError:
                    pass
            elif key == "sample_period":
                try:
                    info["sample_period_ms"] = int(value.replace(" ms", ""))
                except ValueError:
                    pass
    
    return info
