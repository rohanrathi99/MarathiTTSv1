@echo off
setlocal
cd /d "%~dp0.."

set PYTHONPATH=%CD%\piper_train\src\python
set DATASET_DIR=%CD%\training_filtered

echo ============================================
echo   MarathiTTSv1 - Marathi TTS Training
echo ============================================
echo.

:: Check if dataset exists
if not exist "%CD%\data\ljspeech_filtered\wavs" (
    echo ERROR: Dataset not found at data\ljspeech_filtered\
    echo Run "python scripts\format_data.py" first.
    exit /b 1
)

:: 1. Run Preprocessing
:: Using --phoneme-type text for Devanagari character-level training (Windows compatible)
:: NOTE: This mode is NOT compatible with fine-tuning from an English phoneme checkpoint.
::       We train from scratch instead.
echo [Step 1/2] Running preprocessing...
python -m piper_train.preprocess ^
    --language mr ^
    --input-dir "%CD%\data\ljspeech_filtered" ^
    --output-dir "%DATASET_DIR%" ^
    --dataset-format ljspeech ^
    --single-speaker ^
    --sample-rate 22050 ^
    --phoneme-type text

if %ERRORLEVEL% neq 0 (
    echo ERROR: Preprocessing failed.
    exit /b 1
)

:: 2. Start Training (from scratch — text mode is incompatible with phoneme checkpoints)
echo.
echo [Step 2/2] Starting MarathiTTSv1 Training (from scratch)...
echo   Dataset:    %DATASET_DIR%
echo   PYTHONPATH: %PYTHONPATH%
echo   Mode:       Training from scratch (text-mode, Windows compatible)
echo.
echo   NOTE: For faster training via fine-tuning, use scripts/train.sh on Linux
echo         where espeak-ng phonemes and checkpoint fine-tuning are supported.
echo.

python -m piper_train ^
    --dataset-dir "%DATASET_DIR%" ^
    --accelerator auto ^
    --devices auto ^
    --batch-size 32 ^
    --validation-split 0.05 ^
    --num-test-examples 5 ^
    --max_epochs 2000 ^
    --checkpoint-epochs 50 ^
    --precision 32 ^
    %*

echo.
echo Training complete!
echo Checkpoints are in: %DATASET_DIR%\lightning_logs\

endlocal
