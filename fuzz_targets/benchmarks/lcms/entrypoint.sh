#!/bin/bash
set -e

echo "core" | tee /proc/sys/kernel/core_pattern

# Set a permissive umask so that new files are created with broad permissions.
umask 000

: "${FUZZER_BIN:=$OUT/fuzz_both}"

# If FUZZER_ID is not provided, use the container's hostname (ensuring uniqueness in scaled environments)
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi

if [ "$(find "$OUTPUT_DIR/master/crashes" -type f 2>/dev/null | wc -l)" -ne 0 ]; then
    echo "ERROR: $OUTPUT_DIR/master/crashes is not empty. Please rename/clear it or delete the volume before running."
    exit 1
fi

if [ -d "$OUTPUT_DIR/deduped_crashes" ] && [ "$(find "$OUTPUT_DIR/deduped_crashes" -type f | wc -l)" -ne 0 ]; then
    echo "ERROR: $OUTPUT_DIR/deduped_crashes is not empty. Please rename/clear it or delete the volume before running."
    exit 1
fi

# Step 1: Build the target
cd "$SRC"
./build.sh

# Step 2: Run AFL++ fuzzer
echo "Input corpus: $CORPUS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Fuzzer binary: $FUZZER_BIN"
echo "Running afl-fuzz in master mode."

afl-fuzz -M "$FUZZER_ID" -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -- "$FUZZER_BIN" @@

if [ -n "$STACK_FRAMES" ]; then
  echo "Running crash deduplication using top $STACK_FRAMES stack frames..."
  mkdir -p "$OUTPUT_DIR/deduped_crashes"
  declare -A seen
  declare -A hash_to_files
  declare -A hash_to_trace

  for crash in "$OUTPUT_DIR/master/crashes"/id:*; do
    [ -f "$crash" ] || continue

    echo
    echo "====================================="
    echo "Analyzing crash: $(basename "$crash")"
    echo "====================================="

    gdb_output=$(gdb -batch -ex "run $crash" -ex "bt" --args "$FUZZER_BIN" "$crash" 2>&1)
    
    if [ "SHOW_GDB" == "true" ]; then
      echo
      echo "Full GDB output:"
      echo "$gdb_output"
      echo
    fi

    bt=$(echo "$gdb_output" | grep "^#"[0-9])
    trimmed_bt=$(echo "$bt" | head -n "$STACK_FRAMES")

    echo
    echo "Trimmed Stack Trace (Top $STACK_FRAMES frames):"
    echo "$trimmed_bt"
    echo

    cleaned_bt=$(echo "$trimmed_bt" | sed -E 's/(#[0-9]+)  (0x[0-9a-f]+ in )?([^(]+)\([^)]*\) (at|from)/\1 \3 () \4/')
    
    echo
    echo "Cleaned Stack Trace (Top $STACK_FRAMES frames without addresses and arguments):"
    echo "$cleaned_bt"
    echo

    hash=$(echo "$cleaned_bt" | md5sum | cut -d' ' -f1)

    if [[ -z "${seen[$hash]}" ]]; then
      seen[$hash]=1
      hash_to_trace[$hash]="$cleaned_bt"
      cp "$crash" "$OUTPUT_DIR/deduped_crashes/$(basename "$crash")"
    fi

    hash_to_files[$hash]="${hash_to_files[$hash]}$(basename "$crash")"$'\n'
  done

  num_unique=$(ls "$OUTPUT_DIR/deduped_crashes" | wc -l)

  LOGFILE="$OUTPUT_DIR/crash_dedup.log"
  {
    echo
    echo "========== Deduplication Summary =========="
    echo "$num_unique unique crashes saved to $OUTPUT_DIR/deduped_crashes"
    index=1
    for hash in "${!seen[@]}"; do
      echo
      echo "====================================="
      file_list=$(echo "${hash_to_files[$hash]}")
      file_count=$(echo "$file_list" | wc -l)
      echo "Unique Bug Hash #$index: $hash"
      echo "====================================="
      echo "Stack Trace:"
      echo "${hash_to_trace[$hash]}"
      echo
      echo "Crash Files:"
      if [ "$file_count" -le 3 ]; then
        echo "$file_list"
      else
        echo "$file_list" | head -n 3
        echo "..."
      fi
      ((index++))
    done
  } | tee "$LOGFILE"
  echo 
  echo "Deduplication summary saved to $LOGFILE"
fi
