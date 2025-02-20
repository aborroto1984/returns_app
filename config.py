db_config = {
    "ExampleDb": {
        "server": "example.database.windows.net",
        "database": "ExampleDb",
        "username": "example",
        "password": "example",
        "driver": "{ODBC Driver 17 for SQL Server}",
        "port": 1433,  # Default port for SQL Server
    },
}


def create_connection_string(server_config):
    return (
        f"DRIVER={server_config['driver']};"
        f"SERVER={server_config['server']};"
        f"PORT={server_config["port"]};DATABASE={server_config['database']};"
        f"UID={server_config['username']};"
        f"PWD={server_config['password']}"
    )


SENDER_EMAIL = "sender_email@domain.com"
SENDER_PASSWORD = "sender_password"
RECIPIENT_EMAILS = [
    "recipient_email_1@domain.com",
    "recipient_email_2@domain.com",
]  # List of emails to send the report
