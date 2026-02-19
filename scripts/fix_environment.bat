@echo off
:: ============================================================
::  MarathiTTSv1 - Environment Fix Script
::  -------------------------------------------------------
::  Run this ONCE from the project root to resolve:
::    ModuleNotFoundError: No module named 'pkg_resources'
::
::  Usage:
::    scripts\fix_environment.bat
::
::  What this does:
::    1. Installs setuptools  (restores pkg_resources for Python 3.12)
::    2. Upgrades pytorch-lightning to >=2.4.0  (lightning_fabric 2.3+
::       no longer requires pkg_resources at all — permanent fix)
::    3. Re-installs piper_train in editable mode
::    4. Runs a self-test to confirm all imports succeed
:: ============================================================

setlocal
cd /d "%~dp0.."

echo ============================================================
echo   MarathiTTSv1 - Environment Fix
echo   Resolves: ModuleNotFoundError: No module named 'pkg_resources'
echo ============================================================
echo.

:: ── Locate venv ───────────────────────────────────────────────────────────────
if exist "%CD%\venv\Scripts\python.exe" (
    set PYTHON=%CD%\venv\Scripts\python.exe
    set PIP=%CD%\venv\Scripts\pip.exe
) else (
    echo ERROR: Virtual environment not found at .\venv\
    echo        Create it first:  python -m venv venv
    exit /b 1
)

echo Using Python: %PYTHON%
echo.

:: ── Fix 1: setuptools ─────────────────────────────────────────────────────────
echo [Fix 1/3] Installing / upgrading setuptools...
echo           (provides pkg_resources, absent in Python 3.12 venvs by default)
"%PIP%" install --upgrade setuptools
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install setuptools.
    exit /b 1
)
echo   Done.
echo.

:: ── Fix 2: pytorch-lightning >=2.4.0 ─────────────────────────────────────────
::
::  WHY THIS VERSION:
::   - lightning_fabric ^< 2.3.0 imports pkg_resources in its __init__.py
::   - lightning_fabric ^>= 2.3.0 removed that dependency entirely
::   - piper_train_patches/requirements.txt already targets PL ^>= 2.4.0
::   - Upgrading is the correct permanent fix (setuptools alone is a workaround)
::
echo [Fix 2/3] Upgrading pytorch-lightning to ^>=2.4.0 ^(permanent fix^)...
"%PIP%" install "pytorch-lightning>=2.4.0,<3.0.0" "lightning>=2.4.0,<3.0.0"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to upgrade pytorch-lightning.
    exit /b 1
)
echo   Done.
echo.

:: ── Fix 3: Re-install piper_train ────────────────────────────────────────────
echo [Fix 3/3] Re-installing piper_train in editable mode...
if not exist "%CD%\piper_train\src\python" (
    echo   WARNING: piper_train\src\python not found.
    echo   Run setup: see SETUP_GUIDE.md or clone piper manually.
    goto :selftest
)
"%PIP%" install -e "%CD%\piper_train\src\python"
if %ERRORLEVEL% neq 0 (
    echo   WARNING: piper_train re-install had errors (may already be installed).
)
echo   Done.
echo.

:: ── Self-test ─────────────────────────────────────────────────────────────────
:selftest
echo ── Self-test ────────────────────────────────────────────────────────────────
echo.

set PASS=1

:: pkg_resources
"%PYTHON%" -c "import pkg_resources; print('  [OK] pkg_resources', pkg_resources.__version__)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [FAIL] pkg_resources still missing
    echo          Try: venv\Scripts\pip install setuptools --force-reinstall
    set PASS=0
)

:: pytorch_lightning
"%PYTHON%" -c "import pytorch_lightning as pl; print('  [OK] pytorch_lightning', pl.__version__)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [FAIL] pytorch_lightning fails to import
    set PASS=0
)

:: lightning_fabric
"%PYTHON%" -c "import lightning_fabric; print('  [OK] lightning_fabric', lightning_fabric.__version__)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [FAIL] lightning_fabric fails to import
    set PASS=0
)

:: torch
"%PYTHON%" -c "import torch; print('  [OK] torch', torch.__version__, '| CUDA:', torch.cuda.is_available())" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [FAIL] torch not installed
    echo          Run: venv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
    set PASS=0
)

:: piper_train
set PYTHONPATH=%CD%\piper_train\src\python
"%PYTHON%" -c "import piper_train; print('  [OK] piper_train at', piper_train.__file__)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [FAIL] piper_train fails to import
    echo          Ensure piper_train\src\python exists (see SETUP_GUIDE.md)
    set PASS=0
)

echo.
if "%PASS%"=="1" (
    echo ============================================================
    echo   All checks passed!
    echo   You can now run:  scripts\train.bat
    echo ============================================================
) else (
    echo ============================================================
    echo   Some checks FAILED. Review the messages above.
    echo ============================================================
    exit /b 1
)

endlocal
