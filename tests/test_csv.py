"""Unit tests for CSV I/O functionality."""

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from core.io_csv import load_csv, save_csv, get_csv_info
from core.models import MeasurementMetadata, Sample


class TestCSVIO:
    """Test CSV input/output functionality."""
    
    def test_save_csv_basic(self):
        """Test basic CSV save functionality."""
        # Create test data
        samples = [
            Sample(
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                t_seconds=0.0,
                capacitance_farads=1e-9,
            ),
            Sample(
                timestamp=datetime(2023, 1, 1, 12, 0, 1),
                t_seconds=1.0,
                capacitance_farads=1.1e-9,
            ),
        ]
        
        metadata = MeasurementMetadata(
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            sample_period_ms=100,
            autorange_enabled=True,
            instrument_type="mock",
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_csv(temp_path, samples, metadata)
            
            # Verify file exists and has content
            assert temp_path.exists()
            content = temp_path.read_text()
            assert "Capacitance Measurement Data" in content
            assert "timestamp_iso8601" in content
            assert "t_seconds" in content
            assert "capacitance_F" in content
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_load_csv_basic(self):
        """Test basic CSV load functionality."""
        # Create test data
        samples = [
            Sample(
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                t_seconds=0.0,
                capacitance_farads=1e-9,
            ),
            Sample(
                timestamp=datetime(2023, 1, 1, 12, 0, 1),
                t_seconds=1.0,
                capacitance_farads=1.1e-9,
            ),
        ]
        
        metadata = MeasurementMetadata(
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            sample_period_ms=100,
            autorange_enabled=True,
            instrument_type="mock",
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_csv(temp_path, samples, metadata)
            
            # Load the data back
            loaded_samples, loaded_metadata = load_csv(temp_path)
            
            # Verify samples
            assert len(loaded_samples) == 2
            assert loaded_samples[0].t_seconds == 0.0
            assert loaded_samples[0].capacitance_farads == 1e-9
            assert loaded_samples[1].t_seconds == 1.0
            assert loaded_samples[1].capacitance_farads == 1.1e-9
            
            # Verify metadata
            assert loaded_metadata is not None
            assert loaded_metadata.instrument_type == "mock"
            assert loaded_metadata.sample_period_ms == 100
            assert loaded_metadata.autorange_enabled is True
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_save_load_round_trip(self):
        """Test round-trip save/load preserves data accuracy."""
        # Create test data with various capacitance values
        samples = [
            Sample(
                timestamp=datetime(2023, 1, 1, 12, 0, i),
                t_seconds=float(i),
                capacitance_farads=1e-12 * (i + 1),  # 1 pF, 2 pF, 3 pF, etc.
            )
            for i in range(10)
        ]
        
        metadata = MeasurementMetadata(
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            sample_period_ms=50,
            autorange_enabled=False,
            manual_range_farads=1e-9,
            instrument_type="keithley2110",
            visa_resource="USB0::0x05E6::0x2110::XXXX::INSTR",
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_csv(temp_path, samples, metadata)
            loaded_samples, loaded_metadata = load_csv(temp_path)
            
            # Verify all samples match
            assert len(loaded_samples) == len(samples)
            for original, loaded in zip(samples, loaded_samples):
                assert abs(loaded.t_seconds - original.t_seconds) < 1e-9
                assert abs(loaded.capacitance_farads - original.capacitance_farads) < 1e-18
                assert loaded.timestamp == original.timestamp
            
            # Verify metadata matches
            assert loaded_metadata.instrument_type == metadata.instrument_type
            assert loaded_metadata.sample_period_ms == metadata.sample_period_ms
            assert loaded_metadata.autorange_enabled == metadata.autorange_enabled
            assert loaded_metadata.manual_range_farads == metadata.manual_range_farads
            assert loaded_metadata.visa_resource == metadata.visa_resource
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_save_empty_data(self):
        """Test saving empty data raises error."""
        metadata = MeasurementMetadata(
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            sample_period_ms=100,
            autorange_enabled=True,
            instrument_type="mock",
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="No data to save"):
                save_csv(temp_path, [], metadata)
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error."""
        nonexistent_path = Path("/nonexistent/file.csv")
        
        with pytest.raises(FileNotFoundError):
            load_csv(nonexistent_path)
    
    def test_load_invalid_csv(self):
        """Test loading invalid CSV file."""
        # Create invalid CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,csv,content\n")
            f.write("1,2,3\n")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                load_csv(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_get_csv_info(self):
        """Test getting CSV file information."""
        # Create test data
        samples = [
            Sample(
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                t_seconds=0.0,
                capacitance_farads=1e-9,
            ),
        ]
        
        metadata = MeasurementMetadata(
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            sample_period_ms=100,
            autorange_enabled=True,
            instrument_type="mock",
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_csv(temp_path, samples, metadata)
            
            # Get file info
            info = get_csv_info(temp_path)
            
            # Verify info
            assert info["filepath"] == str(temp_path)
            assert info["size_bytes"] > 0
            assert info["instrument_type"] == "mock"
            assert info["sample_count"] == 1
            assert info["sample_period_ms"] == 100
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_get_csv_info_nonexistent(self):
        """Test getting info for nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.csv")
        
        with pytest.raises(FileNotFoundError):
            get_csv_info(nonexistent_path)
    
    def test_save_without_metadata(self):
        """Test saving CSV without metadata comments."""
        samples = [
            Sample(
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                t_seconds=0.0,
                capacitance_farads=1e-9,
            ),
        ]
        
        metadata = MeasurementMetadata(
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            sample_period_ms=100,
            autorange_enabled=True,
            instrument_type="mock",
        )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            save_csv(temp_path, samples, metadata, include_metadata=False)
            
            # Verify file exists and has content
            assert temp_path.exists()
            content = temp_path.read_text()
            assert "Capacitance Measurement Data" not in content
            assert "timestamp_iso8601" in content
            assert "t_seconds" in content
            assert "capacitance_F" in content
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_load_csv_without_metadata(self):
        """Test loading CSV without metadata comments."""
        # Create CSV file without metadata
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("timestamp_iso8601,t_seconds,capacitance_F\n")
            f.write("2023-01-01T12:00:00,0.0,1e-09\n")
            f.write("2023-01-01T12:00:01,1.0,1.1e-09\n")
            temp_path = Path(f.name)
        
        try:
            loaded_samples, loaded_metadata = load_csv(temp_path)
            
            # Verify samples
            assert len(loaded_samples) == 2
            assert loaded_samples[0].t_seconds == 0.0
            assert loaded_samples[0].capacitance_farads == 1e-9
            
            # Metadata should be None since it wasn't in the file
            assert loaded_metadata is None
            
        finally:
            temp_path.unlink(missing_ok=True)
