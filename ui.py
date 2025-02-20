from PyQt5.QtWidgets import (
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QApplication,
    QToolTip,
    QDesktopWidget,
    QTextEdit,
    QScrollArea,
    QDialog,
)
from PyQt5.QtGui import QFont, QIcon, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from example_db import ReturnsDb
import os
import sys
from label_updater import LabelUpdater
from pallet_form import generate_and_print_pdf


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class PalletNoteDialog(QDialog):
    def __init__(self, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pallet Note")
        self.character_limit = 500  # Set the character limit

        # Create layout
        layout = QVBoxLayout(self)

        # Label
        self.label = QLabel("Pallet Note")
        layout.addWidget(self.label)

        # Scrollable text field
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(initial_text)
        self.text_edit.textChanged.connect(self.update_character_count)
        layout.addWidget(self.text_edit)

        # Character count label
        self.char_count_label = QLabel(f"0/{self.character_limit} characters")
        layout.addWidget(self.char_count_label)

        # Buttons layout
        button_layout = QHBoxLayout()

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.update_character_count()  # Update character count initially

    def update_character_count(self):
        """
        Updates the character count label and limits input to the character limit.
        """
        current_text = self.text_edit.toPlainText()
        current_length = len(current_text)

        # If text exceeds character limit, truncate it
        if current_length > self.character_limit:
            self.text_edit.setPlainText(current_text[: self.character_limit])
            # Move the cursor to the end after truncation
            self.text_edit.moveCursor(QTextCursor.End)
            current_length = self.character_limit

        # Update the character count label
        self.char_count_label.setText(
            f"{current_length}/{self.character_limit} characters"
        )

    def get_text(self):
        """
        Returns the text from the text edit field.
        """
        return self.text_edit.toPlainText()


class CustomLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        # Check if the pressed key is the Group Separator (ASCII 29)
        if event.text() == chr(29):
            # Clear the line edit
            self.clear()
        else:
            # Call the base class method to handle other key presses
            super().keyPressEvent(event)


class ClickableLabel(QLabel):
    clicked = pyqtSignal(int)  # Signal to emit the index when the label is clicked

    def __init__(self, index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)  # Emit the clicked signal with the index
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Global varibles
        self.db = ReturnsDb()
        self.fields_min_height = 60
        self.tracking_font = QFont("Arial", 32, QFont.Bold)
        self.tracking_min_height = 90
        self.current_tracking_number_was_checked_in = False
        self.do_not_update_state = False
        self.current_search_results = None
        self.originally_wrong_parts = False
        self.originally_wrong_product = False
        self.results = None
        self.current_result_index = 0
        self.current_tracking_number = None
        self.sku_status_labels = {}
        self.sku_selected_labels = {}
        self.is_pallet = False
        self.current_pallet_note = None

        self.setWindowIcon(QIcon(resource_path("RC.ico")))
        self.setWindowTitle("Returns Check-In V2.3")

        # Create the main horizontal layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(30)
        self.main_layout.setContentsMargins(40, 40, 40, 40)

        # Header section-----------------------------------------
        # Create box layout for header section
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        # Create a label for sucessful check-in
        self.check_in_label = QLabel()
        # self.check_in_label.setMinimumHeight(self.check_in_label.fontMetrics().height())
        self.check_in_label.setText(" ")
        self.check_in_label.setAlignment(Qt.AlignLeft)
        check_in_label_color = "color: green"  # Green text color
        self.check_in_label.setStyleSheet(check_in_label_color)
        header_layout.addWidget(self.check_in_label)

        # Create a label for the database connection status
        self.db_label = QLabel("Connected to Database")
        db_label_color = "color: green"  # Green text color
        self.db_label.setStyleSheet(db_label_color)
        self.db_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.db_label)

        # Add the header layout to the main layout
        self.main_layout.addLayout(header_layout)

        # Tracking number section----------------------------------------------
        # Create box layout for tracking number section
        tracking_number_layout = QVBoxLayout()
        tracking_number_layout.setSpacing(5)

        # Create a label for tracking number
        self.tracking_label = QLabel("Tracking Number:")
        self.tracking_label.setAlignment(Qt.AlignLeft)
        tracking_number_layout.addWidget(self.tracking_label)

        # Create a large text field for tracking number
        self.tracking_number_field = CustomLineEdit(self)
        self.tracking_font = self.tracking_font
        self.tracking_number_field.setFont(self.tracking_font)
        self.tracking_number_field.setPlaceholderText("Enter Tracking Number")
        self.tracking_number_field.setMinimumHeight(self.tracking_min_height)
        self.tracking_number_field.setMinimumWidth(900)
        self.tracking_number_field.returnPressed.connect(self.search_tracking_number)
        tracking_number_layout.addWidget(self.tracking_number_field)

        # Create a layout for the clear button
        clear_button_layout = QVBoxLayout()
        clear_button_layout.setSpacing(5)

        # Create a space holder for the top of the clear button
        self.clear_button_label_spacer = QLabel("")
        clear_button_layout.addWidget(self.clear_button_label_spacer)

        # Create a button to clear the tracking number
        self.clear_tracking_button = QPushButton("Clear")
        self.clear_tracking_button.setMinimumHeight(self.tracking_min_height)
        self.clear_tracking_button.clicked.connect(self.clear_button_click)
        clear_button_layout.addWidget(self.clear_tracking_button)

        # Create horizontal layout for the tracking number and clear button
        tracking_layout = QHBoxLayout()
        tracking_layout.setSpacing(0)
        tracking_layout.addLayout(tracking_number_layout)
        tracking_layout.addLayout(clear_button_layout)

        # Add the tracking layout to the main layout
        self.main_layout.addLayout(tracking_layout)

        # Drop Box section-----------------------------------------------------
        # Create verticcal layout for the sku dropdown and its label
        self.sku_layout = QVBoxLayout()
        self.sku_layout.setSpacing(10)

        # Create a label for SKU selection
        self.sku_label = QLabel("SKU:")
        self.sku_label.setAlignment(Qt.AlignLeft)
        self.sku_layout.addWidget(self.sku_label)

        # Create a dropdown menu for SKU selection
        self.sku_field = QLineEdit(self)
        self.sku_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.sku_field.setMinimumHeight(self.fields_min_height)
        self.sku_field.setPlaceholderText("SKU")
        self.sku_field.returnPressed.connect(self.search_sku_button_click)
        self.sku_field.setDisabled(True)
        self.sku_layout.addWidget(self.sku_field)

        # Create a layout for the search sku button
        self.search_button_layout = QVBoxLayout()
        # self.search_button_layout.setSpacing(5)

        # Create a space holder for the top of the clear button
        self.search_button_label_spacer = QLabel("")
        self.search_button_layout.addWidget(self.clear_button_label_spacer)

        # Create a button to clear the tracking number
        self.search_sku_button = QPushButton("Search")
        self.search_sku_button.setMinimumHeight(self.fields_min_height)
        self.search_sku_button.clicked.connect(self.search_sku_button_click)
        self.search_sku_button.setVisible(False)
        self.search_button_layout.addWidget(self.search_sku_button)

        self.sku_and_search_layout = QHBoxLayout()
        self.sku_and_search_layout.setSpacing(0)
        self.sku_and_search_layout.addLayout(self.sku_layout)
        self.sku_and_search_layout.addLayout(self.search_button_layout)

        # Create vertical layout for the status dropdown and its label
        self.status_layout = QVBoxLayout()
        self.status_layout.setSpacing(10)

        # Create a label for status selection
        self.status_label = QLabel("Select Status:")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_layout.addWidget(self.status_label)

        # Create a dropdown menu for status selection
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems(
            ["Select Status", "Complete", "Incomplete", "Wrong Part", "Wrong Product"]
        )
        self.status_dropdown.setDisabled(True)
        self.status_dropdown.currentIndexChanged.connect(self.on_status_change)
        self.status_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_dropdown.setMinimumHeight(self.fields_min_height)
        self.status_layout.addWidget(self.status_dropdown)

        # Create horizontal layout for the dropdowns
        self.dropdown_layout = QHBoxLayout()
        self.dropdown_layout.addLayout(self.sku_and_search_layout)
        self.dropdown_layout.addLayout(self.status_layout)

        # Add the dropdown layout to the main layout
        self.main_layout.addLayout(self.dropdown_layout)

        # Components section-------------------------------------------------
        # SKU layout: container for SKU labels and dropdowns
        self.sku_status_layout = QVBoxLayout()
        # self.main_layout.addLayout(self.sku_status_layout)

        # Create widgets and hide them initially (create enough for max SKUs you might have)
        self.sku_widgets = (
            []
        )  # List to hold tuples of (label, dropdown, horizontal layout)

        for _ in range(5):
            # Horizontal layout for each SKU
            h_layout = QHBoxLayout()

            # SKU label
            sku_label = QLabel("SKU")
            sku_label.setAlignment(Qt.AlignLeft)
            h_layout.addWidget(sku_label)

            # Dropdown for status
            status_dropdown = QComboBox()
            status_dropdown.setMinimumHeight(self.fields_min_height - 10)
            status_dropdown.addItems(["Good", "Damaged", "Missing"])
            status_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            status_dropdown.currentIndexChanged.connect(self.on_parts_condition_change)
            h_layout.addWidget(status_dropdown)

            # Add the horizontal layout to the vertical layout
            self.sku_status_layout.addLayout(h_layout)

            # Hide the widgets (not the layout)
            sku_label.setVisible(False)
            status_dropdown.setVisible(False)

            # Store the widgets in a list for later access
            self.sku_widgets.append((h_layout, sku_label, status_dropdown))

        # Now wrap sku_status_layout in a widget
        self.sku_status_widget = QWidget()
        self.sku_status_widget.setLayout(self.sku_status_layout)

        # Create a scroll area and add the widget to it
        self.sku_scroll_area = QScrollArea()
        self.sku_scroll_area.setMinimumHeight(250)
        self.sku_scroll_area.setWidgetResizable(True)  # Allow resizing
        self.sku_scroll_area.setWidget(
            self.sku_status_widget
        )  # Add the layout's widget to the scroll area

        # # Add the scroll area to the main layout
        # self.main_layout.addWidget(self.sku_scroll_area)

        # Note section-------------------------------------------------------
        # Create vertical layout for the note section
        self.note_layout = QVBoxLayout()
        self.note_layout.setSpacing(10)

        # Create a label for the note
        self.note_label = QLabel("Note:")
        self.note_label.setAlignment(Qt.AlignLeft)

        # Create a text field for the note
        self.note_field = QTextEdit()
        self.note_field.setPlaceholderText("Enter Note")
        self.note_field.setMinimumHeight(self.fields_min_height)
        self.note_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.note_field.textChanged.connect(self.on_note_change)

        # Create a layout for the note label and a pallet note button
        self.pallet_note_layout = QHBoxLayout()
        self.pallet_note_button = QPushButton("Create Pallet Note")
        self.pallet_note_button.setFixedSize(250, self.fields_min_height)
        self.pallet_note_button.clicked.connect(self.open_pallet_note_dialog)
        self.pallet_note_button.setVisible(False)

        self.pallet_note_layout.addWidget(self.note_label)
        self.pallet_note_layout.addWidget(self.pallet_note_button)

        # self.note_layout.addWidget(self.note_label)
        self.note_layout.addLayout(self.pallet_note_layout)
        self.note_layout.addWidget(self.note_field)

        # Create horizontal layout for the note and other sku
        self.note_other_sku_layout = QHBoxLayout()
        # self.note_other_sku_layout.addLayout(self.other_sku_layout)

        self.note_other_sku_layout.addWidget(self.sku_scroll_area)
        self.note_other_sku_layout.addLayout(self.note_layout)

        # Add the note layout to the main layout
        self.main_layout.addLayout(self.note_other_sku_layout)
        # self.main_layout.addLayout(self.sku_status_layout)

        # Information section------------------------------------------------
        # Create vertical layout for the information section desciptions
        self.info_labels_layout = QVBoxLayout()
        self.info_labels_layout.setSpacing(5)

        # Create a label for the information section description
        self.auth_label = QLabel("Authorization ID:")
        self.auth_label.setAlignment(Qt.AlignLeft)

        self.expected_label = QLabel("Expected Number of Skus:")
        self.expected_label.setAlignment(Qt.AlignLeft)

        self.received_label = QLabel("Received Number of Skus:")
        self.received_label.setAlignment(Qt.AlignLeft)

        # Add the information section descriptions to the layout
        self.info_labels_layout.addWidget(self.auth_label)
        self.info_labels_layout.addWidget(self.expected_label)
        self.info_labels_layout.addWidget(self.received_label)

        # Create vertical layout for the information section values
        self.info_values_layout = QVBoxLayout()
        self.info_values_layout.setSpacing(5)

        # Create labels for the information values
        self.auth_value = ClickableLabel(" ")
        self.auth_value.setAlignment(Qt.AlignRight)
        self.auth_value.clicked.connect(self.copy_auth_value)

        self.expected_value = QLabel(" ")
        self.expected_value.setAlignment(Qt.AlignRight)

        self.received_value = QLabel(" ")
        self.received_value.setAlignment(Qt.AlignRight)

        # Add the information section values to the layout
        self.info_values_layout.addWidget(self.auth_value)
        self.info_values_layout.addWidget(self.expected_value)
        self.info_values_layout.addWidget(self.received_value)

        # Create horizontal layout for the information section
        self.info_layout = QHBoxLayout()

        # Create the print checklist button
        self.print_checklist_button = QPushButton("Print Checklist")
        self.print_checklist_button.setFixedSize(250, self.tracking_min_height)
        self.print_checklist_button.clicked.connect(self.print_checklist)
        self.print_checklist_button.setVisible(self.is_pallet)

        self.info_layout.addWidget(self.print_checklist_button)
        self.info_layout.addLayout(self.info_labels_layout)
        self.info_layout.addLayout(self.info_values_layout)

        # Add the information section layout to the main layout
        self.main_layout.addLayout(self.info_layout)

        # Button section-----------------------------------------------------
        # Create a button
        self.submit_button = QPushButton("Check In Return")
        self.submit_button.setFixedSize(
            250, self.tracking_min_height
        )  # Fixed size for the button
        self.submit_button.clicked.connect(self.on_check_in)

        # Create a layout just for the button to center it
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 20)
        self.button_layout.addStretch()  # Add stretchable space before the button
        self.button_layout.addWidget(self.submit_button)
        self.button_layout.addStretch()  # Add stretchable space after the button

        # Add the button layout to the main layout
        self.main_layout.addLayout(self.button_layout)

        # Pallet section-----------------------------------------------------
        # Initialize the pallet layout
        self.pallet_layout = QVBoxLayout()
        self.pallet_layout.setSpacing(10)
        self.pallet_widget = QWidget()
        self.pallet_widget.setLayout(self.pallet_layout)

        # Create the scroll area for the pallet layout
        self.pallet_scroll_area = QScrollArea()
        self.pallet_scroll_area.setWidgetResizable(True)
        self.pallet_scroll_area.setWidget(self.pallet_widget)
        self.pallet_scroll_area.setMinimumHeight(200)
        self.pallet_scroll_area.setMinimumWidth(450)
        self.pallet_scroll_area.setVisible(False)

        # Set the layout to a central widget
        central_widget = QWidget()
        main_layout_wrapper = QHBoxLayout()
        main_layout_wrapper.addLayout(self.main_layout)
        main_layout_wrapper.addWidget(self.pallet_scroll_area)
        central_widget.setLayout(main_layout_wrapper)
        self.setCentralWidget(central_widget)

        # Center the window
        # self.center()

    # Checking in the return ------------------------------------------------------------------

    def on_check_in(self):
        if self.check_db_connection():
            tracking_number = self.tracking_number_field.text()

            if self.is_pallet:
                if self.ready_to_click_next():

                    not_updated = []
                    for result in self.results:
                        status = result[4]
                        note = result[5]
                        sku = result[0]
                        components = result[-1]
                        conditions = [condition for _, condition in components.items()]
                        if "green" in self.sku_status_labels[sku].styleSheet():
                            successfull = self.db.check_in_return(
                                tracking_number, status, note, sku, components
                            )
                            if not successfull:
                                not_updated.append(sku)

                    self.db.update_pallet_note(
                        tracking_number, self.current_pallet_note
                    )

                    if not not_updated:
                        self.check_in_label.setStyleSheet("color: green")
                        self.check_in_label.setText("Check In Successfull")
                        self.reset_fields()
                        return
                    else:
                        self.check_in_label.setStyleSheet("color: red")
                        self.check_in_label.setText(
                            f"Error checking in: {', '.join(not_updated)}"
                        )
                        return

            # Getting the values from the fields
            status = self.status_dropdown.currentText()
            note = self.note_field.toPlainText()
            # sku = self.sku_field.text()
            sku = self.results[self.current_result_index][0]
            components = self.get_sku_status_layout()
            conditions = [condition for sku, condition in components.items()]

            # Making sure the status has been selected
            if status == "Select Status":
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("Please select a status.")
                return
            # Making sure the SKU is not empty if the status is "Wrong Part"
            elif status == "Wrong Part" and not sku:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("Please enter a SKU.")
                return
            # Making sure the SKU has been verified if the status is "Wrong Part"
            elif status == "Wrong Part" and self.sku_layout_is_not_visible():
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("Please click search to verify SKU.")
                return
            # Making sure if status is incomplete, there are no missing parts
            elif status == "Incomplete" and "Missing" not in conditions:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText(
                    "Can't be Incomplete. There are no missing parts."
                )
                return
            elif status == "Complete" and "Missing" in conditions:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText(
                    "Can't be Complete. There are missing parts."
                )
                return

            successfull = self.db.check_in_return(
                tracking_number, status, note, sku, components
            )

            if not successfull:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("Error checking in.")
                return

            if self.current_tracking_number_was_checked_in and successfull:
                self.check_in_label.setStyleSheet("color: green")
                self.check_in_label.setText("Updated Successfully.")
            elif successfull:
                self.check_in_label.setStyleSheet("color: green")
                self.check_in_label.setText("Check In Successfull")

            self.reset_fields()
            return

    # Searching for a tracking number --------------------------------------------------------

    def clean_fedex_tracking_number(self, tracking_number):
        # Step 1: Remove any non-digit characters
        cleaned_number = "".join(filter(str.isdigit, tracking_number))

        if len(cleaned_number) > 30:
            self.tracking_number_field.setText(cleaned_number[-12:])
            return cleaned_number[-12:]
        else:
            return tracking_number

    def run_search_task(self, tracking_number):
        """
        This function will be run in the background. It performs the search in the database.
        """
        if self.check_db_connection():
            results = self.db.search_tracking_number(tracking_number)
            return results
        return None

    def search_tracking_number(self):
        # Step 1: Clean the tracking number
        self.reset_fields(clear_tracking=False)
        self.status_dropdown.setDisabled(False)
        tracking_number = self.tracking_number_field.text().upper().replace(" ", "")
        tracking_number = self.clean_fedex_tracking_number(tracking_number)

        self.tracking_number_field.setDisabled(True)
        self.current_tracking_number = tracking_number

        # Step 2: Set up a QTimer in the main thread to update the label
        self.loading_step = 0  # Reset the loading step
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(
            lambda: self.update_loading_label("Searching")
        )
        self.loading_timer.start(500)  # Update the label every 500ms

        # Step 3: Start the LabelUpdater (worker) to run the long-running task in a background thread
        self.label_updater = LabelUpdater(self.run_search_task, args=(tracking_number,))

        # Connect the signals
        self.label_updater.update_done.connect(self.handle_search_results)
        self.label_updater.update_failed.connect(self.handle_search_failed)

        # Start the worker thread
        self.label_updater.start()

    def update_loading_label(self, action):
        """
        Update the label text with a loading message.
        """
        self.check_in_label.setStyleSheet("color: green")
        dots = "." * (self.loading_step % 4)  # Cycle between 0 to 3 dots
        self.check_in_label.setText(f"{action}{dots}")
        self.loading_step += 1

    def stop_loading_animation(self):
        """
        Stop the QTimer and reset the label text.
        """
        if hasattr(self, "loading_timer"):
            self.loading_timer.stop()
        self.check_in_label.setText("")  # Clear the label text

    def handle_search_results(self, results):
        self.stop_loading_animation()  # Stop the loading animation
        if not results:
            self.check_in_label.setStyleSheet("color: red")
            self.check_in_label.setText("Tracking Number not found.")
        else:
            self.results = results
            if len(results) > 1:
                self.populate_pallet_list(results)
                self.is_pallet = True
                self.print_checklist_button.setVisible(True)
                self.mark_selected_sku(0)
                self.current_pallet_note = self.db.get_pallet_note(
                    self.current_tracking_number
                )
                self.pallet_note_button.setVisible(True)

            self.check_in_label.setText(" ")

            self.show_results()

    def handle_search_failed(self, error_message):
        self.stop_loading_animation()  # Stop the loading animation
        self.check_in_label.setStyleSheet("color: red")
        self.check_in_label.setText(f"Error: {error_message}")

    # Current result modifiers --------------------------------------------------------

    def on_status_change(self):
        status = self.status_dropdown.currentText()

        if status == "Wrong Part":
            if self.results[self.current_result_index][4] != "Wrong Part":
                self.swap_parts()
            self.update_current_status(status)
            self.update_note("Wrong sku was received.")
            self.clear_sku_status_layout()

            self.sku_field.setText("")
            self.sku_field.setDisabled(False)
            self.search_sku_button.setVisible(True)

        elif status == "Wrong Product":
            if self.results[self.current_result_index][4] == "Wrong Part":
                self.swap_parts()
                self.delete_worng_parts()

            self.update_current_status(status)
            self.reset_fields(clear_tracking=False)
            self.update_note("Not our product.")
            components = self.switch_all_conditions("Missing")
            self.update_sku_status_layout(components)

        elif status == "Select Status":
            if self.results[self.current_result_index][4] == "Wrong Part":
                self.swap_parts()
                self.delete_worng_parts()

            self.update_current_status(status)
            self.reset_fields(clear_tracking=False)

        else:
            if self.results[self.current_result_index][4] == "Wrong Part":
                self.swap_parts()
                self.delete_worng_parts()
                self.switch_all_conditions("Good")
                self.reset_note_to_empty()

            if self.results[self.current_result_index][4] == "Wrong Product":
                self.switch_all_conditions("Good")
                self.reset_note_to_empty()

            self.update_current_status(status)
            self.reset_fields(clear_tracking=False)

        self.show_results()

    def switch_all_conditions(self, new_condition):
        components = self.results[self.current_result_index][-1]
        components = {part: new_condition for part, contition in components.items()}
        self.update_components(components)
        return components

    def update_note(self, note):
        results = list(self.results[self.current_result_index])
        results[5] = note
        self.results[self.current_result_index] = tuple(results)
        self.note_field.setText(note)

    def update_components(self, components):
        results = list(self.results[self.current_result_index])
        results[-1] = components
        self.results[self.current_result_index] = tuple(results)

    def update_current_status(self, new_status):
        if self.results[self.current_result_index][4] != new_status:
            results = list(self.results[self.current_result_index])
            results[4] = new_status
            self.results[self.current_result_index] = tuple(results)

    def swap_parts(self):
        reults_list = list(self.results[self.current_result_index])
        temp = reults_list[-2]
        reults_list[-2] = reults_list[-1]
        reults_list[-1] = temp
        self.results[self.current_result_index] = tuple(reults_list)

    def delete_worng_parts(self):
        results = list(self.results[self.current_result_index])
        results[-2] = {}
        self.results[self.current_result_index] = tuple(results)

    def search_sku_button_click(self):
        if self.check_db_connection():
            sku = self.sku_field.text().upper()
            self.sku_field.setText(sku)
            components = self.db.verify_sku(sku)

            if self.is_pallet and self.sku_in_pallet(sku):
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("The SKU is already in the pallet.")
                return

            if components:
                self.check_in_label.setStyleSheet("color: green")
                self.check_in_label.setText("SKU found.")
                self.update_sku_status_layout(components)
                components = {part: "Good" for part in components}
                self.update_components(components)
                self.sku_field.clearFocus()
            else:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("SKU not found.")
                self.clear_sku_status_layout()

    def sku_in_pallet(self, sku):
        for result in self.results:
            if sku == self.sku_cleanner(result[0]):
                return True
        return False

    def reset_note_to_empty(self):
        self.note_field.setText("")
        self.on_note_change()

    # On changes -------------------------------------------------------------------
    def on_parts_condition_change(self):
        if self.results:
            results = list(self.results[self.current_result_index])
            if not self.do_not_update_state:
                new_components = self.get_sku_status_layout()
                results[-1] = new_components
                self.results[self.current_result_index] = tuple(results)

    def on_note_change(self):
        if self.results:
            results = list(self.results[self.current_result_index])
            if self.status_dropdown.currentText() not in [
                "Wrong Product",
                "Wrong Part",
            ]:
                new_note = self.note_field.toPlainText()
                results[5] = new_note
                self.results[self.current_result_index] = tuple(results)

    # Pallets -------------------------------------------------------------------

    def open_pallet_note_dialog(self):
        """
        Opens the pallet note dialog and returns the entered text.
        :param initial_text: Text to pre-fill in the text field.
        :return: The text entered in the text field or an empty string if no text is entered.
        """
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        dialog = PalletNoteDialog(initial_text=self.current_pallet_note)
        if dialog.exec_() == QDialog.Accepted:
            self.current_pallet_note = dialog.get_text()

    def print_checklist(self):
        authorization_id = self.results[0][1]
        tracking_number = self.current_tracking_number

        # Step 1: Set up a QTimer in the main thread to update the label
        self.loading_step = 0  # Reset the loading step
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(
            lambda: self.update_loading_label("Printing")
        )
        self.loading_timer.start(500)  # Update the label every 500ms

        # Step 2: Start the LabelUpdater (worker) to run the long-running task in a background thread
        self.label_updater = LabelUpdater(
            generate_and_print_pdf,
            args=(
                authorization_id,
                tracking_number,
                self.results,
            ),
        )

        # Connect the signals
        self.label_updater.update_done.connect(self.handle_successful_print)
        self.label_updater.update_failed.connect(self.handle_failed_print)

        # Start the worker thread
        self.label_updater.start()

    def handle_successful_print(self):
        self.stop_loading_animation()
        self.check_in_label.setText("Printed Successfully")

    def handle_failed_print(self):
        self.stop_loading_animation()
        self.check_in_label.setText("Error Printing")

    def on_sku_clicked(self, index):
        self.check_in_label.setText(" ")
        if self.ready_to_click_next():
            self.mark_selected_sku(index)
            self.reset_fields(clear_tracking=False)
            self.current_search_results = self.results[index]
            self.current_result_index = index
            self.show_results()

    def mark_selected_sku(self, index):
        # If there was a previously selected index, reset its appearance
        if self.results:
            selected_sku = self.results[index][0]
            previous_sku = self.results[self.current_result_index][0]

            selected_label = self.sku_selected_labels.get(selected_sku)
            previous_label = self.sku_selected_labels.get(previous_sku)

            if selected_label != previous_label:
                selected_label.setStyleSheet(
                    "border: 1px solid black; background-color: white;"
                )
                previous_label.setStyleSheet(
                    "border: 0px; background-color: ligh gray;"
                )
            else:
                selected_label.setStyleSheet(
                    "border: 1px solid black; background-color: white;;"
                )

    def ready_to_click_next(self):
        (
            sku,
            return_id_number,
            expected_sku_amount,
            sku_amount_received,
            status,
            note,
            received,
            wrong_parts,
            components,
        ) = self.results[self.current_result_index]

        if status != "Select Status":
            # Making sure the status has been selected
            conditions = [condition for sku, condition in components.items()]

            # Making sure the SKU is not empty if the status is "Wrong Part"
            if status == "Wrong Part" and not sku:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("Please enter a SKU.")
                return False
            # Making sure the SKU has been verified if the status is "Wrong Part"
            elif status == "Wrong Part" and self.sku_layout_is_not_visible():
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText("Please click search to verify SKU.")
                return False
            # Making sure if status is incomplete, there are no missing parts
            elif status == "Incomplete" and "Missing" not in conditions:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText(
                    "Can't be Incomplete. There are no missing parts."
                )
                return False
            elif status == "Complete" and "Missing" in conditions:
                self.check_in_label.setStyleSheet("color: red")
                self.check_in_label.setText(
                    "Can't be Complete. There are missing parts."
                )
                return False

            self.update_status_label_to_green(sku)

        elif status == "Select Status":
            self.update_status_label_to_red(sku)

        return True

    def update_status_label_to_green(self, sku):
        self.sku_status_labels[sku].setStyleSheet("color: green;")

    def update_status_label_to_red(self, sku):
        self.sku_status_labels[sku].setStyleSheet("color: red;")

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().setParent(None)
                elif child.layout() is not None:
                    self.clear_layout(child.layout())

    def clear_pallet_list(self):
        # Clear any existing items in the pallet layout
        for i in reversed(range(self.pallet_layout.count())):
            item = self.pallet_layout.itemAt(i)
            if item is not None:
                widget_to_remove = item.widget()
                if widget_to_remove is not None:
                    widget_to_remove.setParent(None)
                else:
                    # If the item is a layout, recursively delete its items
                    self.clear_layout(item.layout())
                    self.pallet_layout.removeItem(item)

        # Make the pallet scroll area invisible
        self.pallet_scroll_area.setVisible(False)

    def populate_pallet_list(self, results):
        skus = [sku for sku, _, _, _, _, _, _, _, _ in results]
        sku_and_received = {
            sku: received for sku, _, _, _, _, _, received, _, _ in results
        }
        # Clear any existing items in the pallet layout
        self.pallet_scroll_area.setVisible(True)

        for i in reversed(range(self.pallet_layout.count())):
            widget_to_remove = self.pallet_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)

        self.sku_status_labels.clear()  # Clear the status labels dictionary
        self.sku_selected_labels.clear()  # Clear the selected labels dictionary

        # Populate the pallet layout with SKUs
        for index, sku in enumerate(skus):
            # Create a horizontal layout for each SKU
            h_layout = QHBoxLayout()

            # SKU Label with index
            sku_label = ClickableLabel(index)
            sku_label.setText(self.sku_cleanner(sku))
            sku_label.setAlignment(Qt.AlignLeft)
            sku_label.setAlignment(Qt.AlignVCenter)
            sku_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            sku_label.clicked.connect(self.on_sku_clicked)  # Connect signal
            h_layout.addWidget(sku_label)

            # Status Label
            status_label = QLabel("█")
            status_label.setAlignment(Qt.AlignRight)
            status_label.setAlignment(Qt.AlignVCenter)
            if sku_and_received[sku]:
                status_label.setStyleSheet("color: green;")
            else:
                status_label.setStyleSheet("color: red;")
            status_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            h_layout.addWidget(status_label)

            # Add the horizontal layout to the pallet layout
            self.pallet_layout.addLayout(h_layout)

            # Store the status label for later updates
            self.sku_status_labels[sku] = status_label
            self.sku_selected_labels[sku] = sku_label

    # UI manipulators -------------------------------------------------------------------
    def sku_cleanner(self, sku):
        sku_and_po = sku.split("@")
        return sku_and_po[0]

    def clear_button_click(self):
        self.reset_fields(True)

    def show_results(self):
        if self.results[self.current_result_index]:
            (
                sku,
                return_id_number,
                expected_sku_amount,
                sku_amount_received,
                status,
                note,
                received,
                wrong_parts,
                components,
            ) = self.results[self.current_result_index]
            if status == "Wrong Part":
                sku = ""
            self.status_dropdown.setCurrentText(status)
            self.sku_field.setText(self.sku_cleanner(sku))
            self.auth_value.setText(return_id_number)
            self.expected_value.setText(str(expected_sku_amount))
            self.received_value.setText(
                f"{sku_amount_received} out of {expected_sku_amount}"
            )
            self.note_field.setText(note)

            if components:
                self.update_sku_status_layout(components)

            if received:
                self.check_in_label.setStyleSheet("color: green")
                self.check_in_label.setText("Tracking Number already checked in.")
                self.current_tracking_number_was_checked_in = True

    def reset_fields(self, clear_tracking=True):
        # Resetting Tracking Number field
        if clear_tracking:
            self.tracking_number_field.clear()
            self.tracking_number_field.setDisabled(False)
            self.status_dropdown.setCurrentIndex(0)
            self.status_dropdown.setDisabled(True)
            self.current_search_results = None
            self.note_field.clear()
            self.originally_wrong_parts = False
            self.originally_wrong_product = False
            self.current_tracking_number_was_checked_in = False
            self.current_result_index = 0
            self.clear_pallet_list()
            self.is_pallet = False
            self.print_checklist_button.setVisible(False)
            self.results = None
            self.pallet_note_button.setVisible(False)
            self.current_pallet_note = None

        # Resetting Information fields
        self.auth_value.setText(" ")
        self.expected_value.setText(" ")
        self.received_value.setText(" ")

        # Resetting SKU fields
        self.sku_field.clear()
        self.sku_field.setDisabled(True)
        self.clear_sku_status_layout()
        self.search_sku_button.setVisible(False)

        # Setting the focus back to the tracking number field to scan the next tracking number
        self.tracking_number_field.setFocus()

    def update_sku_status_layout(self, components):
        self.do_not_update_state = True
        # Hide all SKU widgets initially
        for layout, label, dropdown in self.sku_widgets:
            label.setVisible(False)
            dropdown.setVisible(False)

        # Get the list of SKUs from the components
        sku_list = list(components.keys())

        # Update and show only the widgets you need based on sku_list
        for i, sku in enumerate(sku_list):
            if i < len(self.sku_widgets):

                layout, label, dropdown = self.sku_widgets[i]
                contition = components[sku]
                if contition == "Good":
                    dropdown.setCurrentIndex(0)
                elif contition == "Damaged":
                    dropdown.setCurrentIndex(1)
                elif contition == "Missing":
                    dropdown.setCurrentIndex(2)
                else:
                    dropdown.setCurrentIndex(0)
                label.setText(sku)  # Update SKU label
                label.setVisible(True)  # Show the label
                dropdown.setVisible(True)  # Show the dropdown

        self.do_not_update_state = False

    def get_sku_status_layout(self):
        components = {}
        for layout, label, dropdown in self.sku_widgets:
            sku = label.text()
            if sku == "SKU":
                continue
            status = dropdown.currentText()
            if sku and status:
                components[sku] = status
        return components

    def clear_sku_status_layout(self):
        # Hide all SKU widgets
        for layout, label, dropdown in self.sku_widgets:
            label.setText("SKU")
            label.setVisible(False)
            dropdown.setVisible(False)

    def sku_layout_is_not_visible(self):
        return not any(
            label.isVisible() for layout, label, dropdown in self.sku_widgets
        )

    # Copying the authorization ID --------------------------------------------------------

    def copy_auth_value(self):
        # Get the text from the label
        value = self.auth_value.text()

        # Copy the value to the clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(value)

        # self.auth_value.setToolTip("Copied!")
        self.show_tooltip()

    def show_tooltip(self):
        # Get the position for the tooltip
        tooltip_position = self.auth_value.mapToGlobal(self.auth_value.rect().center())

        # Adjust the position slightly to ensure visibility
        screen_rect = QDesktopWidget().availableGeometry(self)
        if tooltip_position.x() + 50 > screen_rect.right():
            tooltip_position.setX(screen_rect.right() - 50)
        if tooltip_position.y() + 20 > screen_rect.bottom():
            tooltip_position.setY(screen_rect.bottom() - 20)

        # Delay showing the tooltip slightly to ensure it shows
        QTimer.singleShot(0, lambda: QToolTip.showText(tooltip_position, "Copied!"))

    # Database connection -------------------------------------------------------------------

    def check_db_connection(self):
        if self.db.check_if_connected():
            self.db_label.setText("Connected to Database")
            self.db_label.setStyleSheet("color: green")
            return True
        else:
            try:
                self.db.reconnect()
                self.db_label.setText("Connected to Database")
                self.db_label.setStyleSheet("color: green")
                return True
            except Exception as e:
                self.db_label.setText("Disconnected from Database")
                self.db_label.setStyleSheet("color: red")
                return False
