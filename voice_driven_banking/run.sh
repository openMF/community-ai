#!/bin/bash

echo "Starting Voice Banking Application..."
echo ""
echo "Activating conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate voice-banking || {
    echo "Failed to activate conda environment."
    echo "Please ensure Miniconda is installed and the environment is created with:"
    echo "conda env create -f environment.yml"
    exit 1
}
echo ""
echo "Starting Flask server..."
python app.py
