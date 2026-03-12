import sys
from odoo.cli.server import Server

class Run(Server):
    name = "run"
    
    def run(self, args):
        # Default flags for "run"
        # We use sys.argv[0:1] to keep the script name, 
        # but odoo's config._parse_config expects just the options
        default_args = [
            "-d", "odoo19",
            "--dev=all"
        ]
        
        # Merge with any extra arguments passed via command line
        # e.g. python odoo-bin run --db-filter=...
        super().run(default_args + args)
