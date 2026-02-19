@echo off
:: ============================================================
::  MarathiTTSv1 - Marathi TTS Training (Windows)
::  v2 — includes pre-flight environment checks
::
::  Usage:
::    scripts\train.bat
::    scripts\train.bat --batch-size 4
::    scripts\train.bat --max_epochs 500
::
::  If any check fails, run:  scripts\fix_environment.bat
:: ============================================================

setlocal
cd /d "%~dp0.."

set PYTHONPATH=%CD%\piper_train\src\python
set DATASET_DIR=%CD%\training_filtered

echo ============================================
echo   MarathiTTSv1 - Marathi TTS Training
echo ============================================
echo.

:: ── Pre-flight checks ────────────────────────────────────────────────────────

:: 1. Virtual environment
if not exist "%CD%\venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at .\venv\
    echo        Create it first:  python -m venv venv
    echo        Then run:         scripts\fix_environment.bat
    exit /b 1
)

:: 2. pkg_resources / setuptools  (Python 3.12+ venvs omit this by default)
echo [Check 1/3] Verifying pkg_resources (setuptools)...
venv\Scripts\python.exe -c "import pkg_resources" 2>nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo *** ENVIRONMENT ERROR: pkg_resources not found ***
    echo.
    echo   Root cause: Python 3.12 no longer auto-installs setuptools into
    echo   virtual environments. pkg_resources lives inside setuptools and is
    echo   required by pytorch-lightning ^< 2.3.
    echo.
    echo   Fix: Run this command, then re-run train.bat:
    echo.
    echo       scripts\fix_environment.bat
    echo.
    echo   Or manually:
    echo       venv\Scripts\pip install setuptools
    echo       venv\Scripts\pip install "pytorch-lightning>=2.4.0,<3.0.0"
    echo.
    exit /b 1
)
echo   OK

:: 3. pytorch_lightning
echo [Check 2/3] Verifying pytorch_lightning...
venv\Scripts\python.exe -c "import pytorch_lightning" 2>nul
if %ERRORLEVEL% neq 0 (
    echo.
    echo *** ENVIRONMENT ERROR: pytorch_lightning fails to import ***
    echo   Run: scripts\fix_environment.bat
    echo.
    exit /b 1
)
echo   OK

:: 4. Dataset
echo [Check 3/3] Verifying dataset...
if not exist "%CD%\data\ljspeech_filtered\wavs" (
    echo.
    echo *** DATA ERROR: Dataset not found at data\ljspeech_filtered\ ***
    echo   Run: python scripts\format_data.py
    echo.
    exit /b 1
)
echo   OK

echo.
echo   All checks passed. Starting pipeline...
echo.

:: ── Step 1: Preprocessing ────────────────────────────────────────────────────
::
::  --phoneme-type text  uses raw Devanagari characters as input tokens.
::  This is the only option that works on Windows without espeak-ng.
::  It is NOT compatible with fine-tuning from the English Lessac checkpoint.
::  Training always starts from scratch in this mode.
::
echo [Step 1/2] Running preprocessing...
venv\Scripts\python.exe -u -m piper_train.preprocess ^
    --language mr ^
    --input-dir "%CD%\data\ljspeech_filtered" ^
    --output-dir "%DATASET_DIR%" ^
    --dataset-format ljspeech ^
    --single-speaker ^
    --sample-rate 22050 ^
    --phoneme-type text ^
    --max-workers 1 ^
    --debug

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Preprocessing failed ^(exit code %ERRORLEVEL%^).
    echo        Check the log above for details.
    exit /b 1
)

:: ── Step 2: Training ─────────────────────────────────────────────────────────
echo.
echo [Step 2/2] Starting MarathiTTSv1 Training (from scratch)...
echo   Dataset:    %DATASET_DIR%
echo   PYTHONPATH: %PYTHONPATH%
echo   Mode:       Training from scratch (text-mode, Windows compatible)
echo.
echo   NOTE: For faster training via fine-tuning from the English checkpoint,
echo         use scripts/train.sh on Linux or Google Colab.
echo.

venv\Scripts\python.exe -m piper_train ^
    --dataset-dir "%DATASET_DIR%" ^
    --accelerator auto ^
    --devices auto ^
    --batch-size 8 ^
    --validation-split 0.05 ^
    --num-test-examples 5 ^
    --max_epochs 2000 ^
    --check_val_every_n_epoch 10 ^
    --checkpoint-epochs 50 ^
    --precision 32 ^
    %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Training failed ^(exit code %ERRORLEVEL%^).
    echo        Check the output above for details.
    exit /b 1
)

echo.
echo ============================================
echo   Training complete!
echo   Checkpoints: %DATASET_DIR%\lightning_logs\
echo ============================================

endlocal
