# Tally to Odoo Import Scripts

These scripts help you import data from Tally exports to your Odoo ERP system.

## Prerequisites

1. **Python packages** (install using pip):
```bash
pip install pandas openpyxl xmlrpc
```

2. **Tally Data Export**:
   - Export data from Tally in Excel format
   - Required columns for each export type are listed below

3. **Odoo Configuration**:
   - Update `config.py` with your Odoo credentials
   - Ensure you have API access enabled

## Directory Structure

```
tally_import/
├── __init__.py
├── config.py                  # Configuration settings
├── odoo_connector.py          # Odoo XML-RPC connector
├── import_products.py         # Product import script
├── import_partners.py         # Customer/Vendor import script
├── README.md                  # This file
└── tally_exports/            # Place your Tally export files here
    ├── products.xlsx
    ├── customers.xlsx
    ├── vendors.xlsx
    └── invoices.xlsx
```

## Excel File Format Requirements

### 1. Products Export (products.xlsx)

Required columns:
- `Product Name` - Name of the product (Required)
- `Item Code` - Internal reference/SKU
- `Category` - Product category
- `Unit` - Unit of measure (Nos, Kg, Ltr, etc.)
- `Sale Price` - Selling price
- `Purchase Price` - Cost price
- `HSN Code` - HSN code for GST
- `GST Rate` - GST percentage (e.g., "GST 18%")
- `Barcode` - Product barcode
- `Description` - Product description

**Example:**
| Product Name | Item Code | Category | Unit | Sale Price | Purchase Price | HSN Code | GST Rate | Barcode | Description |
|-------------|-----------|----------|------|------------|----------------|----------|----------|---------|-------------|
| Laptop | LAP001 | Electronics | Nos | 45000 | 40000 | 84713000 | GST 18% | 123456 | Dell Laptop |
| Rice 1Kg | RICE001 | Grocery | Kg | 60 | 50 | 10063000 | GST 5% | 789012 | Basmati Rice |

### 2. Customers Export (customers.xlsx)

Required columns:
- `Party Name` - Customer name (Required)
- `Address Line 1` - Street address
- `Address Line 2` - Additional address
- `City` - City
- `State` - State name
- `PIN Code` - Postal code
- `Country` - Country (default: India)
- `Phone` - Phone number
- `Mobile` - Mobile number
- `Email` - Email address
- `GSTIN` - GST number
- `PAN` - PAN number
- `Company Type` - "Company" or "Individual"

**Example:**
| Party Name | Address Line 1 | City | State | PIN Code | Phone | Mobile | Email | GSTIN | PAN | Company Type |
|-----------|----------------|------|-------|----------|-------|--------|-------|-------|-----|--------------|
| ABC Ltd | 123 MG Road | Mumbai | Maharashtra | 400001 | 022-12345678 | 9876543210 | abc@example.com | 27AABCU9603R1ZM | AABCU9603R | Company |

### 3. Vendors Export (vendors.xlsx)

Same format as customers.xlsx

## Usage

### 1. Configure Connection

Edit `config.py`:
```python
ODOO_URL = "http://localhost:8069"
ODOO_DB = "new_smb_db"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "admin"
```

### 2. Prepare Tally Exports

1. Export data from Tally to Excel
2. Save files in `tally_exports/` folder
3. Ensure column names match the required format

### 3. Run Import Scripts

**Import Products:**
```bash
python import_products.py
```

**Import Customers and Vendors:**
```bash
python import_partners.py
```

## Features

### Product Import
- ✅ Creates products with all attributes
- ✅ Maps Tally units to Odoo UoM
- ✅ Creates product categories automatically
- ✅ Assigns GST taxes based on rate
- ✅ Handles HSN codes for Indian localization
- ✅ Skips duplicates (checks by name)
- ✅ Detailed logging and error handling

### Partner Import (Customers/Vendors)
- ✅ Creates/updates customers and vendors
- ✅ Maps address fields including Indian states
- ✅ Handles GSTIN and PAN numbers
- ✅ Supports both company and individual partners
- ✅ Automatically links country and state
- ✅ Skips duplicates (checks by name and GSTIN)
- ✅ Detailed logging and error handling

## Customization

### Adding Custom Fields

Modify the mapping functions in respective import scripts:

```python
def map_product_data(self, row: pd.Series) -> dict:
    product_data = {
        # ... existing fields ...
        'your_custom_field': row.get('Tally Column Name', ''),
    }
    return product_data
```

### Modifying GST Mapping

Edit `config.py`:
```python
GST_MAPPING = {
    "GST 0%": 0,
    "GST 5%": 5,
    # Add more mappings
}
```

### Modifying UoM Mapping

Edit `config.py`:
```python
UOM_MAPPING = {
    "Nos": "Units",
    "Kg": "kg",
    # Add more mappings
}
```

## Troubleshooting

### Authentication Error
- Check Odoo URL, database name, username, and password in `config.py`
- Ensure Odoo is running and accessible
- Verify API access is enabled in Odoo

### File Not Found
- Ensure Excel files are in `tally_exports/` folder
- Check file names match configuration in `config.py`

### Import Errors
- Check Excel column names match requirements
- Ensure data types are correct (numbers as numbers, not text)
- Check Odoo logs for detailed error messages

### Tax/UoM Not Found
- Verify GST taxes are configured in Odoo
- Check Units of Measure exist in Odoo
- Adjust mappings in `config.py` if needed

## Advanced: Invoice Import

For invoice import (more complex), you'll need to:
1. Create invoice lines with proper tax mapping
2. Handle journal entries
3. Match customers/vendors with existing partners
4. Handle payment terms and due dates

Contact for custom invoice import script development.

## Notes

- **Test first**: Always test on a test database before production
- **Backup**: Take database backup before bulk imports
- **Data validation**: Verify imported data in Odoo after import
- **Performance**: For large datasets (>1000 records), consider batch processing
- **Duplicates**: Scripts check by name/GSTIN - customize as needed

## Support

For issues or customizations:
1. Check logs for detailed error messages
2. Verify data format and mappings
3. Test with small sample data first
4. Contact your Odoo implementation partner for complex scenarios
