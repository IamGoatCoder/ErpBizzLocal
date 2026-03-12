#!/usr/bin/env python3
import os
import sys
import subprocess

# Determine the path to the virtual environment python
venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts', 'python.exe')
if not os.path.exists(venv_python):
    # Fallback for non-Windows or if script is run differently
    venv_python = sys.executable

# Check if config is provided
args = sys.argv[1:]
if "-c" not in args and "--config" not in args and os.path.exists("odoo.conf"):
    args = ["-c", "odoo.conf"] + args

# Full command to execute
cmd = [venv_python, "odoo-bin", "run"] + args

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    pass
