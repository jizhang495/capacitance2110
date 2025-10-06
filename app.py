"""Main application entry point for the capacitance monitor."""

import argparse
import logging
import logging.handlers
import sys
from pathlib import Path

import appdirs
from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

from core import AppConfig
from ui import MainWindow

# Load environment variables from .env file
load_dotenv()


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler (rotating)
    from path import get_logs_directory
    log_dir = get_logs_directory()
    log_file = log_dir / "capacitance-monitor.log"
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from some libraries
    logging.getLogger("pyvisa").setLevel(logging.WARNING)
    logging.getLogger("PySide6").setLevel(logging.WARNING)


def load_config(args) -> AppConfig:
    """Load application configuration."""
    from path import get_config_directory
    
    config_dir = get_config_directory()
    config_file = config_dir / "config.json"
    
    try:
        config = AppConfig.load_from_file(config_file)
    except Exception:
        # Create default config
        config = AppConfig()
    
    # Override with command line arguments
    if args.mock:
        config.use_mock_instrument = True
    
    if args.resource:
        config.visa_resource = args.resource
        config.use_mock_instrument = False
    
    return config


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Capacitance Monitor for Keithley 2110 DMM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py --mock                    # Run with mock instrument
  python app.py --resource "USB0::..."   # Run with real instrument
  python app.py --debug                  # Run with debug logging
        """
    )
    
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock instrument for testing (default: False)"
    )
    
    parser.add_argument(
        "--resource",
        type=str,
        help="VISA resource string for real instrument (deprecated: use GUI instrument selection instead)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    logger.info("Starting Capacitance Monitor application")
    
    try:
        # Load configuration
        config = load_config(args)
        logger.info(f"Configuration loaded: mock={config.use_mock_instrument}")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Capacitance Monitor")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("Capacitance Monitor")
        
        # Create main window
        main_window = MainWindow(config)
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
