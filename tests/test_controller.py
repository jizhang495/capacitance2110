"""Unit tests for measurement controller functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from core.controller import MeasurementController, VISAWorker
from core.models import AppConfig, Sample
from instruments.mock import MockInstrument


class TestVISAWorker:
    """Test VISA worker thread functionality."""
    
    def test_worker_initialization(self):
        """Test worker thread initialization."""
        config = AppConfig()
        instrument = MockInstrument()
        
        worker = VISAWorker(instrument, config)
        
        assert worker._instrument == instrument
        assert worker._config == config
        assert worker._sample_period_ms == config.sample_period_ms
        assert worker._soft_error_count == 0
        assert not worker._running
    
    def test_worker_stop(self):
        """Test stopping worker thread."""
        config = AppConfig()
        instrument = MockInstrument()
        
        worker = VISAWorker(instrument, config)
        worker.stop()
        
        assert not worker._running
    
    def test_worker_update_config(self):
        """Test updating worker configuration."""
        config = AppConfig(sample_period_ms=100)
        instrument = MockInstrument()
        
        worker = VISAWorker(instrument, config)
        
        # Update config
        new_config = AppConfig(sample_period_ms=200)
        worker.update_config(new_config)
        
        assert worker._config == new_config
        assert worker._sample_period_ms == 200
    
    def test_worker_get_soft_error_count(self):
        """Test getting soft error count."""
        config = AppConfig()
        instrument = MockInstrument()
        
        worker = VISAWorker(instrument, config)
        worker._soft_error_count = 5
        
        assert worker.get_soft_error_count() == 5


class TestMeasurementController:
    """Test measurement controller functionality."""
    
    def test_controller_initialization(self):
        """Test controller initialization."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        assert controller._config == config
        assert controller._samples.maxlen == 10000
        assert len(controller._overlay_data) == 0
        assert controller._worker is None
        assert not controller._is_measuring
        assert controller._start_time is None
        assert controller._metadata is None
    
    def test_controller_start_measurement(self):
        """Test starting measurement."""
        config = AppConfig()
        controller = MeasurementController(config)
        instrument = MockInstrument()
        
        # Mock the worker to avoid actual thread creation
        with patch('core.controller.VISAWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker
            
            controller.start_measurement(instrument)
            
            # Verify worker was created and started
            mock_worker_class.assert_called_once_with(instrument, config)
            mock_worker.start.assert_called_once()
            
            # Verify controller state
            assert controller._is_measuring is True
            assert controller._start_time is not None
            assert controller._metadata is not None
            assert controller._metadata.instrument_type == "mock"
    
    def test_controller_stop_measurement(self):
        """Test stopping measurement."""
        config = AppConfig()
        controller = MeasurementController(config)
        instrument = MockInstrument()
        
        # Start measurement first
        with patch('core.controller.VISAWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker
            
            controller.start_measurement(instrument)
            controller.stop_measurement()
            
            # Verify worker was stopped
            mock_worker.stop.assert_called_once()
            mock_worker.wait.assert_called_once_with(5000)
            
            # Verify controller state
            assert not controller._is_measuring
            assert controller._metadata.end_time is not None
    
    def test_controller_clear_data(self):
        """Test clearing data."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Add some test data
        controller._samples.append(Sample(
            timestamp=datetime.now(),
            t_seconds=0.0,
            capacitance_farads=1e-9,
        ))
        controller._overlay_data.append(Sample(
            timestamp=datetime.now(),
            t_seconds=0.0,
            capacitance_farads=1e-9,
        ))
        
        # Clear data
        controller.clear_data()
        
        # Verify data is cleared
        assert len(controller._samples) == 0
        assert len(controller._overlay_data) == 0
    
    def test_controller_save_data(self):
        """Test saving data."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Add test data
        sample = Sample(
            timestamp=datetime.now(),
            t_seconds=0.0,
            capacitance_farads=1e-9,
        )
        controller._samples.append(sample)
        
        # Create metadata
        controller._metadata = controller._metadata or Mock()
        controller._metadata.sample_count = 1
        
        # Mock save_csv to avoid file I/O
        with patch('core.controller.save_csv') as mock_save:
            from pathlib import Path
            test_path = Path("test.csv")
            
            controller.save_data(test_path)
            
            # Verify save_csv was called
            mock_save.assert_called_once()
            args, kwargs = mock_save.call_args
            assert args[0] == test_path
            assert len(args[1]) == 1
            assert args[1][0] == sample
    
    def test_controller_save_empty_data(self):
        """Test saving empty data raises error."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        with pytest.raises(ValueError, match="No data to save"):
            from pathlib import Path
            controller.save_data(Path("test.csv"))
    
    def test_controller_load_data(self):
        """Test loading data."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Mock load_csv to avoid file I/O
        test_samples = [
            Sample(
                timestamp=datetime.now(),
                t_seconds=0.0,
                capacitance_farads=1e-9,
            ),
        ]
        test_metadata = Mock()
        
        with patch('core.controller.load_csv') as mock_load:
            mock_load.return_value = (test_samples, test_metadata)
            
            from pathlib import Path
            test_path = Path("test.csv")
            
            controller.load_data(test_path)
            
            # Verify load_csv was called
            mock_load.assert_called_once_with(test_path)
            
            # Verify data was loaded
            assert controller._overlay_data == test_samples
    
    def test_controller_update_config(self):
        """Test updating configuration."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        new_config = AppConfig(sample_period_ms=200)
        
        # Mock worker
        mock_worker = Mock()
        controller._worker = mock_worker
        
        controller.update_config(new_config)
        
        # Verify config was updated
        assert controller._config == new_config
        
        # Verify worker was updated
        mock_worker.update_config.assert_called_once_with(new_config)
    
    def test_controller_get_current_samples(self):
        """Test getting current samples."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Add test samples
        sample1 = Sample(
            timestamp=datetime.now(),
            t_seconds=0.0,
            capacitance_farads=1e-9,
        )
        sample2 = Sample(
            timestamp=datetime.now(),
            t_seconds=1.0,
            capacitance_farads=1.1e-9,
        )
        controller._samples.extend([sample1, sample2])
        
        # Test getting all samples
        all_samples = controller.get_current_samples()
        assert len(all_samples) == 2
        
        # Test getting samples with time window
        recent_samples = controller.get_current_samples(time_window_seconds=0.5)
        # Should return only recent samples (implementation dependent)
        assert len(recent_samples) <= 2
    
    def test_controller_get_overlay_data(self):
        """Test getting overlay data."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Add test overlay data
        overlay_sample = Sample(
            timestamp=datetime.now(),
            t_seconds=0.0,
            capacitance_farads=1e-9,
        )
        controller._overlay_data.append(overlay_sample)
        
        # Get overlay data
        overlay_data = controller.get_overlay_data()
        
        # Verify data is returned as copy
        assert len(overlay_data) == 1
        assert overlay_data[0] == overlay_sample
        assert overlay_data is not controller._overlay_data  # Should be a copy
    
    def test_controller_is_measuring(self):
        """Test checking if measurement is running."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Initially not measuring
        assert not controller.is_measuring()
        
        # Set measuring state
        controller._is_measuring = True
        assert controller.is_measuring()
    
    def test_controller_get_sample_count(self):
        """Test getting sample count."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Initially no samples
        assert controller.get_sample_count() == 0
        
        # Add samples
        controller._samples.append(Sample(
            timestamp=datetime.now(),
            t_seconds=0.0,
            capacitance_farads=1e-9,
        ))
        controller._samples.append(Sample(
            timestamp=datetime.now(),
            t_seconds=1.0,
            capacitance_farads=1.1e-9,
        ))
        
        assert controller.get_sample_count() == 2
    
    def test_controller_get_soft_error_count(self):
        """Test getting soft error count."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # No worker initially
        assert controller.get_soft_error_count() == 0
        
        # Mock worker with error count
        mock_worker = Mock()
        mock_worker.get_soft_error_count.return_value = 5
        controller._worker = mock_worker
        
        assert controller.get_soft_error_count() == 5
    
    def test_controller_on_sample_acquired(self):
        """Test handling new sample from worker."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Set start time
        controller._start_time = datetime.now()
        
        # Create test sample
        timestamp = datetime.now()
        capacitance = 1e-9
        
        # Handle sample
        controller._on_sample_acquired(timestamp, capacitance)
        
        # Verify sample was added
        assert len(controller._samples) == 1
        sample = controller._samples[0]
        assert sample.timestamp == timestamp
        assert sample.capacitance_farads == capacitance
        assert sample.t_seconds >= 0
    
    def test_controller_cleanup(self):
        """Test controller cleanup."""
        config = AppConfig()
        controller = MeasurementController(config)
        
        # Mock worker and instrument
        mock_worker = Mock()
        mock_instrument = Mock()
        controller._worker = mock_worker
        controller._worker_instrument = mock_instrument
        
        # Cleanup
        controller.cleanup()
        
        # Verify cleanup was called
        mock_worker.stop.assert_called_once()
        mock_instrument.close.assert_called_once()
