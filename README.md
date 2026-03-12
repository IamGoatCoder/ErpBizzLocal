# ErpBizz (SMBs Branch)

This branch contains a lightweight version of ErpBizz tailored for SMBs in India, typically requiring only Inventory, Invoicing, POS, Purchase, Sales, and Taxation.

**Note:** If you are switching to this branch from `main`, you must use a **fresh database** or ensure all removed modules (HR, CRM, Project, Marketing, Google/Microsoft integrations) are uninstalled first. Otherwise, you will encounter client errors like `field is undefined`.

---

## Prerequisites

| Dependency  | Version             | Notes                              |
| ----------- | ------------------- | ---------------------------------- |
| Python      | 3.13.2              | Must be added to system PATH       |
| PostgreSQL  | 10 or higher        | Service must be running            |
| Git         | Latest              | For cloning the repository         |
| Wkhtmltopdf | 0.12.6 (patched Qt) | Required for PDF report generation |

> **Wkhtmltopdf:** Download the patched Qt version from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html). The standard version from package managers will not render reports correctly.

---

## Environment Setup (Development)

Use this when you need a full working copy for development, debugging, or contributing.

### 1. Clone and enter the repository

```bash
git clone <repo-url> C:\ErpBizz
cd C:\ErpBizz
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
.\venv\Scripts\activate.bat

# Linux/macOS
source venv/bin/activate
```

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up PostgreSQL user and database

Open a terminal with `psql` access (or use pgAdmin):

```sql
-- Create the odoo role (one-time)
CREATE USER odoo WITH CREATEDB PASSWORD 'odoo';
```

### 6. Create a new database and initialise base module

```bash
python run.py -d new_smb_db -i base
```

This creates the database `new_smb_db` using the `odoo` user configured in `odoo.conf` and installs the `base` module.

### 7. Start the server

```bash
python run.py
```

`run.py` automatically picks up `odoo.conf` if no `-c` flag is provided. The server will be available at **http://localhost:8069**.

### 8. First login

Open **http://localhost:8069** in your browser. Create your admin account on first launch. Install the required apps (Inventory, Invoicing, POS, Purchase, Sales) from the Apps menu.

---

## Environment Setup (Business / Production-like)

Use this when deploying for actual business use on a local Windows machine.

### Quick-start (all steps)

```powershell
# 1. Clone
git clone <repo-url> C:\ErpBizz
cd C:\ErpBizz

# 2. Virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Database (requires PostgreSQL already installed and running)
psql -U postgres -c "CREATE USER odoo WITH CREATEDB PASSWORD 'odoo';"

# 5. Initialise
python run.py -d new_smb_db -i base

# 6. Run
python run.py
```

### Key configuration (`odoo.conf`)

| Setting                   | Default                               | Description                                            |
| ------------------------- | ------------------------------------- | ------------------------------------------------------ |
| `http_port`               | 8069                                  | Web server port                                        |
| `db_name`                 | new_smb_db                            | Default database name                                  |
| `db_user` / `db_password` | odoo / odoo                           | PostgreSQL credentials                                 |
| `addons_path`             | addons,odoo/addons                    | Comma-separated addon directories                      |
| `data_dir`                | `%LOCALAPPDATA%\OpenERP S.A.\ErpBizz` | Filestore and session data                             |
| `with_demo`               | False                                 | Set to `True` only for demo/testing                    |
| `list_db`                 | True                                  | Set to `False` in production to hide database selector |
| `admin_passwd`            | (hashed)                              | Master password for database management                |

> **Security:** For business use, change the default `admin_passwd` in `odoo.conf` and use a strong PostgreSQL password instead of `odoo`.

### Auto-start (Windows)

To have ErpBizz start automatically on login, create a batch script and add it to the Windows Startup folder:

```bat
@echo off
cd /d C:\ErpBizz
call venv\Scripts\activate.bat
python run.py
```

Save as `start_erpbizz.bat` and place a shortcut in `shell:startup`.

---

## Tally Data Import

The `tally_import/` directory contains scripts to migrate data from Tally to ErpBizz via XML-RPC.

1. Export your Tally data as Excel files (products, customers, vendors, invoices).
2. Place the files in `tally_import/tally_exports/`.
3. Update `tally_import/config.py` with your ErpBizz credentials (URL, database, username, password).
4. Install additional dependencies: `pip install pandas openpyxl`
5. Run the import scripts:

```bash
cd tally_import
python import_products.py
python import_partners.py
```

See `tally_import/README.md` for column format requirements.

---

## Utility Scripts

| Script            | Purpose                                              |
| ----------------- | ---------------------------------------------------- |
| `run.py`          | Starts the ErpBizz server (auto-loads `odoo.conf`)   |
| `odoo-bin`        | Low-level Odoo CLI entry point                       |
| `clean_assets.py` | Removes orphaned asset attachments from the database |

---

## Common `run.py` Commands

```bash
# Start with default config
python run.py

# Start with explicit config
python run.py -c odoo.conf

# Create/reinitialise a database with base module
python run.py -d new_smb_db -i base

# Update a specific module
python run.py -d new_smb_db -u account

# Start in developer mode (assets are not bundled)
python run.py --dev=all
```

---

## Project Structure

```
erp-bizz-local/
├── odoo-bin              # Odoo CLI entry point
├── run.py                # Convenience server launcher
├── odoo.conf             # Server configuration
├── requirements.txt      # Python dependencies
├── clean_assets.py       # DB asset cleanup utility
├── addons/               # ErpBizz addon modules (Invoicing, POS, Sales, etc.)
├── odoo/                 # Odoo core framework
├── setup/                # Packaging and deployment helpers
└── tally_import/         # Tally → ErpBizz data migration scripts
```

---

## Project Roadmap

### Features

- [ ] In-Built GST templates
- [ ] Default addons as git branches
- [ ] Remove unwanted options from apps

### Testing & Verification

- [ ] Test by cloning the app again in test folder

### Automation & Installer

Goal: Create a GUI installer (Python executable) that automates the full setup:

1. [ ] Install Git, Python 3.13.2 and add to PATH
2. [ ] Install Wkhtmltopdf (patched Qt)
3. [ ] Clone the ErpBizz repository to `C:\ErpBizz`
4. [ ] Create virtual environment (`python -m venv venv`) and activate it
5. [ ] Upgrade pip (`python -m pip install --upgrade pip`)
6. [ ] Install PostgreSQL, create `odoo` user with CREATEDB and password `odoo`
7. [ ] Install Python dependencies (`pip install -r requirements.txt`)
8. [ ] On success: install default SMB modules/configs and remove the installer `.exe`
9. [ ] Create and initialise the database (`python run.py -d new_smb_db -i base`)
10. [ ] Start the ErpBizz server (`python run.py`)
11. [ ] User creates admin login and performs manual setup
12. [ ] Create a PWA shortcut for easy Windows access (background process)

---

## Getting Started with ErpBizz

To learn the software, we recommend the [ErpBizz eLearning](https://www.odoo.com/slides),
or [Scale-up, the business game](https://www.odoo.com/page/scale-up-business-game).
Developers can start with [the developer tutorials](https://www.odoo.com/documentation/master/developer/howtos.html).

---

## Demo Checklist

1. Show the demo to the client and ask for feedback.
2. Ask about the client's business processes and requirements.
3. Ask about how they use ledger, inventory, and sales.
4. Ask about their current software and what they like/dislike about it.
5. Ask about their pain points and what they want to improve.
6. Test import-export of data from their current software to ErpBizz (see Tally Import above).
