#!/bin/bash

echo "Starting Unified Community AI Backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload