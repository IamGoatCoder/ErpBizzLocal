"""Configuration for Tally to Odoo import."""

# Odoo Connection Settings
ODOO_URL = "http://localhost:8069"
ODOO_DB = "new_smb_db"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "admin"

# File paths for Tally exports (Excel/CSV format)
TALLY_PRODUCTS_FILE = "tally_exports/products.xlsx"
TALLY_CUSTOMERS_FILE = "tally_exports/customers.xlsx"
TALLY_VENDORS_FILE = "tally_exports/vendors.xlsx"
TALLY_INVOICES_FILE = "tally_exports/invoices.xlsx"

# Mapping configurations
DEFAULT_COMPANY_ID = 1  # Your company ID in Odoo
DEFAULT_CURRENCY_ID = 20  # INR currency ID (check in Odoo)
DEFAULT_PRODUCT_CATEGORY = 1  # All category

# GST Rate mapping (Tally → Odoo)
GST_MAPPING = {
    "GST 0%": 0,
    "GST 5%": 5,
    "GST 12%": 12,
    "GST 18%": 18,
    "GST 28%": 28,
    "IGST 5%": 5,
    "IGST 12%": 12,
    "IGST 18%": 18,
    "IGST 28%": 28,
}

# Unit of Measure mapping (Tally → Odoo)
UOM_MAPPING = {
    "Nos": "Units",
    "Pcs": "Units",
    "Kg": "kg",
    "Gms": "g",
    "Ltr": "L",
    "Mtr": "m",
    "Box": "Units",
    "Set": "Units",
}
