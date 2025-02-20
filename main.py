import sys
from PyQt5.QtWidgets import QApplication
from ui import MainWindow
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
import os

# To package
# pyinstaller --name ReturnsCheckIn --onefile --windowed --icon=RC.ico --add-data "C:\Users\Alfredo\Documents\DevFolder\new_code\returns\returns_app\RC.ico;." main.py


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    global_font = QFont("Arial", 18, QFont.Normal)
    app.setWindowIcon(QIcon(resource_path("RC.ico")))
    app.setFont(global_font)
    app.setStyleSheet(
        """
    /* General background for the whole application */
    QWidget {
        background-color: #f0f0f0; /* Light Gray Background */
        color: #333333; /* Dark Gray Text */
    }

    /* Button styles */
    QPushButton {
        background-color: #f39c12; /* Safety Orange Button */
        color: white; /* White Text */
        border: 1px solid #e67e22; /* Slightly darker orange border */
        padding: 6px 12px; /* Padding inside the button */
        border-radius: 0px; /* Rounded corners */
    }
    QPushButton:hover {
        background-color: #e67e22; /* Darker Orange on Hover */
    }
    QPushButton:pressed {
        background-color: #d35400; /* Even Darker Orange when pressed */
    }

    /* Label styles */
    QLabel {
        color: #333333; /* Dark Gray Text */
        background-color: #f0f0f0; /* Same as background */
    }

    /* Combo Box styles */
    QComboBox {
        background-color: white; /* White background for combo box */
        color: #333333; /* Dark Gray Text */
        border: 1px solid #bdc3c7; /* Light Gray border */
        padding: 4px; /* Padding inside the combo box */
    }
    QComboBox::drop-down {
        border-left: 1px solid #bdc3c7; /* Separate drop-down button with a border */
    }
    QComboBox::down-arrow {
        image: url(down_arrow_icon.png); /* Custom arrow icon */
        width: 10px;
        height: 10px;
    }

    /* Line Edit styles */
    QLineEdit {
        background-color: white; /* White background for line edit */
        color: #333333; /* Dark Gray Text */
        border: 1px solid #bdc3c7; /* Light Gray border */
        padding: 4px; /* Padding inside the line edit */
    }
    QTextEdit {
        background-color: white; /* White background for line edit */
        color: #333333; /* Dark Gray Text */
        border: 1px solid #bdc3c7; /* Light Gray border */
        padding: 4px; /* Padding inside the line edit */
    }
"""
    )
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
