@echo off
echo Starting Voice Banking Application...
echo.
echo Activating conda environment...
call conda activate voice-banking || (
    echo Failed to activate conda environment.
    echo Please ensure Miniconda is installed and the environment is created with:
    echo conda env create -f environment.yml
    exit /b 1
)
echo.
echo Starting Flask server...
python app.py
