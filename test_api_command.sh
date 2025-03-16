#!/bin/bash

# Create test directories
mkdir -p Frontend/public/uploads
mkdir -p Frontend/public/results/test

# Copy a sample image
cp SampleDrawings/Screenshot.png Frontend/public/uploads/test.png

# Get the absolute path to the current directory
ROOT_DIR=$(pwd)

# Build the command
PYTHON_SCRIPT="$ROOT_DIR/src/perimeter_wall_extractor.py"
UPLOAD_PATH="$ROOT_DIR/Frontend/public/uploads/test.png"
RESULTS_DIR="$ROOT_DIR/Frontend/public/results/test"

COMMAND="python \"$PYTHON_SCRIPT\" \"$UPLOAD_PATH\" --overall_width \"38'-0\" --output_dir \"$RESULTS_DIR\""

echo "Executing command:"
echo $COMMAND

# Execute the command
eval $COMMAND

echo "Check the results in $RESULTS_DIR"
