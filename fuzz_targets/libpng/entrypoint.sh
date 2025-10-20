#!/bin/bash
trap 'echo "Received termination signal. Shutting down..."; exit 0' SIGTERM SIGINT
set -e

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# Set the defaults if not provided.
: "${CORPUS_DIR:=/corpus}"
: "${OUTPUT_DIR:=/afl-output}"
: "${FUZZER_ID:="master"}"
: "${FUZZER_BIN:=/out/fuzz_target}"

# Create directory for minimization output
MINIMIZED_DIR=./corpus_min
mkdir $MINIMIZED_DIR

/minimize.sh $CORPUS_DIR $MINIMIZED_DIR $FUZZER_BIN

echo "Using FUZZER_ID: $FUZZER_ID"
echo "[*] Running afl-fuzz on $FUZZER_BIN …"

if [ "$FUZZER_ID" = "master" ]; then
    echo "→ Master mode"
    exec afl-fuzz -M "$FUZZER_ID" \
    -i "$MINIMIZED_DIR" \
    -o "$OUTPUT_DIR" \
    -- "$FUZZER_BIN" @@
fi

