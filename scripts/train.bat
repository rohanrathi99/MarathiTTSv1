@echo off
setlocal
cd /d "%~dp0.."

set PYTHONPATH=%CD%\piper_train\src\python
set DATASET_DIR=%CD%\training

echo Starting AiAntargyanV2 Training...
echo Dataset: %DATASET_DIR%
echo Python Path: %PYTHONPATH%

python -m piper_train ^
    --dataset-dir "%DATASET_DIR%" ^
    --accelerator auto ^
    --devices 1 ^
    --batch-size 32 ^
    --validation-split 0.05 ^
    --num-test-examples 5 ^
    --max_epochs 5000 ^
    --quality medium ^
    --precision 32 ^
    %*

endlocal
