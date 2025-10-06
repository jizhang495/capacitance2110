"""Path utilities for the capacitance monitor application."""

from pathlib import Path


def get_app_directory() -> Path:
    """Get the directory where the application is located."""
    return Path(__file__).parent.absolute()


def get_measurements_directory() -> Path:
    """Get the directory for storing measurement data."""
    measurements_dir = get_app_directory() / "measurements"
    measurements_dir.mkdir(exist_ok=True)
    return measurements_dir


def get_logs_directory() -> Path:
    """Get the directory for storing log files."""
    logs_dir = get_app_directory() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_config_directory() -> Path:
    """Get the directory for storing configuration files."""
    config_dir = get_app_directory() / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir
