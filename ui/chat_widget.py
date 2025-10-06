"""Chat widget for AI assistant interface."""

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QTextEdit,
    QVBoxLayout, QWidget, QFrame, QSizePolicy
)


class ChatMessageWidget(QFrame):
    """Widget for displaying a single chat message."""
    
    def __init__(self, message: str, is_user: bool = True):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        
        # Set up styling
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        
        if is_user:
            self.setStyleSheet("""
                ChatMessageWidget {
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 8px;
                    padding: 8px;
                    margin: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                ChatMessageWidget {
                    background-color: #f5f5f5;
                    border: 1px solid #9e9e9e;
                    border-radius: 8px;
                    padding: 8px;
                    margin: 4px;
                }
            """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Create label for message
        self._message_label = QLabel(message)
        self._message_label.setWordWrap(True)
        self._message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._message_label)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


class ChatWidget(QWidget):
    """Chat widget for AI assistant communication."""
    
    # Signals
    message_sent = Signal(str)  # message content
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        
        # UI components
        self._chat_area: Optional[QScrollArea] = None
        self._chat_content: Optional[QWidget] = None
        self._chat_layout: Optional[QVBoxLayout] = None
        self._input_line: Optional[QLineEdit] = None
        self._send_button: Optional[QPushButton] = None
        self._clear_button: Optional[QPushButton] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the chat widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create chat area
        self._chat_area = QScrollArea()
        self._chat_area.setWidgetResizable(True)
        self._chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget for chat messages
        self._chat_content = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_content)
        self._chat_layout.setContentsMargins(8, 8, 8, 8)
        self._chat_layout.addStretch()  # Push messages to top
        
        self._chat_area.setWidget(self._chat_content)
        layout.addWidget(self._chat_area)
        
        # Create input area
        input_layout = QHBoxLayout()
        
        self._input_line = QLineEdit()
        self._input_line.setPlaceholderText("Type your message here...")
        self._input_line.returnPressed.connect(self._on_send_clicked)
        input_layout.addWidget(self._input_line)
        
        self._send_button = QPushButton("Send")
        self._send_button.clicked.connect(self._on_send_clicked)
        self._send_button.setDefault(True)
        input_layout.addWidget(self._send_button)
        
        self._clear_button = QPushButton("Clear")
        self._clear_button.clicked.connect(self._on_clear_clicked)
        input_layout.addWidget(self._clear_button)
        
        layout.addLayout(input_layout)
        
        # Add welcome message
        self.add_message("AI Assistant", "Hello! I can help you control measurements, export data, and automate tasks. What would you like to do?", False)
    
    def add_message(self, sender: str, message: str, is_user: bool = True) -> None:
        """Add a message to the chat."""
        # Create message widget
        message_widget = ChatMessageWidget(message, is_user)
        
        # Add to layout (before the stretch)
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, message_widget)
        
        # Scroll to bottom
        self._chat_area.verticalScrollBar().setValue(
            self._chat_area.verticalScrollBar().maximum()
        )
        
        self._logger.debug(f"Added message from {sender}: {message[:50]}...")
    
    def clear_messages(self) -> None:
        """Clear all messages from the chat."""
        # Remove all widgets except the stretch
        while self._chat_layout.count() > 1:
            child = self._chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add welcome message back
        self.add_message("AI Assistant", "Chat cleared. How can I help you?", False)
    
    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        message = self._input_line.text().strip()
        if not message:
            return
        
        # Add user message to chat
        self.add_message("You", message, True)
        
        # Clear input
        self._input_line.clear()
        
        # Emit signal
        self.message_sent.emit(message)
    
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.clear_messages()
    
    def set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable input controls."""
        self._input_line.setEnabled(enabled)
        self._send_button.setEnabled(enabled)
        
        if enabled:
            self._input_line.setPlaceholderText("Type your message here...")
        else:
            self._input_line.setPlaceholderText("AI is processing...")
    
    def focus_input(self) -> None:
        """Focus the input line."""
        self._input_line.setFocus()
