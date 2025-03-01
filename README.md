# Returns Check-In System

This project provides a PyQt-based application to manage returns check-ins, update tracking information, and handle pallet form generation.

## Features
- Fetches return details from the database using tracking numbers.
- Updates return status and notes.
- Supports pallet returns with multiple SKUs.
- Generates printable pallet checklist PDFs.
- Provides a user-friendly PyQt interface.

## Project Structure
```
project_root/
├── config.py              # Configuration file for database, API, and email credentials
├── email_helper.py        # Sends email notifications
├── example_db.py          # Manages database interactions for return processing
├── label_updater.py       # Updates labels asynchronously using PyQt signals
├── main.py                # Main script launching the PyQt application
├── pallet_form.py         # Generates printable PDF checklists
├── ui.py                  # Defines the graphical user interface with PyQt
```

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/returns-checkin.git
cd returns-checkin
```

### 2. Install Dependencies
Ensure you have Python 3 installed, then install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure the System
Modify `config.py` with your database credentials.

Example database configuration:
```python
db_config = {
    "ExampleDb": {
        "server": "your.database.windows.net",
        "database": "YourDB",
        "username": "your_user",
        "password": "your_password",
        "driver": "{ODBC Driver 17 for SQL Server}",
    },
}
```

Example email configuration:
```python
SENDER_EMAIL = "your_email@example.com"
SENDER_PASSWORD = "your_email_password"
```

## Usage
Run the main script to start the application:
```bash
python main.py
```

## How It Works
1. User enters a tracking number.
2. System retrieves return details from the database.
3. User selects a return status and updates notes.
4. If part of a pallet, a checklist PDF can be printed.
5. Updated details are saved back to the database.

## Tech Stack
- Python 3
- PyQt5 (GUI framework)
- ReportLab (PDF generation)
- Azure SQL Database (`pyodbc`)
- Email Notifications (`smtplib`)

## Troubleshooting
- If the database connection fails, ensure `ODBC Driver 17` is installed.
- If emails fail to send, ensure SMTP settings allow external authentication.
- Ensure PyQt5 is installed correctly for GUI functionality.
