"""Unit tests for capacitance unit conversion and formatting."""

import pytest

from core.units import (
    format_capacitance,
    get_typical_ranges,
    parse_capacitance_string,
    format_frequency,
)


class TestFormatCapacitance:
    """Test capacitance formatting functions."""
    
    def test_format_capacitance_auto_pf(self):
        """Test auto-formatting for picofarad range."""
        value, unit, factor = format_capacitance(1e-12, "auto")
        assert value == 1.0
        assert unit == "pF"
        assert factor == 1e-12
    
    def test_format_capacitance_auto_nf(self):
        """Test auto-formatting for nanofarad range."""
        value, unit, factor = format_capacitance(1e-9, "auto")
        assert value == 1.0
        assert unit == "nF"
        assert factor == 1e-9
    
    def test_format_capacitance_auto_uf(self):
        """Test auto-formatting for microfarad range."""
        value, unit, factor = format_capacitance(1e-6, "auto")
        assert value == 1.0
        assert unit == "µF"
        assert factor == 1e-6
    
    def test_format_capacitance_auto_f(self):
        """Test auto-formatting for farad range."""
        value, unit, factor = format_capacitance(1e-3, "auto")
        assert value == 1e-3
        assert unit == "F"
        assert factor == 1.0
    
    def test_format_capacitance_specific_unit(self):
        """Test formatting with specific unit."""
        value, unit, factor = format_capacitance(1e-9, "pF")
        assert value == 1000.0
        assert unit == "pF"
        assert factor == 1e-12
    
    def test_format_capacitance_zero(self):
        """Test formatting zero value."""
        value, unit, factor = format_capacitance(0.0, "auto")
        assert value == 0.0
        assert unit == "pF"  # Should default to smallest unit
        assert factor == 1e-12
    
    def test_format_capacitance_negative(self):
        """Test formatting negative value."""
        value, unit, factor = format_capacitance(-1e-9, "auto")
        assert value == -1.0
        assert unit == "nF"
        assert factor == 1e-9


class TestParseCapacitanceString:
    """Test capacitance string parsing functions."""
    
    def test_parse_capacitance_string_pf(self):
        """Test parsing picofarad string."""
        result = parse_capacitance_string("1000", "pF")
        assert result == 1e-9  # 1000 pF = 1 nF
    
    def test_parse_capacitance_string_nf(self):
        """Test parsing nanofarad string."""
        result = parse_capacitance_string("1", "nF")
        assert result == 1e-9
    
    def test_parse_capacitance_string_uf(self):
        """Test parsing microfarad string."""
        result = parse_capacitance_string("1", "µF")
        assert result == 1e-6
    
    def test_parse_capacitance_string_f(self):
        """Test parsing farad string."""
        result = parse_capacitance_string("1", "F")
        assert result == 1.0
    
    def test_parse_capacitance_string_float(self):
        """Test parsing float string."""
        result = parse_capacitance_string("1.5", "nF")
        assert result == 1.5e-9
    
    def test_parse_capacitance_string_invalid(self):
        """Test parsing invalid string."""
        with pytest.raises(ValueError):
            parse_capacitance_string("invalid", "nF")
    
    def test_parse_capacitance_string_invalid_unit(self):
        """Test parsing with invalid unit."""
        with pytest.raises(ValueError):
            parse_capacitance_string("1", "invalid")


class TestGetTypicalRanges:
    """Test typical range functions."""
    
    def test_get_typical_ranges_nf(self):
        """Test getting typical ranges in nF."""
        ranges = get_typical_ranges("nF")
        assert len(ranges) > 0
        assert all(r > 0 for r in ranges)
        assert 1.0 in ranges  # 1 nF should be in the list
    
    def test_get_typical_ranges_pf(self):
        """Test getting typical ranges in pF."""
        ranges = get_typical_ranges("pF")
        assert len(ranges) > 0
        assert all(r > 0 for r in ranges)
        assert 1000.0 in ranges  # 1000 pF should be in the list
    
    def test_get_typical_ranges_uf(self):
        """Test getting typical ranges in µF."""
        ranges = get_typical_ranges("µF")
        assert len(ranges) > 0
        assert all(r > 0 for r in ranges)
        assert 1.0 in ranges  # 1 µF should be in the list
    
    def test_get_typical_ranges_f(self):
        """Test getting typical ranges in F."""
        ranges = get_typical_ranges("F")
        assert len(ranges) > 0
        assert all(r > 0 for r in ranges)
        assert 1e-3 in ranges  # 1 mF should be in the list
    
    def test_get_typical_ranges_invalid_unit(self):
        """Test getting ranges with invalid unit."""
        with pytest.raises(ValueError):
            get_typical_ranges("invalid")


class TestFormatFrequency:
    """Test frequency formatting functions."""
    
    def test_format_frequency_hz(self):
        """Test formatting frequency in Hz."""
        value, unit = format_frequency(100.0)
        assert value == 100.0
        assert unit == "Hz"
    
    def test_format_frequency_khz(self):
        """Test formatting frequency in kHz."""
        value, unit = format_frequency(1500.0)
        assert value == 1.5
        assert unit == "kHz"
    
    def test_format_frequency_mhz(self):
        """Test formatting frequency in MHz."""
        value, unit = format_frequency(2.5e6)
        assert value == 2.5
        assert unit == "MHz"
    
    def test_format_frequency_zero(self):
        """Test formatting zero frequency."""
        value, unit = format_frequency(0.0)
        assert value == 0.0
        assert unit == "Hz"
    
    def test_format_frequency_negative(self):
        """Test formatting negative frequency."""
        value, unit = format_frequency(-100.0)
        assert value == -100.0
        assert unit == "Hz"


class TestRoundTrip:
    """Test round-trip conversion accuracy."""
    
    def test_round_trip_pf(self):
        """Test round-trip conversion for pF."""
        original = 1e-12
        value, unit, factor = format_capacitance(original, "pF")
        parsed = parse_capacitance_string(str(value), unit)
        assert abs(parsed - original) < 1e-18
    
    def test_round_trip_nf(self):
        """Test round-trip conversion for nF."""
        original = 1e-9
        value, unit, factor = format_capacitance(original, "nF")
        parsed = parse_capacitance_string(str(value), unit)
        assert abs(parsed - original) < 1e-18
    
    def test_round_trip_uf(self):
        """Test round-trip conversion for µF."""
        original = 1e-6
        value, unit, factor = format_capacitance(original, "µF")
        parsed = parse_capacitance_string(str(value), unit)
        assert abs(parsed - original) < 1e-18
    
    def test_round_trip_f(self):
        """Test round-trip conversion for F."""
        original = 1.0
        value, unit, factor = format_capacitance(original, "F")
        parsed = parse_capacitance_string(str(value), unit)
        assert abs(parsed - original) < 1e-18
