#!/bin/bash
trap 'echo "Received termination signal. Shutting down..."; exit 0' SIGTERM SIGINT
set -e

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# Set the defaults if not provided.
: "${CORPUS_DIR:=/corpus}"
: "${OUTPUT_DIR:=/afl-output}"
: "${FUZZER_ID:=}"
# Path to your JSON-C fuzzer binary
: "${FUZZER_BIN:=/out/json_object_fuzzer}" # there are four of them, this is one of them
: "${AFL_DICT:=/out/json_object_fuzzer.dict}"

# Unique ID: master vs secondaries
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi

echo "Using FUZZER_ID: $FUZZER_ID"
echo "[*] Running afl-fuzz on $FUZZER_BIN …"

if [ "$FUZZER_ID" = "master" ]; then
    echo "→ Master mode"
    exec afl-fuzz -M "$FUZZER_ID" \
        -x "$AFL_DICT" \
        -i "$CORPUS_DIR" \
        -o "$OUTPUT_DIR" \
        -- "$FUZZER_BIN" @@
else
    echo "→ Secondary mode"
    exec afl-fuzz -S "$FUZZER_ID" \
        -x "$AFL_DICT" \
        -i "$CORPUS_DIR" \
        -o "$OUTPUT_DIR" \
        -- "$FUZZER_BIN" @@
fi
