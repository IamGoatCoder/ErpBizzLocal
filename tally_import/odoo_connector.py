"""Odoo XML-RPC connector for importing data."""

import xmlrpc.client
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OdooConnector:
    """Connect and interact with Odoo via XML-RPC."""
    
    def __init__(self, url: str, db: str, username: str, password: str):
        """Initialize Odoo connection."""
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Odoo."""
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if not self.uid:
                raise Exception("Authentication failed")
            
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            logger.info(f"Successfully authenticated as {self.username}")
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    def search(self, model: str, domain: List = None) -> List[int]:
        """Search for records."""
        if domain is None:
            domain = []
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search', [domain]
            )
        except Exception as e:
            logger.error(f"Search error in {model}: {e}")
            return []
    
    def search_read(self, model: str, domain: List = None, fields: List = None) -> List[Dict]:
        """Search and read records."""
        if domain is None:
            domain = []
        if fields is None:
            fields = []
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_read', [domain], {'fields': fields}
            )
        except Exception as e:
            logger.error(f"Search_read error in {model}: {e}")
            return []
    
    def create(self, model: str, values: Dict) -> Optional[int]:
        """Create a record."""
        try:
            record_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'create', [values]
            )
            logger.info(f"Created {model} record: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"Create error in {model}: {e}")
            logger.error(f"Values: {values}")
            return None
    
    def write(self, model: str, record_id: int, values: Dict) -> bool:
        """Update a record."""
        try:
            result = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'write', [[record_id], values]
            )
            logger.info(f"Updated {model} record: {record_id}")
            return result
        except Exception as e:
            logger.error(f"Write error in {model}: {e}")
            return False
    
    def get_or_create(self, model: str, domain: List, values: Dict) -> Optional[int]:
        """Get existing record or create new one."""
        record_ids = self.search(model, domain)
        
        if record_ids:
            logger.info(f"Found existing {model} record: {record_ids[0]}")
            return record_ids[0]
        
        return self.create(model, values)
    
    def find_tax_id(self, gst_rate: float, tax_type: str = "sale") -> Optional[int]:
        """Find GST tax ID by rate."""
        domain = [
            ('amount', '=', gst_rate),
            ('type_tax_use', '=', tax_type),
            ('country_code', '=', 'IN')
        ]
        
        tax_ids = self.search('account.tax', domain)
        
        if tax_ids:
            return tax_ids[0]
        
        logger.warning(f"Tax not found for rate {gst_rate}%")
        return None
    
    def find_uom_id(self, uom_name: str) -> Optional[int]:
        """Find Unit of Measure ID by name."""
        domain = [('name', 'ilike', uom_name)]
        uom_ids = self.search('uom.uom', domain)
        
        if uom_ids:
            return uom_ids[0]
        
        logger.warning(f"UoM not found: {uom_name}")
        # Return default Units UoM
        return 1
