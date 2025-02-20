import tempfile
import os
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing, Rect
from email_helper import send_email
import traceback


def create_pdf_report(filename, return_id_number, tracking_number, results):
    """Create a temporary PDF report for printing."""
    # Create a PDF document
    pdf_file = SimpleDocTemplate(filename, pagesize=letter)

    # Set up a stylesheet and styles for the document
    styles = getSampleStyleSheet()
    elements = []

    # Define the main header data
    header_data = [
        ["Return Id Number:", return_id_number],
        ["Tracking Number:", tracking_number],
        ["Source:", "Amazon Vendor"],
    ]

    # Add the header to the document
    for row in header_data:
        elements.append(Paragraph(f"{row[0]} {row[1]}", styles["Normal"]))

    # Add space between the header and the tables
    elements.append(Spacer(1, 12))  # 12 points space

    # Helper function to create a simulated checkbox
    def create_checkbox():
        d = Drawing(10, 10)
        d.add(
            Rect(
                0,
                0,
                10,
                10,
                strokeWidth=1,
                strokeColor=colors.black,
                fillColor=colors.white,
            )
        )
        return d

    # Process SKUs and components
    for result in results:
        sku = sku_cleanner(result[0])
        components = [component for component, _ in result[-1].items()]

        # SKU Header
        sku_header = [["Sku", "Complete", "Incomplete", "Wrong Product", "Wrong Part"]]
        components_header = [["Components", "Good", "Damaged", "Missing"]]

        # Add SKU and components table for each SKU
        data = [
            sku_header[0],
            [
                sku,
                create_checkbox(),
                create_checkbox(),
                create_checkbox(),
                create_checkbox(),
            ],
            components_header[0],
        ]

        for component in components:
            data.append(
                [component, create_checkbox(), create_checkbox(), create_checkbox()]
            )

        # Create table with consistent column widths
        table = Table(data, colWidths=[1.5 * inch] + [1 * inch] * 4)

        # Add style to prevent table splitting across pages
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    (
                        "SPLITTABLE",
                        (0, 0),
                        (-1, -1),
                        False,
                    ),  # Prevent table from splitting
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 12))  # Add space between tables

    # Build the PDF
    pdf_file.build(elements)


def try_delete_file(pdf_filename, max_retries=5, delay=2):
    """Attempt to delete the PDF file, retrying if the file is in use."""
    retries = 0
    while retries < max_retries:
        try:
            os.remove(pdf_filename)
            print(f"Temporary PDF file {pdf_filename} has been deleted.")
            return
        except PermissionError:
            print(f"File is still in use. Retrying deletion in {delay} seconds...")
            time.sleep(delay)
            retries += 1
    print(
        f"Failed to delete the temporary PDF file {pdf_filename} after {max_retries} attempts."
    )


def sku_cleanner(sku):
    sku_and_po = sku.split("@")
    return sku_and_po[0]


def generate_and_print_pdf(
    return_id_number, tracking_number, results, delay_before_delete=3
):
    """Generate the PDF, print it, and delete it after printing."""
    try:
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            pdf_filename = tmp_pdf.name

        try:
            # Create the PDF
            create_pdf_report(pdf_filename, return_id_number, tracking_number, results)

            # Print the PDF using the default viewer
            os.startfile(pdf_filename, "print")

            # Add a delay to ensure printing has started before deleting the file
            time.sleep(delay_before_delete)  # Wait before trying to delete

        finally:
            # After the delay, try to delete the temporary PDF file with retries
            try_delete_file(pdf_filename)

    except Exception as e:
        send_email(send_email("Unexpected Error", traceback.format_exc()))


# from openpyxl import Workbook
# from openpyxl.styles import Font, PatternFill, Border, Side
# from openpyxl.utils import get_column_letter
# from openpyxl.worksheet.pagebreak import Break
# import win32com.client as win32
# import os


# def auto_adjust_column_width(ws):
#     """Automatically adjust the column widths based on the content."""
#     for col in ws.columns:
#         max_length = 0
#         col_letter = get_column_letter(col[0].column)  # Get the column letter
#         for cell in col:
#             if cell.value:
#                 max_length = max(max_length, len(str(cell.value)))
#         # Set column width slightly larger than the max length
#         ws.column_dimensions[col_letter].width = max_length + 2


# def is_row_empty(ws, row_number):
#     """Check if a row is empty."""
#     for cell in ws[row_number]:
#         if cell.value is not None:
#             return False
#     return True


# def insert_page_break(ws, row_number):
#     """Insert a manual page break at the specified row."""
#     ws.row_breaks.append(Break(id=row_number))  # Add a horizontal page break


# def print_last_n_rows(ws, n):
#     """Print the last N rows of the worksheet."""
#     total_rows = ws.max_row  # Get the total number of rows
#     start_row = max(1, total_rows - n + 1)  # Determine the starting row for printing

#     # Loop through the rows from the start_row to the last row
#     for row in ws.iter_rows(min_row=start_row, max_row=total_rows, values_only=True):
#         print([cell for cell in row])


# def create_custom_excel_and_print(return_id_number, tracking_number, results):
#     """Create an Excel sheet with custom data, print with preview, and handle page breaks."""
#     # Create a workbook and add a worksheet
#     wb = Workbook()
#     ws = wb.active
#     ws.title = "ReturnsCheck"

#     # Define styles
#     header_font = Font(bold=True)
#     sku_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
#     component_fill = PatternFill(
#         start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"
#     )
#     thin_border = Border(
#         left=Side(style="thin"),
#         right=Side(style="thin"),
#         top=Side(style="thin"),
#         bottom=Side(style="thin"),
#     )

#     # Define the main header
#     main_header = [
#         ["Return Id Number:", return_id_number],
#         ["Tracking Number:", tracking_number],
#         ["Source:", "Amazon Vendor"],
#     ]

#     # Add the main header to the worksheet
#     for row in main_header:
#         ws.append(row)
#         for cell in ws[ws.max_row]:  # Use ws.max_row to get the last row
#             cell.font = header_font

#     # Add space between the main header and the table
#     ws.append([])

#     # Define the table headers
#     sku_header = [
#         "Sku",
#         "Complete",
#         "Incomplete",
#         "Wrong Product",
#         "Wrong Part",
#     ]
#     components_header = ["Components", "Good", "Damaged", "Missing"]

#     # Add empty rows
#     ws.append([])

#     # # Start with page 1
#     # page_number = 1
#     # max_rows_per_page = 44  # Maximum rows allowed per page

#     # Process SKUs and components
#     for result_index, result in enumerate(results):
#         sku = result[0]
#         components = [component for component, _ in result[-1].items()]

#         # lines_it_will_add = 2 + len(components) + 1 + 1  # Rows to be added

#         # # Insert a manual page break if the next section will exceed the page limit
#         # if ws.max_row + lines_it_will_add > (max_rows_per_page * page_number):
#         #     insert_page_break(ws, ws.max_row)
#         #     page_number += 1

#         ws.append([])  # Add space before each SKU section
#         ws.append(sku_header)  # Add SKU header
#         for cell in ws[ws.max_row]:  # Use ws.max_row to get the last row
#             cell.fill = sku_fill  # Color code SKU header
#             cell.font = header_font
#             cell.border = thin_border

#         # Add the SKU row with empty checkboxes
#         ws.append([sku, "☐", "☐", "☐", "☐"])
#         for cell in ws[ws.max_row]:  # Use ws.max_row to get the last row
#             cell.border = thin_border

#         # Add the component headers
#         ws.append(components_header)
#         for cell in ws[ws.max_row]:  # Use ws.max_row to get the last row
#             cell.fill = component_fill  # Color code component header
#             cell.font = header_font
#             cell.border = thin_border

#         # Add the components data with empty checkboxes
#         for component in components:
#             ws.append([component, "☐", "☐", "☐"])
#             for cell in ws[ws.max_row]:  # Use ws.max_row to get the last row
#                 cell.border = thin_border

#         # Add an empty row after each section
#         ws.append([])

#         # print_last_n_rows(ws, lines_it_will_add)

#         # # Insert a manual page break if the next section will exactly fill the page
#         # if ws.max_row + lines_it_will_add == (max_rows_per_page * page_number):
#         #     insert_page_break(ws, ws.max_row)
#         #     page_number += 1

#     # Adjust column widths to fit the content
#     auto_adjust_column_width(ws)

#     # # Page layout settings to ensure proper page breaks
#     # ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
#     # ws.page_setup.paperSize = ws.PAPERSIZE_LETTER  # Letter size
#     # ws.page_margins.left = 0.5  # Adjust margins to prevent content overflow
#     # ws.page_margins.right = 0.5
#     # ws.page_margins.top = 0.75
#     # ws.page_margins.bottom = 0.75
#     # ws.page_margins.header = 0.5
#     # ws.page_margins.footer = 0.5

#     # Save the workbook to a temporary file
#     temp_file_path = os.path.join(os.getcwd(), "temp_excel_file.xlsx")
#     wb.save(temp_file_path)

#     # Use Excel to open the file and show print preview
#     excel = win32.Dispatch("Excel.Application")
#     excel.Visible = True  # Show Excel window

#     # Open the workbook in Excel
#     workbook = excel.Workbooks.Open(temp_file_path)

#     try:
#         # Show the print preview dialog
#         workbook.PrintOut()  # Shows print preview dialog
#         pass
#     except Exception as e:
#         print(f"Error printing the file: {e}")
#     finally:
#         # Close the workbook and Excel
#         workbook.Close(False)
#         excel.Quit()

#     # Optionally, clean up the temporary file
#     os.remove(temp_file_path)
