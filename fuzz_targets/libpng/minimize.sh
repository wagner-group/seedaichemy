#!/bin/bash
set -e

echo "Starting minimization procedure..."

# Validate arguments
echo "Validating arguments..."
if [[ $# != 3 ]]; then
    echo "Incorrect number of arguments: $#"
    exit 1
fi

# Assign arguments
CORPUS_DIR=$1
MINIMIZED_DIR=$2
FUZZ_BIN=$3

# Additional variables
CORPUS_SIZE=$(ls $CORPUS_DIR | wc -l)   # Number of files in corpus
TEMP_DIR=./cmin                         # Temporary directory for cmin
MAX_TMIN_FILE_SIZE=102400               # Skip files larger than 100KB for tmin

# Use real paths
CORPUS_DIR=$(realpath $CORPUS_DIR)
MINIMIZED_DIR=$(realpath $MINIMIZED_DIR)
FUZZ_BIN=$(realpath $FUZZ_BIN)

# Display arguments and statistics
echo "Argument validation successful!"
echo "Input directory: $CORPUS_DIR"
echo "Output (minimized) directory: $MINIMIZED_DIR"
echo "Fuzz target: $FUZZ_BIN"
echo "Number of files in initial corpus: $CORPUS_SIZE"

# Display start time
echo "Starting corpus minimization at $(date)"

# Create temporary directory
mkdir -p $TEMP_DIR

# Step 1: Use afl-cmin to reduce the corpus with edge-only coverage
echo
echo "Step 1: Running afl-cmin with edge-only coverage..."

# Run afl-cmin in edge-coverage mode
AFL_DEBUG=1 afl-cmin -i "$CORPUS_DIR" -o "$TEMP_DIR" -e -- "$FUZZ_BIN" @@

# Display number of remaining files after running cmin
CMIN_CORPUS_SIZE=$(ls $TEMP_DIR | wc -l)
echo "Remaining files after cmin minimization: $CMIN_CORPUS_SIZE"

# Step 2: Use afl-tmin on remaining files with edge-only coverage
echo
echo "Step 2: Running afl-tmin with edge-only coverage on remaining files..."

# Run afl-tmin on files that are less than MAX_TMIN_FILE_SIZE bytes
for f in "$TEMP_DIR"/*; do
    if [ -f "$f" ]; then
        base=$(basename "$f")
        size=$(stat -c%s "$f")

        if [ $size -gt $MAX_TMIN_FILE_SIZE ]; then
            echo "$base is too large (${size} bytes). Directly copying file to output directory."
            cp "$f" "$MINIMIZED_DIR/$base"
        else
            afl-tmin -i $f -o $MINIMIZED_DIR/$base-w_tmin -e -- $FUZZ_BIN @@
        fi
    fi
done

# Display number of remaining files after running tmin
TMIN_CORPUS_SIZE=$(ls "$MINIMIZED_DIR" | wc -l)
echo "Remaining files after tmin minimization: $TMIN_CORPUS_SIZE"

# Cleanup temporary folder
rm -rf $TEMP_DIR

# Exit
echo
echo "Minimization successful! Minimized corpus located at $MINIMIZED_DIR".