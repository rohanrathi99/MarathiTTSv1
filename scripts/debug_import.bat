
@echo off
setlocal
cd /d "%~dp0.."
set PYTHONPATH=%CD%\piper_train\src\python
echo PYTHONPATH is %PYTHONPATH%
venv\Scripts\python.exe -c "import sys; print(sys.path); import piper_phonemize; print(piper_phonemize)"
