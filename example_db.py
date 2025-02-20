import pyodbc
from config import create_connection_string, db_config
from datetime import datetime
import socket


class ExampleDb:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establish a new connection to the database."""
        self.conn = pyodbc.connect(create_connection_string(db_config["ExampleDb"]))
        self.cursor = self.conn.cursor()

    def check_if_connected(self):
        """Check if the database connection is active."""
        try:
            self.cursor.execute("SELECT 1")
            return True
        except (pyodbc.ProgrammingError, pyodbc.OperationalError):
            return False

    def reconnect(self):
        """Reconnect to the database if the connection is lost."""
        if not self.check_if_connected():
            self.connect()

    def get_pallet_note(self, tracking_number):
        """Check if a return has a pallet note."""
        self.cursor.execute(
            """
            SELECT pallet_note FROM ReturnPalletNotes WHERE tracking_number = ?
            """,
            tracking_number,
        )
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            self.insert_pallet_note(tracking_number, "")
            return ""

    def insert_pallet_note(self, tracking_number, pallet_note):
        """Inserts new pallet note."""
        self.cursor.execute(
            """
            INSERT INTO ReturnPalletNotes (tracking_number, pallet_note) VALUES (?, ?)
            """,
            tracking_number,
            pallet_note,
        )
        self.conn.commit()

    def update_pallet_note(self, tracking_number, pallet_note):
        """Update pallet note."""
        self.cursor.execute(
            """
            UPDATE ReturnPalletNotes SET pallet_note = ? WHERE tracking_number = ?
            """,
            pallet_note,
            tracking_number,
        )
        self.conn.commit()

    def search_tracking_number(self, tracking_number):
        """Search for a tracking number in the database."""
        tracking_number.upper()
        self.cursor.execute(
            """
            SELECT id, return_id_number, sku, po, received, status, note FROM Returns 
            WHERE tracking_number = ?
            """,
            tracking_number,
        )
        results = []
        try:
            for row in self.cursor.fetchall():
                if not row.status:
                    row.status = "Select Status"
                if not row.note:
                    row.note = ""

                results.append(
                    {
                        "id": row.id,
                        "return_id_number": row.return_id_number,
                        "sku": f"{row.sku}@{row.po}",
                        "received": row.received,
                        "status": row.status,
                        "note": row.note,
                    }
                )

        except pyodbc.ProgrammingError:
            return None

        if not results:
            return None

        results_tuples = []
        for result in results:
            result["components"] = self.get_components(result["id"])
            result["wrong_parts"] = self.get_wrong_parts(result["id"])
            result["expected_sku_amount"] = self.get_expected_sku_amount(
                result["return_id_number"]
            )
            result["sku_amount_received"] = self.get_skus_received(
                result["return_id_number"]
            )
            results_tuples.append(self.return_tuple(result))

        return results_tuples

    def return_tuple(self, result):
        if result["wrong_parts"]:
            return (
                result["sku"],
                result["return_id_number"],
                result["expected_sku_amount"],
                result["sku_amount_received"],
                result["status"],
                result["note"],
                result["received"],
                result["components"],
                result["wrong_parts"],
            )
        return (
            result["sku"],
            result["return_id_number"],
            result["expected_sku_amount"],
            result["sku_amount_received"],
            result["status"],
            result["note"],
            result["received"],
            result["wrong_parts"],
            result["components"],
        )

    def get_components(self, id):
        self.cursor.execute(
            """
            SELECT parts, condition FROM ReturnItems 
            WHERE return_id = ?
            """,
            id,
        )
        components = {}
        for row in self.cursor.fetchall():
            if not row.condition:
                row.condition = "Good"
            components[row.parts] = row.condition
        return components

    def get_wrong_parts(self, id):
        self.cursor.execute(
            """
            SELECT parts, condition FROM ReturnWrongItemsReceived 
            WHERE return_id = ?
            """,
            id,
        )
        wrong_parts = {row.parts: row.condition for row in self.cursor.fetchall()}
        return wrong_parts

    def get_expected_sku_amount(self, return_id_number):
        self.cursor.execute(
            """
            SELECT count(*) FROM Returns
            WHERE return_id_number = ?
            """,
            return_id_number,
        )
        expected_sku_amount = self.cursor.fetchone()[0]
        return expected_sku_amount

    def get_skus_received(self, return_id_number):
        self.cursor.execute(
            """
            SELECT count(*) FROM Returns
            WHERE return_id_number = ? and received = 1
            """,
            return_id_number,
        )
        sku_amount_received = self.cursor.fetchone()[0]
        return sku_amount_received

    def check_in_return(self, tracking_number, status, note, sku, components):
        """Check in a return to the database."""

        try:
            sku_and_po = sku.split("@")
            sku = sku_and_po[0]
            po = sku_and_po[1]

            if self.it_has_wrong_parts(tracking_number, sku, po):
                self.delete_wrong_parts(tracking_number, sku, po)

            checkin_station = socket.gethostname()

            self.cursor.execute(
                """
                UPDATE Returns SET received = 1, received_date= ?, status = ?, note = ?, checkin_station = ? WHERE tracking_number = ? AND sku = ? AND po = ?
                """,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status,
                note,
                checkin_station,
                tracking_number,
                sku,
                po,
            )

            self.conn.commit()

            if status == "Wrong Part":
                components_data = [
                    (tracking_number, sku, po, component, condition)
                    for component, condition in components.items()
                ]
                self.cursor.executemany(
                    """
                    INSERT INTO ReturnWrongItemsReceived (return_id, parts, condition) VALUES ((SELECT id FROM Returns WHERE tracking_number = ? AND sku = ? AND po = ?), ?, ?)
                    """,
                    components_data,
                )

                self.conn.commit()

            else:

                components_data = [
                    (condition, tracking_number, sku, po, component)
                    for component, condition in components.items()
                ]
                self.cursor.executemany(
                    """
                    UPDATE ReturnItems SET condition = ? WHERE return_id = (SELECT id FROM Returns WHERE tracking_number = ? AND  sku = ? AND po= ?) AND parts = ?
                    """,
                    components_data,
                )

                self.conn.commit()

        except pyodbc.IntegrityError:
            return False

        return True

    def it_has_wrong_parts(self, tracking_number, sku, po):
        """Check if a return is a wrong part return."""
        self.cursor.execute(
            """
            SELECT status FROM Returns WHERE tracking_number = ? AND sku = ? AND po = ?
            """,
            tracking_number,
            sku,
            po,
        )
        try:
            result = self.cursor.fetchone()[0]
        except TypeError:
            return False

        return result == "Wrong Part"

    def delete_wrong_parts(self, tracking_number, sku, po):
        """Delete wrong parts from the database."""
        self.cursor.execute(
            """
            DELETE FROM ReturnWrongItemsReceived WHERE return_id = (SELECT id FROM Returns WHERE tracking_number = ? AND sku = ? AND po = ?)
            """,
            tracking_number,
            sku,
            po,
        )
        self.conn.commit()

    def verify_sku(self, sku):
        """Verify if a SKU is in the database."""
        self.cursor.execute(
            """
            SELECT component FROM components WHERE sku = ?
            """,
            sku,
        )
        result = {}
        for row in self.cursor.fetchall():
            if row[0] is not None:
                result[row[0]] = None
            else:
                result[sku] = None

        return result

    def get_sku_component_map(self):
        """Inserts the sales data into the Sales database."""
        self.spinner.start(
            "Getting SKU ASIN Component Map from the Product Catalog database"
        )
        try:
            self.cursor.execute(
                "select * from vProductAndAliasWithComponentsView",
            )
            sku_component_map = {}
            for row in self.cursor:
                if row.component is not None and row.sku not in sku_component_map:
                    sku_component_map[row.sku] = [row.component]
                elif row.component is not None and row.sku in sku_component_map:
                    sku_component_map[row.sku].append(row.component)

            return sku_component_map

        except pyodbc.Error as e:
            print(f"Error inserting sales FBA sales data: {e}")
            raise

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None


ex_db = ExampleDb()
