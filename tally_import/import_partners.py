"""Import customers and vendors from Tally export to Odoo."""

import pandas as pd
import logging
from odoo_connector import OdooConnector
from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PartnerImporter:
    """Import customers and vendors from Tally to Odoo."""
    
    def __init__(self, odoo: OdooConnector):
        self.odoo = odoo
        self.success_count = 0
        self.error_count = 0
        self.skipped_count = 0
    
    def map_partner_data(self, row: pd.Series, partner_type: str) -> dict:
        """Map Tally partner data to Odoo format.
        
        Args:
            row: Pandas series with Tally data
            partner_type: 'customer' or 'vendor'
        """
        
        # Determine country (default India)
        country_id = self._get_country_id(row.get('Country', 'India'))
        
        # Determine state
        state_id = None
        if 'State' in row and pd.notna(row['State']):
            state_id = self._get_state_id(row['State'], country_id)
        
        # Build partner values
        partner_data = {
            'name': row['Party Name'],
            'street': row.get('Address Line 1', ''),
            'street2': row.get('Address Line 2', ''),
            'city': row.get('City', ''),
            'state_id': state_id,
            'zip': str(row.get('PIN Code', '')) if pd.notna(row.get('PIN Code')) else '',
            'country_id': country_id,
            'phone': str(row.get('Phone', '')),
            'mobile': str(row.get('Mobile', '')),
            'email': row.get('Email', ''),
            'website': row.get('Website', ''),
            'vat': str(row.get('GSTIN', '')) if pd.notna(row.get('GSTIN')) else '',  # GST Number
            'company_type': 'company' if row.get('Company Type') == 'Company' else 'person',
        }
        
        # Set partner type flags
        if partner_type == 'customer':
            partner_data['customer_rank'] = 1
        elif partner_type == 'vendor':
            partner_data['supplier_rank'] = 1
        
        # Indian localization fields
        if 'PAN' in row and pd.notna(row['PAN']):
            partner_data['l10n_in_pan'] = str(row['PAN'])
        
        return partner_data
    
    def _get_country_id(self, country_name: str) -> int:
        """Get country ID by name."""
        domain = [('name', 'ilike', country_name)]
        countries = self.odoo.search_read('res.country', domain, ['id'])
        
        if countries:
            return countries[0]['id']
        
        # Default to India
        return 104  # India ID (check in your Odoo)
    
    def _get_state_id(self, state_name: str, country_id: int) -> int:
        """Get state ID by name and country."""
        domain = [
            ('name', 'ilike', state_name),
            ('country_id', '=', country_id)
        ]
        states = self.odoo.search_read('res.country.state', domain, ['id'])
        
        if states:
            return states[0]['id']
        
        logger.warning(f"State not found: {state_name}")
        return False
    
    def import_from_excel(self, file_path: str, partner_type: str):
        """Import partners from Tally Excel export.
        
        Args:
            file_path: Path to Excel file
            partner_type: 'customer' or 'vendor'
        """
        logger.info(f"Starting {partner_type} import from {file_path}")
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            logger.info(f"Found {len(df)} {partner_type}s to import")
            
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row.get('Party Name')):
                        self.skipped_count += 1
                        continue
                    
                    # Check if partner already exists by name
                    domain = [('name', '=', row['Party Name'])]
                    
                    # Check by GSTIN if available
                    if 'GSTIN' in row and pd.notna(row['GSTIN']) and row['GSTIN']:
                        domain = ['|', ('name', '=', row['Party Name']), ('vat', '=', str(row['GSTIN']))]
                    
                    existing = self.odoo.search('res.partner', domain)
                    
                    if existing:
                        # Update existing partner type
                        update_data = {}
                        if partner_type == 'customer':
                            update_data['customer_rank'] = 1
                        elif partner_type == 'vendor':
                            update_data['supplier_rank'] = 1
                        
                        if update_data:
                            self.odoo.write('res.partner', existing[0], update_data)
                        
                        logger.info(f"Partner already exists: {row['Party Name']}")
                        self.skipped_count += 1
                        continue
                    
                    # Map and create partner
                    partner_data = self.map_partner_data(row, partner_type)
                    partner_id = self.odoo.create('res.partner', partner_data)
                    
                    if partner_id:
                        self.success_count += 1
                        logger.info(f"✓ Imported: {row['Party Name']}")
                    else:
                        self.error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error importing row {index}: {e}")
                    self.error_count += 1
            
            self._print_summary(partner_type)
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Import error: {e}")
    
    def _print_summary(self, partner_type: str):
        """Print import summary."""
        logger.info("\n" + "="*50)
        logger.info(f"{partner_type.upper()} IMPORT SUMMARY")
        logger.info("="*50)
        logger.info(f"Successfully imported: {self.success_count}")
        logger.info(f"Skipped (existing): {self.skipped_count}")
        logger.info(f"Errors: {self.error_count}")
        logger.info("="*50)


def main():
    """Main execution function."""
    # Connect to Odoo
    odoo = OdooConnector(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    
    # Import customers
    logger.info("\n=== IMPORTING CUSTOMERS ===\n")
    customer_importer = PartnerImporter(odoo)
    customer_importer.import_from_excel(TALLY_CUSTOMERS_FILE, 'customer')
    
    # Import vendors
    logger.info("\n=== IMPORTING VENDORS ===\n")
    vendor_importer = PartnerImporter(odoo)
    vendor_importer.import_from_excel(TALLY_VENDORS_FILE, 'vendor')


if __name__ == "__main__":
    main()
