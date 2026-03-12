"""Import products from Tally export to Odoo."""

import pandas as pd
import logging
from odoo_connector import OdooConnector
from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductImporter:
    """Import products from Tally to Odoo."""
    
    def __init__(self, odoo: OdooConnector):
        self.odoo = odoo
        self.success_count = 0
        self.error_count = 0
        self.skipped_count = 0
    
    def map_product_data(self, row: pd.Series) -> dict:
        """Map Tally product data to Odoo format."""
        
        # Extract GST rate
        gst_rate = GST_MAPPING.get(row.get('GST Rate', ''), 18)
        
        # Map UoM
        tally_uom = row.get('Unit', 'Nos')
        odoo_uom_name = UOM_MAPPING.get(tally_uom, 'Units')
        uom_id = self.odoo.find_uom_id(odoo_uom_name)
        
        # Find or create product category
        category_name = row.get('Category', 'All')
        category_id = self._get_or_create_category(category_name)
        
        # Build product values
        product_data = {
            'name': row['Product Name'],
            'default_code': row.get('Item Code', ''),  # Internal Reference
            'type': 'product',  # 'product' for stockable, 'consu' for consumable, 'service'
            'categ_id': category_id,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'list_price': float(row.get('Sale Price', 0)),
            'standard_price': float(row.get('Purchase Price', 0)),
            'description': row.get('Description', ''),
            'barcode': row.get('Barcode', ''),
            'active': True,
        }
        
        # Add HSN code (for Indian localization)
        if 'HSN Code' in row and pd.notna(row['HSN Code']):
            product_data['l10n_in_hsn_code'] = str(row['HSN Code'])
        
        # Add GST taxes
        if gst_rate > 0:
            tax_id = self.odoo.find_tax_id(gst_rate, 'sale')
            if tax_id:
                product_data['taxes_id'] = [(6, 0, [tax_id])]
        
        return product_data
    
    def _get_or_create_category(self, category_name: str) -> int:
        """Get or create product category."""
        if not category_name or category_name == 'All':
            return DEFAULT_PRODUCT_CATEGORY
        
        domain = [('name', '=', category_name)]
        category_id = self.odoo.get_or_create(
            'product.category',
            domain,
            {'name': category_name}
        )
        
        return category_id if category_id else DEFAULT_PRODUCT_CATEGORY
    
    def import_from_excel(self, file_path: str):
        """Import products from Tally Excel export."""
        logger.info(f"Starting product import from {file_path}")
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            logger.info(f"Found {len(df)} products to import")
            
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row.get('Product Name')):
                        self.skipped_count += 1
                        continue
                    
                    # Check if product already exists
                    domain = [('name', '=', row['Product Name'])]
                    existing = self.odoo.search('product.product', domain)
                    
                    if existing:
                        logger.info(f"Product already exists: {row['Product Name']}")
                        self.skipped_count += 1
                        continue
                    
                    # Map and create product
                    product_data = self.map_product_data(row)
                    product_id = self.odoo.create('product.product', product_data)
                    
                    if product_id:
                        self.success_count += 1
                        logger.info(f"✓ Imported: {row['Product Name']}")
                    else:
                        self.error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error importing row {index}: {e}")
                    self.error_count += 1
            
            self._print_summary()
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Import error: {e}")
    
    def _print_summary(self):
        """Print import summary."""
        logger.info("\n" + "="*50)
        logger.info("PRODUCT IMPORT SUMMARY")
        logger.info("="*50)
        logger.info(f"Successfully imported: {self.success_count}")
        logger.info(f"Skipped (existing): {self.skipped_count}")
        logger.info(f"Errors: {self.error_count}")
        logger.info("="*50)


def main():
    """Main execution function."""
    # Connect to Odoo
    odoo = OdooConnector(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    
    # Import products
    importer = ProductImporter(odoo)
    importer.import_from_excel(TALLY_PRODUCTS_FILE)


if __name__ == "__main__":
    main()
