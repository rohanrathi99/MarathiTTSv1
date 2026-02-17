@echo off
setlocal
cd /d "%~dp0.."

set PYTHONPATH=%CD%\piper_train\src\python
set DATASET_DIR=%CD%\training_filtered

@echo:: 1. Run Preprocessing (Optional if already done)
:: We use --phoneme-type text for Devanagari character-level training (Windows compatible)
echo Running preprocessing...
python -m piper_train.preprocess ^
    --language mr ^
    --input-dir "%CD%\data\ljspeech_filtered" ^
    --output-dir "%DATASET_DIR%" ^
    --dataset-format ljspeech ^
    --single-speaker ^
    --sample-rate 22050 ^
    --phoneme-type text

:: 2. Start Training
echo Starting AiAntargyanV2 Training...
echo Dataset: %DATASET_DIR%
echo Python Path: %PYTHONPATH%

python -m piper_train ^
    --dataset-dir "%DATASET_DIR%" ^
    --accelerator auto ^
    --devices auto ^
    --batch-size 32 ^
    --validation-split 0.05 ^
    --num-test-examples 5 ^
    --max_epochs 5000 ^
    --resume_from_checkpoint "%CD%\checkpoints\en_US-lessac-medium.ckpt" ^
    --checkpoint-epochs 50 ^
    --precision 32 ^
    %*

endlocal
