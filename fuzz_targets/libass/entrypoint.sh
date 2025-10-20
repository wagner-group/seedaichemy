#!/bin/bash
trap 'echo "Received termination signal. Shutting down..."; exit 0' SIGTERM SIGINT
set -e

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# Check that the fuzzer binary has been set
if [[ -z "$FUZZER_BIN" ]]; then
    echo "Error: make sure FUZZER_BIN is set in the Dockerfile"
    exit 1
fi

# Create minimized corpus directory (won't fail if it already exists)
mkdir -p ./corpus_min
MINIMIZED_DIR=./corpus_min

# Generate minimized corpus
/minimize.sh "$CORPUS_DIR" "$MINIMIZED_DIR" "$FUZZER_BIN"

if [[ $? -eq 1 ]]; then
    echo "Minimization failed!"
    exit 1
fi

# Extract minimized corpus to mounted volume if available
# if [[ -d "/corpus_min_mount" ]]; then
#     echo "Extracting minimized corpus to mounted volume..."
#     # Try to copy files one by one to handle permission issues
#     for file in "$MINIMIZED_DIR"/*; do
#         if [[ -f "$file" ]]; then
#             filename=$(basename "$file")
#             echo "Copying $filename..."
#             cat "$file" > "/corpus_min_mount/$filename" 2>/dev/null || echo "Warning: Could not copy $filename"
#         fi
#     done
#     echo "Minimized corpus extraction completed"
# fi

# Run AFL++ on the minimized corpus
echo "Using FUZZER_ID: $FUZZER_ID"
echo "[*] Running afl-fuzz on $FUZZER_BIN …"
if [ "$FUZZER_ID" = "master" ]; then
    echo "→ Master mode"
    exec afl-fuzz -M "$FUZZER_ID" \
    -i "$MINIMIZED_DIR" \
    -o "$OUTPUT_DIR" \
    -- "$FUZZER_BIN" @@
fi