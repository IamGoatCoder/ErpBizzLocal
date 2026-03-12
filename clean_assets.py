#!/usr/bin/env python3
"""Clean up orphaned asset attachments."""

import psycopg2

# Database connection parameters
dbname = "new_smb_db"
user = "odoo"
password = "odoo"
host = "localhost"

try:
    # Connect to database
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host
    )
    cursor = conn.cursor()
    
    # Count attachments before deletion
    cursor.execute("SELECT COUNT(*) FROM ir_attachment WHERE url LIKE '/web/assets/%'")
    count = cursor.fetchone()[0]
    print(f"Found {count} asset attachments to delete")
    
    # Delete asset attachments
    cursor.execute("DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%'")
    conn.commit()
    
    print(f"Deleted {count} asset attachments successfully")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    raise

print("\nAssets cleanup complete. Restart the server to regenerate assets.")
