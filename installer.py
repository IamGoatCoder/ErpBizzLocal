#!/usr/bin/env python3
"""
ErpBizz Installer — Professional GUI installer for Windows.

Checks for existing dependencies before installing, shows real-time
progress, and sets up a complete ErpBizz environment.

Usage:
    python installer.py          (GUI mode)
    pyinstaller --onefile --noconsole --icon=logo.ico installer.py
"""

import ctypes
import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import  font as tkfont, messagebox, ttk
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_NAME = "ErpBizz"
DEFAULT_INSTALL_DIR = r"C:\ErpBizz"
REPO_URL = "https://github.com/IamGoatCoder/ErpBizzLocal.git"
REPO_BRANCH = "SMBs"
DB_NAME = "erp_bizz"
DB_USER = "odoo"
DB_PASSWORD = "odoo"
HTTP_PORT = 8069

LOGO_RELATIVE = os.path.join("addons", "web", "static", "img", "favicon.png")

# Download URLs for silent installers
GIT_INSTALLER_URL = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/Git-2.47.1.2-64-bit.exe"
PYTHON_INSTALLER_URL = (
    "https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
)
PG_INSTALLER_URL = (
    "https://get.enterprisedb.com/postgresql/postgresql-17.2-1-windows-x64.exe"
)
WKHTML_INSTALLER_URL = "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox-0.12.6.1-3.msvc2015-win64.exe"

# Colours
BG = "#FFFFFF"
FG = "#1E1E2F"
ACCENT = "#481fb2"  # ErpBizz purple
ACCENT_HOVER = "#662cfe"
SUCCESS = "#27AE60"
ERROR = "#E74C3C"
SUBTLE = "#8C8C8C"
BORDER = "#E0E0E0"

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _run(cmd, cwd=None, env=None, timeout=600):
    """Run *cmd* and return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, "", "command not found"
    except subprocess.TimeoutExpired:
        return -2, "", "timeout"


def _which(name):
    return shutil.which(name)


def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Dependency checkers
# ---------------------------------------------------------------------------


def check_git():
    path = _which("git")
    if path:
        rc, out, _ = _run(["git", "--version"])
        if rc == 0:
            return True, out, path
    return False, None, None


def check_python():
    path = _which("python")
    if path:
        rc, out, _ = _run(["python", "--version"])
        if rc == 0:
            return True, out, path
    return False, None, None


def check_postgresql():
    """Check if PostgreSQL is installed (version check only, no connection)."""
    path = _which("psql")
    if path:
        rc, out, _ = _run(["psql", "--version"])
        if rc == 0:
            return True, out, path, True
    # Try common install locations on Windows
    for pg_dir in Path(r"C:\Program Files\PostgreSQL").glob("*"):
        psql = pg_dir / "bin" / "psql.exe"
        if psql.exists():
            rc, out, _ = _run([str(psql), "--version"])
            if rc == 0:
                return True, out, str(psql), True
    return False, None, None, False


def check_wkhtmltopdf():
    path = _which("wkhtmltopdf")
    if path:
        rc, out, _ = _run(["wkhtmltopdf", "--version"])
        if rc == 0:
            return True, out, path
    # Common Windows location
    default = Path(r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    if default.exists():
        rc, out, _ = _run([str(default), "--version"])
        if rc == 0:
            return True, out, str(default)
    return False, None, None


# ---------------------------------------------------------------------------
# Dependency auto-installers
# ---------------------------------------------------------------------------


def _refresh_path():
    """Re-read the system and user PATH from the registry so newly installed
    tools become visible without restarting the process."""
    import winreg

    parts = []
    for hive, sub in [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
        (winreg.HKEY_CURRENT_USER, r"Environment"),
    ]:
        try:
            with winreg.OpenKey(hive, sub) as key:
                val, _ = winreg.QueryValueEx(key, "Path")
                parts.append(val)
        except OSError:
            pass
    os.environ["PATH"] = ";".join(parts)


def _download(url, dest, log_fn=None):
    """Download *url* to *dest* using PowerShell (no extra deps needed)."""
    if log_fn:
        log_fn(f"  … Downloading {url.split('/')[-1]}…")
    ps_cmd = (
        f"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; "
        f'Invoke-WebRequest -Uri "{url}" -OutFile "{dest}" -UseBasicParsing'
    )
    rc, _, err = _run(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=600)
    if rc != 0:
        raise RuntimeError(f"Download failed: {err}")
    return dest


def install_git(log_fn):
    """Download and silently install Git for Windows."""
    tmp = Path(os.environ.get("TEMP", r"C:\Temp")) / "Git-Installer.exe"
    _download(GIT_INSTALLER_URL, str(tmp), log_fn)
    log_fn("  … Installing Git (silent)…")
    rc, _, err = _run(
        [
            str(tmp),
            "/VERYSILENT",
            "/NORESTART",
            "/NOCANCEL",
            "/SP-",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
            "/COMPONENTS=icons,ext,ext\\shellhere,ext\\guihere,assoc,assoc_sh",
        ],
        timeout=300,
    )
    tmp.unlink(missing_ok=True)
    if rc != 0:
        raise RuntimeError(f"Git installer failed: {err}")
    _refresh_path()


def install_python(log_fn):
    """Download and silently install Python."""
    tmp = Path(os.environ.get("TEMP", r"C:\Temp")) / "python-installer.exe"
    _download(PYTHON_INSTALLER_URL, str(tmp), log_fn)
    log_fn("  … Installing Python (silent)…")
    rc, _, err = _run(
        [str(tmp), "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0"],
        timeout=300,
    )
    tmp.unlink(missing_ok=True)
    if rc != 0:
        raise RuntimeError(f"Python installer failed: {err}")
    _refresh_path()


def install_postgresql(log_fn):
    """Download and silently install PostgreSQL."""
    tmp = Path(os.environ.get("TEMP", r"C:\Temp")) / "postgresql-installer.exe"
    _download(PG_INSTALLER_URL, str(tmp), log_fn)
    log_fn("  … Installing PostgreSQL (silent — this may take a while)…")
    rc, _, err = _run(
        [
            str(tmp),
            "--mode",
            "unattended",
            "--superpassword",
            "odoo",
            "--servicename",
            "postgresql",
            "--servicepassword",
            "odoo",
            "--serverport",
            "5432",
        ],
        timeout=600,
    )
    tmp.unlink(missing_ok=True)
    if rc != 0:
        raise RuntimeError(f"PostgreSQL installer failed: {err}")
    # Add pg bin to PATH for this session
    for pg_dir in sorted(Path(r"C:\Program Files\PostgreSQL").glob("*"), reverse=True):
        pg_bin = pg_dir / "bin"
        if pg_bin.exists():
            os.environ["PATH"] = str(pg_bin) + ";" + os.environ.get("PATH", "")
            break
    _refresh_path()


def install_wkhtmltopdf(log_fn):
    """Download and silently install wkhtmltopdf."""
    tmp = Path(os.environ.get("TEMP", r"C:\Temp")) / "wkhtmltox-installer.exe"
    _download(WKHTML_INSTALLER_URL, str(tmp), log_fn)
    log_fn("  … Installing wkhtmltopdf (silent)…")
    rc, _, err = _run([str(tmp), "/S"], timeout=300)
    tmp.unlink(missing_ok=True)
    if rc != 0:
        raise RuntimeError(f"wkhtmltopdf installer failed: {err}")
    # Add to PATH for this session
    wk_bin = Path(r"C:\Program Files\wkhtmltopdf\bin")
    if wk_bin.exists():
        os.environ["PATH"] = str(wk_bin) + ";" + os.environ.get("PATH", "")
    _refresh_path()


# ---------------------------------------------------------------------------
# Installer logic (runs in a background thread)
# ---------------------------------------------------------------------------


class InstallerWorker:
    """Performs installation steps, reporting progress via callbacks."""

    def __init__(self, install_dir, pg_superpass, on_step, on_progress, on_log, on_done):
        self.install_dir = Path(install_dir)
        self.pg_superpass = pg_superpass
        self._on_step = on_step  # fn(step_index, label)
        self._on_progress = on_progress  # fn(value 0-100)
        self._on_log = on_log  # fn(message)
        self._on_done = on_done  # fn(success, message)
        self._cancelled = False

    # -- helpers --
    def log(self, msg):
        self._on_log(msg)

    def step(self, idx, label):
        self._on_step(idx, label)

    def progress(self, val):
        self._on_progress(val)

    def fail(self, msg):
        self._on_done(False, msg)

    def _exec(self, cmd, cwd=None, env=None, timeout=600):
        self.log(f"  → {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
        rc, out, err = _run(cmd, cwd=cwd, env=env, timeout=timeout)
        if out:
            for line in out.splitlines()[-10:]:
                self.log(f"    {line}")
        if err and rc != 0:
            for line in err.splitlines()[-10:]:
                self.log(f"    ⚠ {line}")
        return rc, out, err

    # -- main pipeline --
    def run(self):
        try:
            self._run_pipeline()
        except Exception as exc:
            self.fail(f"Unexpected error: {exc}")

    def _run_pipeline(self):
        steps = [
            "Checking & installing dependencies",
            "Cloning repository",
            "Creating virtual environment",
            "Upgrading pip",
            "Installing Python packages",
            "Setting up PostgreSQL user",
            "Generating configuration",
            "Initialising database",
            "Creating app shortcut",
            "Finalising",
        ]
        total = len(steps)

        # ── Step 0: Check & install dependencies ───────────────
        self.step(0, steps[0])
        self.progress(0)

        # --- Git ---
        ok_git, git_ver, _ = check_git()
        if ok_git:
            self.log(f"  ✔ Git found: {git_ver}")
        else:
            self.log("  ✘ Git not found — installing automatically…")
            try:
                install_git(self.log)
                ok_git, git_ver, _ = check_git()
                if ok_git:
                    self.log(f"  ✔ Git installed: {git_ver}")
                else:
                    self.fail(
                        "Git installation completed but git is still not on PATH.\nPlease install Git manually and re-run."
                    )
                    return
            except Exception as e:
                self.fail(
                    f"Failed to install Git automatically:\n{e}\n\nPlease install Git manually from https://git-scm.com/downloads and re-run."
                )
                return

        # --- Python ---
        ok_py, py_ver, py_path = check_python()
        if ok_py:
            self.log(f"  ✔ Python found: {py_ver} ({py_path})")
        else:
            self.log("  ✘ Python not found — installing automatically…")
            try:
                install_python(self.log)
                ok_py, py_ver, py_path = check_python()
                if ok_py:
                    self.log(f"  ✔ Python installed: {py_ver}")
                else:
                    self.fail(
                        "Python installation completed but python is still not on PATH.\nPlease install Python manually and re-run."
                    )
                    return
            except Exception as e:
                self.fail(
                    f"Failed to install Python automatically:\n{e}\n\nPlease install Python 3.10+ manually from https://python.org/downloads and re-run."
                )
                return

        # --- PostgreSQL ---
        ok_pg, pg_ver, pg_path, _ = check_postgresql()
        if ok_pg:
            self.log(f"  ✔ PostgreSQL found: {pg_ver}")
        else:
            self.log("  ✘ PostgreSQL not found — installing automatically…")
            try:
                install_postgresql(self.log)
                ok_pg, pg_ver, pg_path, _ = check_postgresql()
                if ok_pg:
                    self.log(f"  ✔ PostgreSQL installed: {pg_ver}")
                else:
                    self.fail(
                        "PostgreSQL installation completed but psql is still not on PATH.\nPlease install PostgreSQL manually and re-run."
                    )
                    return
            except Exception as e:
                self.fail(
                    f"Failed to install PostgreSQL automatically:\n{e}\n\nPlease install PostgreSQL manually from https://www.postgresql.org/download/windows/ and re-run."
                )
                return

        # --- wkhtmltopdf ---
        ok_wk, wk_ver, _ = check_wkhtmltopdf()
        if ok_wk:
            self.log(f"  ✔ wkhtmltopdf found: {wk_ver}")
        else:
            self.log("  ⚠ wkhtmltopdf not found — installing automatically…")
            try:
                install_wkhtmltopdf(self.log)
                ok_wk, wk_ver, _ = check_wkhtmltopdf()
                if ok_wk:
                    self.log(f"  ✔ wkhtmltopdf installed: {wk_ver}")
                else:
                    self.log(
                        "  ⚠ wkhtmltopdf install finished but not detected. You can install it manually later."
                    )
            except Exception as e:
                self.log(f"  ⚠ Could not install wkhtmltopdf: {e}")
                self.log(
                    "    PDF reports won't work. Install manually later from https://wkhtmltopdf.org/downloads.html"
                )

        self.progress(int(100 / total))

        # ── Step 1: Clone repository ────────────────────────────
        self.step(1, steps[1])
        if (self.install_dir / ".git").exists():
            self.log(f"  ✔ Repository already exists at {self.install_dir}")
            # Pull latest
            rc, _, _ = self._exec(
                ["git", "pull", "--ff-only"], cwd=str(self.install_dir)
            )
            if rc != 0:
                self.log("  ⚠ git pull failed — continuing with existing code.")
        elif self.install_dir.exists() and any(self.install_dir.iterdir()):
            self.log(f"  ⚠ Directory {self.install_dir} exists and is not empty.")
            self.log("    Skipping clone — using existing files.")
        else:
            self.install_dir.mkdir(parents=True, exist_ok=True)
            rc, _, err = self._exec(
                [
                    "git",
                    "clone",
                    "--branch",
                    REPO_BRANCH,
                    "--single-branch",
                    REPO_URL,
                    str(self.install_dir),
                ],
                timeout=300,
            )
            if rc != 0:
                self.fail(f"Git clone failed:\n{err}")
                return
            self.log(f"  ✔ Cloned to {self.install_dir}")
        self.progress(int(100 * 2 / total))

        # ── Step 2: Virtual environment ─────────────────────────
        self.step(2, steps[2])
        venv_dir = self.install_dir / "venv"
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "Scripts" / "pip.exe"

        if venv_python.exists():
            self.log("  ✔ Virtual environment already exists.")
        else:
            rc, _, err = self._exec(["python", "-m", "venv", str(venv_dir)])
            if rc != 0:
                self.fail(f"Failed to create virtual environment:\n{err}")
                return
            self.log("  ✔ Virtual environment created.")
        self.progress(int(100 * 3 / total))

        # ── Step 3: Upgrade pip ─────────────────────────────────
        self.step(3, steps[3])
        rc, _, _ = self._exec(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], timeout=120
        )
        self.log(
            "  ✔ pip upgraded."
            if rc == 0
            else "  ⚠ pip upgrade had issues (continuing)."
        )
        self.progress(int(100 * 4 / total))

        # ── Step 4: Install requirements ────────────────────────
        self.step(4, steps[4])
        req_file = self.install_dir / "requirements.txt"
        if req_file.exists():
            rc, out, err = self._exec(
                [str(venv_pip), "install", "-r", str(req_file)],
                cwd=str(self.install_dir),
                timeout=600,
            )
            if rc != 0:
                self.fail(f"pip install failed:\n{err[-500:]}")
                return
            self.log("  ✔ Python packages installed.")
        else:
            self.log("  ⚠ requirements.txt not found — skipping.")
        self.progress(int(100 * 5 / total))

        # ── Step 5: PostgreSQL user ─────────────────────────────
        self.step(5, steps[5])
        pg_env = {**os.environ, "PGPASSWORD": self.pg_superpass}
        # Check if user already exists
        rc, out, _ = self._exec(
            [
                "psql",
                "-U",
                "postgres",
                "-tAc",
                f"SELECT 1 FROM pg_roles WHERE rolname='{DB_USER}';",
            ],
            env=pg_env,
        )
        if rc == 0 and "1" in out:
            self.log(f"  ✔ PostgreSQL user '{DB_USER}' already exists.")
        else:
            rc, _, err = self._exec(
                [
                    "psql",
                    "-U",
                    "postgres",
                    "-c",
                    f"CREATE USER {DB_USER} WITH CREATEDB PASSWORD '{DB_PASSWORD}';",
                ],
                env=pg_env,
            )
            if rc == 0:
                self.log(f"  ✔ PostgreSQL user '{DB_USER}' created.")
            else:
                self.log(f"  ⚠ Could not create user: {err}")
                self.log("    You may need to create it manually:")
                self.log(
                    f"    psql -U postgres -c \"CREATE USER {DB_USER} WITH CREATEDB PASSWORD '{DB_PASSWORD}';\""
                )
        self.progress(int(100 * 6 / total))

        # ── Step 6: Generate odoo.conf ──────────────────────────
        self.step(6, steps[6])
        conf_path = self.install_dir / "odoo.conf"
        if conf_path.exists():
            self.log("  ✔ odoo.conf already exists — keeping current configuration.")
        else:
            conf_content = f"""[options]
addons_path = addons,odoo/addons
admin_passwd = admin
db_host = localhost
db_name = {DB_NAME}
db_password = {DB_PASSWORD}
db_user = {DB_USER}
http_port = {HTTP_PORT}
with_demo = False
list_db = True
"""
            conf_path.write_text(conf_content, encoding="utf-8")
            self.log("  ✔ odoo.conf generated.")
        self.progress(int(100 * 7 / total))

        # ── Step 7: Initialise database ─────────────────────────
        self.step(7, steps[7])
        # Check if database already exists
        rc, out, _ = self._exec(
            [
                "psql",
                "-U",
                "postgres",
                "-tAc",
                f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}';",
            ],
            env=pg_env,
        )
        if rc == 0 and "1" in out:
            self.log(f"  ✔ Database '{DB_NAME}' already exists — skipping init.")
        else:
            self.log(
                f"  … Creating database '{DB_NAME}' and installing base module (this may take a few minutes)…"
            )
            rc, out, err = self._exec(
                [
                    str(venv_python),
                    "odoo-bin",
                    "-c",
                    str(conf_path),
                    "-d",
                    DB_NAME,
                    "-i",
                    "base",
                    "--stop-after-init",
                ],
                cwd=str(self.install_dir),
                timeout=600,
            )
            if rc != 0:
                self.log(f"  ⚠ Database init returned code {rc}.")
                self.log("    You can initialise manually later with:")
                self.log(f"    python run.py -d {DB_NAME} -i base")
            else:
                self.log(f"  ✔ Database '{DB_NAME}' initialised.")
        self.progress(int(100 * 8 / total))

        # ── Step 8: Create app shortcut ─────────────────────────
        self.step(8, steps[8])

        # -- VBS launcher: starts server hidden + opens PWA-like browser --
        launcher_path = self.install_dir / "launch_erpbizz.vbs"
        launcher_vbs = (
            'Set WshShell = CreateObject("WScript.Shell")\r\n'
            'Set fso = CreateObject("Scripting.FileSystemObject")\r\n'
            f'WshShell.CurrentDirectory = "{self.install_dir}"\r\n'
            'WshShell.Run "cmd /c ""venv\\Scripts\\activate.bat && python run.py""", 0, False\r\n'
            'WScript.Sleep 5000\r\n'
            '\r\n'
            'edgePath = WshShell.ExpandEnvironmentStrings("%ProgramFiles(x86)%") & "\\Microsoft\\Edge\\Application\\msedge.exe"\r\n'
            'If Not fso.FileExists(edgePath) Then\r\n'
            '    edgePath = WshShell.ExpandEnvironmentStrings("%ProgramFiles%") & "\\Microsoft\\Edge\\Application\\msedge.exe"\r\n'
            'End If\r\n'
            'chromePath = WshShell.ExpandEnvironmentStrings("%ProgramFiles%") & "\\Google\\Chrome\\Application\\chrome.exe"\r\n'
            'If Not fso.FileExists(chromePath) Then\r\n'
            '    chromePath = WshShell.ExpandEnvironmentStrings("%ProgramFiles(x86)%") & "\\Google\\Chrome\\Application\\chrome.exe"\r\n'
            'End If\r\n'
            '\r\n'
            'If fso.FileExists(edgePath) Then\r\n'
            f'    WshShell.Run """" & edgePath & """ --app=http://localhost:{HTTP_PORT}", 1, False\r\n'
            'ElseIf fso.FileExists(chromePath) Then\r\n'
            f'    WshShell.Run """" & chromePath & """ --app=http://localhost:{HTTP_PORT}", 1, False\r\n'
            'Else\r\n'
            f'    WshShell.Run "cmd /c start http://localhost:{HTTP_PORT}", 0, False\r\n'
            'End If\r\n'
        )
        launcher_path.write_text(launcher_vbs, encoding="utf-8")
        self.log(f"  ✔ Created launcher: {launcher_path}")

        # -- Server-only VBS for Startup folder (auto-start on login) --
        server_vbs_path = self.install_dir / "start_server.vbs"
        server_vbs = (
            'Set WshShell = CreateObject("WScript.Shell")\r\n'
            f'WshShell.CurrentDirectory = "{self.install_dir}"\r\n'
            'WshShell.Run "cmd /c ""venv\\Scripts\\activate.bat && python run.py""", 0, False\r\n'
        )
        server_vbs_path.write_text(server_vbs, encoding="utf-8")
        self.log(f"  ✔ Created silent server starter: {server_vbs_path}")

        # -- Desktop shortcut (.lnk) pointing to the launcher --
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if desktop.exists():
            lnk_path = desktop / f"{APP_NAME}.lnk"
            # Check for an .ico; if only .png exists, skip custom icon
            ico_path = self.install_dir / "addons" / "web" / "static" / "img" / "favicon.ico"
            ps_parts = [
                '$ws = New-Object -ComObject WScript.Shell',
                f'$s = $ws.CreateShortcut(\"{lnk_path}\")',
                '$s.TargetPath = \"wscript.exe\"',
                f'$s.Arguments = \"\"\"{launcher_path}\"\"\"',
                f'$s.WorkingDirectory = \"{self.install_dir}\"',
                f'$s.Description = \"Launch {APP_NAME}\"',
            ]
            if ico_path.exists():
                ps_parts.append(f'$s.IconLocation = \"{ico_path},0\"')
            ps_parts.append('$s.Save()')
            ps_script = '; '.join(ps_parts)
            rc, _, err = self._exec(
                ["powershell", "-NoProfile", "-Command", ps_script]
            )
            if rc == 0:
                self.log(f"  ✔ Desktop shortcut created: {lnk_path}")
            else:
                self.log(f"  ⚠ Could not create desktop shortcut: {err}")
        else:
            self.log("  ⚠ Desktop folder not found — skipping shortcut.")

        # -- Copy server starter to Windows Startup folder --
        startup_dir = (
            Path(os.environ.get("APPDATA", ""))
            / r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        if startup_dir.exists():
            shortcut_dest = startup_dir / "start_erpbizz_server.vbs"
            if not shortcut_dest.exists():
                try:
                    shutil.copy2(str(server_vbs_path), str(shortcut_dest))
                    self.log("  ✔ Added server auto-start to Windows Startup folder.")
                except OSError:
                    self.log(
                        "  ⚠ Could not copy to Startup folder (permission denied)."
                    )
        self.progress(int(100 * 9 / total))

        # ── Step 9: Done ────────────────────────────────────────
        self.step(9, steps[9])
        self.log("")
        self.log("━" * 50)
        self.log(f"  ✔ {APP_NAME} installed at {self.install_dir}")
        self.log(f"  ✔ Desktop shortcut: {APP_NAME} (double-click to launch)")
        self.log(f"  ✔ Server auto-starts on login")
        self.log("━" * 50)
        self.progress(100)
        self._on_done(
            True,
            f"Installation complete!\n\nDouble-click the {APP_NAME} shortcut on your Desktop to launch.",
        )


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------


class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Installer")
        self.configure(bg=BG)
        self.resizable(False, False)

        # Window size & centering
        w, h = 680, 780
        sx = self.winfo_screenwidth() // 2 - w // 2
        sy = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{sx}+{sy}")

        # Try to set window icon
        self._set_icon()

        # Fonts
        self._f_title = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        self._f_sub = tkfont.Font(family="Segoe UI", size=10)
        self._f_body = tkfont.Font(family="Segoe UI", size=9)
        self._f_log = tkfont.Font(family="Consolas", size=8)
        self._f_btn = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self._f_small = tkfont.Font(family="Segoe UI", size=8)

        # Style ttk widgets
        self._style = ttk.Style(self)
        self._style.theme_use("clam")
        self._style.configure(
            "TProgressbar", troughcolor=BORDER, background=ACCENT, thickness=8
        )
        self._style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            padding=(20, 8),
        )
        self._style.map(
            "Accent.TButton",
            background=[("active", ACCENT_HOVER), ("disabled", SUBTLE)],
        )

        self._build_ui()
        self._check_deps()

    # ── icon ──

    def _set_icon(self):
        """Set window icon from the logo file."""
        logo_candidates = [
            Path(__file__).parent / LOGO_RELATIVE,
            Path(__file__).parent / "addons" / "web" / "static" / "img" / "favicon.png",
        ]
        for lp in logo_candidates:
            if lp.exists():
                try:
                    img = tk.PhotoImage(file=str(lp))
                    self.iconphoto(True, img)
                    self._icon_ref = img  # prevent GC
                except Exception:
                    pass
                break

    # ── UI build ──

    def _build_ui(self):
        # Header area
        header = tk.Frame(self, bg=BG, pady=16)
        header.pack(fill="x")

        # Logo
        self._logo_label = None
        logo_candidates = [
            Path(__file__).parent / LOGO_RELATIVE,
            Path(__file__).parent / "addons" / "web" / "static" / "img" / "favicon.png",
        ]
        for lp in logo_candidates:
            if lp.exists():
                try:
                    from PIL import Image, ImageTk

                    pil_img = Image.open(str(lp))
                    pil_img = pil_img.resize((64, 64), Image.LANCZOS)
                    self._logo_tk = ImageTk.PhotoImage(pil_img)
                    self._logo_label = tk.Label(header, image=self._logo_tk, bg=BG)
                    self._logo_label.pack()
                except ImportError:
                    # Fallback: try raw PhotoImage (works for simple PNGs)
                    try:
                        raw = tk.PhotoImage(file=str(lp)).subsample(8, 8)
                        self._logo_tk = raw
                        self._logo_label = tk.Label(header, image=raw, bg=BG)
                        self._logo_label.pack()
                    except Exception:
                        pass
                break

        # tk.Label(header, text=APP_NAME, font=self._f_title, bg=BG, fg=FG).pack(
        #     pady=(4, 0)
        # )
        tk.Label(
            header, text="Setup Wizard for Windows", font=self._f_sub, bg=BG, fg=SUBTLE
        ).pack()

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24)

        # Dependency status frame
        dep_outer = tk.Frame(self, bg=BG, pady=12, padx=32)
        dep_outer.pack(fill="x")
        tk.Label(
            dep_outer,
            text="Dependency Check",
            font=self._f_sub,
            bg=BG,
            fg=FG,
            anchor="w",
        ).pack(fill="x")

        self._dep_frame = tk.Frame(dep_outer, bg=BG, pady=4)
        self._dep_frame.pack(fill="x")

        self._dep_labels = {}
        for dep in ("Git", "Python", "PostgreSQL", "wkhtmltopdf"):
            row = tk.Frame(self._dep_frame, bg=BG, pady=2)
            row.pack(fill="x")
            status_lbl = tk.Label(
                row,
                text="  ●",
                font=self._f_body,
                bg=BG,
                fg=SUBTLE,
                width=3,
                anchor="w",
            )
            status_lbl.pack(side="left")
            name_lbl = tk.Label(
                row, text=dep, font=self._f_body, bg=BG, fg=FG, anchor="w"
            )
            name_lbl.pack(side="left")
            ver_lbl = tk.Label(
                row, text="checking…", font=self._f_small, bg=BG, fg=SUBTLE, anchor="e"
            )
            ver_lbl.pack(side="right")
            self._dep_labels[dep] = (status_lbl, ver_lbl)

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24)

        # Install directory (fixed)
        dir_frame = tk.Frame(self, bg=BG, pady=12, padx=32)
        dir_frame.pack(fill="x")
        tk.Label(
            dir_frame,
            text="Install Directory",
            font=self._f_sub,
            bg=BG,
            fg=FG,
            anchor="w",
        ).pack(fill="x")

        self._dir_var = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        tk.Label(
            dir_frame,
            textvariable=self._dir_var,
            font=self._f_body,
            bg="#FAFAFA",
            fg=FG,
            relief="solid",
            bd=1,
            anchor="w",
            padx=6,
            pady=4,
        ).pack(fill="x", pady=(4, 0))

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24)

        # PostgreSQL superuser password
        pg_frame = tk.Frame(self, bg=BG, pady=8, padx=32)
        pg_frame.pack(fill="x")
        tk.Label(
            pg_frame,
            text="PostgreSQL Superuser Password",
            font=self._f_sub,
            bg=BG,
            fg=FG,
            anchor="w",
        ).pack(fill="x")
        self._pg_pass_var = tk.StringVar(value="odoo")
        pg_entry = tk.Entry(
            pg_frame,
            textvariable=self._pg_pass_var,
            font=self._f_body,
            bg="#FAFAFA",
            fg=FG,
            relief="solid",
            bd=1,
            show="●",
        )
        pg_entry.pack(fill="x", pady=(4, 0))
        tk.Label(
            pg_frame,
            text="Password for the 'postgres' superuser (set during PostgreSQL install)",
            font=self._f_small,
            bg=BG,
            fg=SUBTLE,
            anchor="w",
        ).pack(fill="x")

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24)

        # Current step label
        step_frame = tk.Frame(self, bg=BG, pady=8, padx=32)
        step_frame.pack(fill="x")
        self._step_var = tk.StringVar(value="Ready to install")
        tk.Label(
            step_frame,
            textvariable=self._step_var,
            font=self._f_sub,
            bg=BG,
            fg=ACCENT,
            anchor="w",
        ).pack(fill="x")

        # Progress bar
        prog_frame = tk.Frame(self, bg=BG, padx=32)
        prog_frame.pack(fill="x")
        self._progress_var = tk.IntVar(value=0)
        self._pbar = ttk.Progressbar(
            prog_frame,
            maximum=100,
            variable=self._progress_var,
            style="TProgressbar",
            length=600,
        )
        self._pbar.pack(fill="x")

        self._progress_pct = tk.Label(
            prog_frame, text="0 %", font=self._f_small, bg=BG, fg=SUBTLE, anchor="e"
        )
        self._progress_pct.pack(fill="x")

        # Bottom buttons (pack BEFORE log so they are always visible)
        btn_frame = tk.Frame(self, bg=BG, pady=12, padx=32)
        btn_frame.pack(side="bottom", fill="x")

        # Log area
        log_frame = tk.Frame(self, bg=BG, padx=32, pady=8)
        log_frame.pack(fill="both", expand=True)
        tk.Label(
            log_frame, text="Log", font=self._f_small, bg=BG, fg=SUBTLE, anchor="w"
        ).pack(fill="x")

        log_container = tk.Frame(log_frame, bg=BORDER, bd=1, relief="solid")
        log_container.pack(fill="both", expand=True)

        self._log_text = tk.Text(
            log_container,
            font=self._f_log,
            bg="#FAFAFA",
            fg=FG,
            relief="flat",
            wrap="word",
            state="disabled",
            highlightthickness=0,
            padx=8,
            pady=6,
        )
        scrollbar = tk.Scrollbar(log_container, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._log_text.pack(side="left", fill="both", expand=True)

        self._install_btn = tk.Button(
            btn_frame,
            text="  Install  ",
            font=self._f_btn,
            bg=ACCENT,
            fg="#FFFFFF",
            activebackground=ACCENT_HOVER,
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=24,
            pady=6,
            command=self._start_install,
        )
        self._install_btn.pack(side="right")

        self._close_btn = tk.Button(
            btn_frame,
            text="  Close  ",
            font=self._f_btn,
            bg="#F0F0F0",
            fg=FG,
            activebackground="#E0E0E0",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self.destroy,
        )
        self._close_btn.pack(side="right", padx=(0, 8))

    # ── actions ──

    def _check_deps(self):
        """Run dependency checks in background thread, update labels."""

        def _check():
            results = {}

            # Git
            ok, ver, _ = check_git()
            results["Git"] = ok
            self.after(0, self._set_dep, "Git", ok, ver)

            # Python
            ok, ver, path = check_python()
            results["Python"] = ok
            self.after(0, self._set_dep, "Python", ok, ver)

            # PostgreSQL
            ok, ver, path, _ = check_postgresql()
            results["PostgreSQL"] = ok
            self.after(0, self._set_dep, "PostgreSQL", ok, ver)

            # wkhtmltopdf
            ok, ver, _ = check_wkhtmltopdf()
            results["wkhtmltopdf"] = ok
            self.after(0, self._set_dep, "wkhtmltopdf", ok, ver, True)  # optional

            # Update status message based on results
            all_found = all(results.values())
            required_found = all(results[d] for d in ("Git", "Python", "PostgreSQL"))
            if all_found:
                self.after(0, self._step_var.set, "All dependencies found — click Install to set up ErpBizz")
            elif required_found:
                self.after(0, self._step_var.set, "Required dependencies found — click Install to continue")
            else:
                self.after(0, self._step_var.set, "Missing dependencies will be installed automatically — click Install")

        threading.Thread(target=_check, daemon=True).start()

    def _set_dep(self, name, found, version=None, optional_ok=True):
        status_lbl, ver_lbl = self._dep_labels[name]
        if found:
            status_lbl.config(text="  ✔", fg=SUCCESS)
            ver_lbl.config(text=version or "found", fg=SUCCESS)
        elif optional_ok and name == "wkhtmltopdf":
            status_lbl.config(text="  ○", fg="#F39C12")
            ver_lbl.config(text="not found (optional)", fg="#F39C12")
        else:
            status_lbl.config(text="  ✘", fg=ERROR)
            ver_lbl.config(text="not found", fg=ERROR)

    def _log(self, msg):
        self._log_text.config(state="normal")
        self._log_text.insert("end", msg + "\n")
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _set_step(self, idx, label):
        self._step_var.set(f"Step {idx + 1}: {label}")

    def _set_progress(self, val):
        self._progress_var.set(val)
        self._progress_pct.config(text=f"{val} %")

    def _start_install(self):
        install_dir = self._dir_var.get().strip()
        if not install_dir:
            messagebox.showwarning(
                "Missing directory", "Please choose an install directory."
            )
            return

        # Disable button
        self._install_btn.config(state="disabled", bg=SUBTLE)

        worker = InstallerWorker(
            install_dir=install_dir,
            pg_superpass=self._pg_pass_var.get(),
            on_step=lambda i, l: self.after(0, self._set_step, i, l),
            on_progress=lambda v: self.after(0, self._set_progress, v),
            on_log=lambda m: self.after(0, self._log, m),
            on_done=lambda ok, m: self.after(0, self._on_done, ok, m),
        )
        threading.Thread(target=worker.run, daemon=True).start()

    def _on_done(self, success, message):
        if success:
            self._step_var.set("✔ Installation Complete")
            self._install_btn.config(
                text="  Done  ", state="normal", bg=SUCCESS, command=self.destroy
            )
            messagebox.showinfo("Success", message)
        else:
            self._step_var.set("✘ Installation Failed")
            self._install_btn.config(
                text="  Retry  ", state="normal", bg=ACCENT, command=self._start_install
            )
            messagebox.showerror("Error", message)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
