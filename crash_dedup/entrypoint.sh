#!/bin/bash
set -e

: "${OUTPUT_DIR:=/afl-output}"
: "${FUZZER_BIN:=/out/fuzz_both}"
: "${STACK_FRAMES:=3}"

echo "Running crash deduplication using top $STACK_FRAMES stack frames in $OUTPUT_DIR..."

mkdir -p "$OUTPUT_DIR/deduped_crashes"
declare -A seen
declare -A hash_to_files
declare -A hash_to_trace

for crash in "$OUTPUT_DIR/master/crashes"/id:*; do
  [ -f "$crash" ] || continue

  echo "FUZZER_BIN: $FUZZER_BIN"
  echo "Crash file: $crash"
  ls -l "$FUZZER_BIN"
  ls -l "$crash"


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
  clean_bt=$(echo "$bt" | sed -E 's/0x[0-9a-fA-F]+//g; s/\([^()]*\)/()/g')
  trimmed_bt=$(echo "$clean_bt" | head -n "$STACK_FRAMES")

  echo
  echo "Trimmed Stack Trace (Top $STACK_FRAMES frames):"
  echo "$trimmed_bt"
  echo

  hash=$(echo "$trimmed_bt" | md5sum | cut -d' ' -f1)

  if [[ -z "${seen[$hash]}" ]]; then
    seen[$hash]=1
    hash_to_trace[$hash]="$trimmed_bt"
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

echo "Deduplication summary written to $LOGFILE"
