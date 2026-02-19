@echo off
:: ============================================================
::  MarathiTTSv1 - Windows Piper Setup Script
::  Equivalent of scripts/setup_piper.sh for Windows
::
::  Run ONCE from the project root (after creating venv):
::    scripts\setup_piper.bat
::
::  What this does:
::    1. Creates venv (if not present)
::    2. Installs all Python dependencies
::    3. Clones rhasspy/piper and extracts training source
::    4. Installs piper_train in editable mode
::    5. Attempts to build monotonic_align C extension
::       (falls back to Numba JIT if MSVC is unavailable)
::    6. Runs fix_environment.bat to ensure correct package versions
::    7. Self-tests the installation
:: ============================================================

setlocal
cd /d "%~dp0.."

echo ============================================================
echo   MarathiTTSv1 - Windows Setup
echo ============================================================
echo.

:: ── Step 1: Verify Python ────────────────────────────────────────────────────
echo [Step 1/6] Checking Python...
python --version 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH.
    echo Download Python 3.10-3.12 from https://python.org
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   Python %PYVER% found.

:: Warn if Python 3.12+ (pkg_resources issue — fixed by fix_environment.bat)
echo %PYVER% | findstr /r "^3\.12\." >nul
if %ERRORLEVEL% equ 0 (
    echo   NOTE: Python 3.12 detected. fix_environment.bat will install
    echo         setuptools to restore pkg_resources.
)
echo.

:: ── Step 2: Create virtual environment ───────────────────────────────────────
echo [Step 2/6] Setting up virtual environment...
if exist "venv\Scripts\python.exe" (
    echo   venv already exists. Skipping creation.
) else (
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
    echo   venv created.
)

echo   Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
echo.

:: ── Step 3: Install PyTorch ──────────────────────────────────────────────────
echo [Step 3/6] Installing PyTorch (CUDA 12.4 for RTX 30/40 series)...
echo.
echo   If your GPU is different, edit this script and change the --index-url.
echo   Options:
echo     CPU only:   pip install torch torchaudio
echo     CUDA 11.8:  pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu118
echo     CUDA 12.1:  pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
echo     CUDA 12.4:  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
echo.

venv\Scripts\python.exe -c "import torch" 2>nul
if %ERRORLEVEL% equ 0 (
    echo   PyTorch already installed. Skipping.
) else (
    venv\Scripts\pip.exe install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
    if %ERRORLEVEL% neq 0 (
        echo WARNING: CUDA 12.4 PyTorch install failed. Trying CPU-only fallback...
        venv\Scripts\pip.exe install torch torchaudio
    )
)
echo.

:: ── Step 4: Install project dependencies ─────────────────────────────────────
echo [Step 4/6] Installing project dependencies...
venv\Scripts\pip.exe install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Dependency installation failed. Check requirements.txt.
    exit /b 1
)
echo.

:: ── Step 5: Clone and install piper_train ────────────────────────────────────
echo [Step 5/6] Setting up piper_train...

if exist "piper_train\src\python\piper_train\__main__.py" (
    echo   piper_train already present. Skipping clone.
    goto :install_piper
)

:: Check for git
git --version 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: git not found. Install Git from https://git-scm.com/
    exit /b 1
)

echo   Cloning rhasspy/piper...
git clone --depth 1 https://github.com/rhasspy/piper.git piper_train_temp
if %ERRORLEVEL% neq 0 (
    echo ERROR: git clone failed. Check internet connection.
    exit /b 1
)

mkdir piper_train 2>nul
xcopy /E /I /Q piper_train_temp\src piper_train\src
rmdir /S /Q piper_train_temp
echo   Piper source extracted to piper_train\src\
echo.

:install_piper
echo   Installing piper_train in editable mode...
venv\Scripts\pip.exe install -e "piper_train\src\python"
if %ERRORLEVEL% neq 0 (
    echo ERROR: piper_train install failed.
    exit /b 1
)
echo.

:: ── Step 6: Build monotonic_align extension ───────────────────────────────────
echo [Step 6/6] Building monotonic_align C extension...
echo   (requires Microsoft Visual C++ Build Tools)

if not exist "piper_train\src\python\piper_train\vits\monotonic_align\setup.py" (
    echo   WARNING: monotonic_align setup.py not found. Skipping build.
    goto :fix_env
)

venv\Scripts\python.exe piper_train\src\python\piper_train\vits\monotonic_align\setup.py ^
    build_ext --inplace ^
    --build-lib piper_train\src\python\piper_train\vits\monotonic_align 2>nul

if %ERRORLEVEL% equ 0 (
    echo   C extension built successfully.
) else (
    echo   C extension build failed (MSVC may not be installed).
    echo   Attempting to install Numba JIT fallback...
    venv\Scripts\pip.exe install numba
    if %ERRORLEVEL% equ 0 (
        echo   Numba installed. The JIT implementation will be used automatically.
    ) else (
        echo   WARNING: Both C build and Numba fallback failed.
        echo   Install Microsoft C++ Build Tools from:
        echo     https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo   Then re-run this script.
    )
)
echo.

:: ── Run fix_environment.bat ───────────────────────────────────────────────────
:fix_env
echo Running environment fix and verification...
echo.
call scripts\fix_environment.bat
if %ERRORLEVEL% neq 0 (
    echo.
    echo Setup completed with warnings. See FAIL lines above.
    exit /b 1
)

echo.
echo ============================================================
echo   Setup complete!
echo.
echo   Next steps:
echo     1. Download dataset:  python scripts\download_dataset.py
echo     2. Prepare data:      python scripts\format_data.py
echo     3. Train:             scripts\train.bat
echo ============================================================

endlocal
