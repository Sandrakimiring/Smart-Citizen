@echo off
echo ================================================================================
echo Rebuilding Vector Store with Enhanced Article Detection
echo ================================================================================
echo.

REM Activate conda environment
call conda activate smartcitizen

REM Run rebuild script
python rebuild_vectorstore.py

pause
