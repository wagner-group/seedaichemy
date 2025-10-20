#!/bin/bash
trap 'echo "Received termination signal. Shutting down..."; exit 0' SIGTERM SIGINT
set -e

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# Set the default corpus, output directory, and corpus minimization output directory if not provided.
: "${CORPUS_DIR:=/corpus}"
: "${OUTPUT_DIR:=/afl-output}"
: "${MINIMIZED_DIR:=/corpus_min}"


# If FUZZER_ID is not provided, use the container's hostname (ensuring uniqueness in scaled environments)
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi

echo "Using FUZZER_ID: $FUZZER_ID"

# TODO: Re-examine this
MODE=$1
shift || true
# MODE=${1:-fuzz}      # if no first argument, default to "fuzz"
# [[ $# -gt 0 ]] && shift   # shift only when an arg was supplied

echo "Mode: $MODE"

if [ "$MODE" = "minimize" ]; then
  echo "[*] Running afl-cmin to minimize corpus..."
  echo "[*] Attempting to delete /corpus_min..."
  # rm -rf "$MINIMIZED_DIR"
  mkdir -p "$MINIMIZED_DIR"
  AFL_CMIN_ALLOW_ANY=1 afl-cmin -t 1000 -i "$CORPUS_DIR" -o "$MINIMIZED_DIR" -T all -- /usr/local/bin/mutool "$@"
  chmod -R a+rwX "$MINIMIZED_DIR"
else
  echo "[*] Running afl-fuzz..."
  # Choose mode based on FUZZER_ID.
  # Setting fuzzing target to mutool clean; this is a common choice for PDF fuzzing.
  if [ "$FUZZER_ID" = "master" ]; then
    echo "Running afl-fuzz in master mode."
    # exec /usr/local/bin/afl-fuzz -M "$FUZZER_ID"  -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -t 2000 -- /usr/local/bin/mutool clean @@ /dev/null
    exec /usr/local/bin/afl-fuzz -M "$FUZZER_ID"  -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -- /usr/local/bin/mutool clean @@ /dev/null
  else
    echo "Running afl-fuzz in secondary mode."
    exec /usr/local/bin/afl-fuzz -S "$(hostname)" -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -- /usr/local/bin/mutool clean @@ /dev/null
  fi
fi
