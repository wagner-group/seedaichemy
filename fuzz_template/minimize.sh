#!/bin/bash
set -e

echo "Starting minimization procedure..."

# Validate arguments
echo "Validating arguments..."
if [[ $# != 3 ]]; then
    echo "Incorrect number of arguments: $#"
    exit 1
fi
if [[ ! -d "$1" ]]; then
    echo "The corpus directory (arg 1) is invalid!"
    exit 1
fi
if [[ ! -d "$2" ]]; then
    echo "The minimized directory (arg 2) is invalid!"
    exit 1
fi
if [[ ! -x "$3" ]]; then
    echo "The fuzz target (arg 3) is invalid!"
    exit 1
fi
echo "Argument validation successful!"

# Assign arguments
CORPUS_DIR=$1
MINIMIZED_DIR=$2
FUZZ_BIN=$3

# Use real paths
CORPUS_DIR=$(realpath $CORPUS_DIR)
MINIMIZED_DIR=$(realpath $MINIMIZED_DIR)
FUZZ_BIN=$(realpath $FUZZ_BIN)

# Constants
CORPUS_SIZE=$(ls $CORPUS_DIR | wc -l)  # Number of files in the initial corpus

# Display arguments and statistics
echo "Input directory: $CORPUS_DIR"
echo "Output (minimized) directory: $MINIMIZED_DIR"
echo "Fuzz target: $FUZZ_BIN"
echo "Number of files in initial corpus: $CORPUS_SIZE"

# Display start time
echo "Starting corpus minimization..."

# Use afl-cmin to reduce the corpus with edge-only coverage
echo
echo "Running afl-cmin with edge-only coverage at $(date)..."

# Run afl-cmin in edge-coverage mode
mkdir -p ./cmin-output
AFL_DEBUG=1 afl-cmin -i "$CORPUS_DIR" -o "./cmin-output" -t 1000 -- "$FUZZ_BIN" @@
cp ./cmin-output/* $MINIMIZED_DIR
rm -rf ./cmin-output

# Display number of remaining files after running cmin
CMIN_CORPUS_SIZE=$(ls $MINIMIZED_DIR | wc -l)
echo "Remaining files after cmin minimization: $CMIN_CORPUS_SIZE"
echo "afl-cmin finished at $(date)."

# Exit
echo
echo "Minimization successful! Minimized corpus located at $MINIMIZED_DIR".