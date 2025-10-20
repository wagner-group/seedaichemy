#!/bin/bash
set -e

echo "core" | tee /proc/sys/kernel/core_pattern

# Set a permissive umask so that new files are created with broad permissions.
umask 000

# One-time seed copy
if [ -d "/init_corpus" ] && [ ! -f "/corpus/.copied" ]; then
    echo "[+] Seeding /corpus from /init_corpus"
    mkdir -p /corpus
    cp -r /init_corpus/* /corpus/ || true
    touch /corpus/.copied
fi

: "${FUZZER_BIN:=$OUT/fuzz_both}"

# If FUZZER_ID is not provided, use the container's hostname (ensuring uniqueness in scaled environments)
if [ -z "$FUZZER_ID" ]; then
    FUZZER_ID=$(hostname)
fi
: "${CODE_DIR:=/src/libpcap}" 
: "${PROFILE_DIR:=${OUTPUT_DIR}/${FUZZER_ID}/profraw}"
: "${REPORT_DIR:=${OUTPUT_DIR}/llvm-cov-web}"
# Step 1: Build the target
cd "$SRC"
./build.sh

# Step 2: Run AFL++ fuzzer
echo "Input corpus: $CORPUS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Fuzzer binary: $FUZZER_BIN"
echo "Running afl-fuzz in master mode."
# exec afl-fuzz -M "$FUZZER_ID" -i "$CORPUS_DIR" -o "$OUTPUT_DIR" -- "$FUZZER_BIN" @@


export LLVM_PROFILE_FILE="${PROFILE_DIR}/id_%m_%p.profraw"
timeout 7200s afl-fuzz -M "$FUZZER_ID" -i "$CORPUS_DIR" -o "$OUTPUT_DIR"  -- "$FUZZER_BIN" @@ || true

# Step 3: Generate coverage report
#  Replay every queue file once
for f in ${OUTPUT_DIR}/${FUZZER_ID}/queue/id:*; do
  [ -f "$f" ] && ${FUZZER_BIN} "$f" || true
done

# ─── Merge profiles & generate HTML coverage ────────────────────────────────
echo "[*] Merging .profraw → merged.profdata"
llvm-profdata merge -sparse "${PROFILE_DIR}"/*.profraw \
                    -o "${OUTPUT_DIR}/${FUZZER_ID}/merged.profdata"

echo "[*] Writing Text report to ${REPORT_DIR}"
#llvm-cov show "${FUZZER_BIN}" \
#     -instr-profile="${OUTPUT_DIR}/merged.profdata" \
#     -format=html -output-dir="${REPORT_DIR}" \
#     -path-equivalence "$CODE_DIR" . \
#     -ignore-filename-regex='/usr/include/.*'

llvm-cov report /out/fuzz_both \
  -instr-profile="${OUTPUT_DIR}/${FUZZER_ID}/merged.profdata" \
  -show-functions \
  -- "$CODE_DIR/sf-pcapng.c" \
  > "$OUTPUT_DIR/${FUZZER_ID}/sf-pcap_coverage_function_report.txt"

# generate line coverage-report
llvm-cov show "${FUZZER_BIN}" \
  -instr-profile="${OUTPUT_DIR}/${FUZZER_ID}/merged.profdata" \
  -format=text \
  -show-line-counts-or-regions \
  -- "$CODE_DIR/sf-pcapng.c" \
  > "${OUTPUT_DIR}/${FUZZER_ID}/sf-pcap_coverage_line_report.txt"

# generate line coverage-report
llvm-cov show "${FUZZER_BIN}" \
  -instr-profile="${OUTPUT_DIR}/${FUZZER_ID}/merged.profdata" \
  -format=text \
  -show-line-counts-or-regions \
  -- "$CODE_DIR/savefile.c" \
  > "${OUTPUT_DIR}/${FUZZER_ID}/savefile_coverage_line_report.txt"

# generate line coverage-report
llvm-cov show "${FUZZER_BIN}" \
  -instr-profile="${OUTPUT_DIR}/${FUZZER_ID}/merged.profdata" \
  -format=text \
  -show-line-counts-or-regions \
  -- "$CODE_DIR/nametoaddr.c" \
  > "${OUTPUT_DIR}/${FUZZER_ID}/nametoaddr_coverage_line_report.txt"

# generate line coverage-report
llvm-cov show "${FUZZER_BIN}" \
  -instr-profile="${OUTPUT_DIR}/${FUZZER_ID}/merged.profdata" \
  -format=text \
  -show-line-counts-or-regions \
  -- "$CODE_DIR/gencode.c" \
  > "${OUTPUT_DIR}/${FUZZER_ID}/gencode_coverage_line_report.txt"

llvm-cov report "${FUZZER_BIN}" \
  -instr-profile="${OUTPUT_DIR}/${FUZZER_ID}/merged.profdata" \
  > "${OUTPUT_DIR}/${FUZZER_ID}/general_file_coverage_report.txt"

echo "[✔] Report ready: ${REPORT_DIR}/coverage.txt"

if [ "$(find "$OUTPUT_DIR/master/crashes" -type f 2>/dev/null | wc -l)" -gt 0 ]; then
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

    if [ "$SHOW_GDB" == "true" ]; then
      echo "Full GDB output:"
      echo "$gdb_output"
      echo
    fi

    bt=$(echo "$gdb_output" | grep "^#"[0-9])
    trimmed_bt=$(echo "$bt" | head -n "$STACK_FRAMES")
    cleaned_bt=$(echo "$trimmed_bt" | sed -E 's/(#[0-9]+)  (0x[0-9a-f]+ in )?([^(]+)\([^)]*\) (at|from)/\1 \3 () \4/')

    echo "Cleaned Stack Trace (Top $STACK_FRAMES frames):"
    echo "$cleaned_bt"

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
        extra=$((file_count - 3))
        echo "...and $extra more"
      fi
      ((index++))
    done
  } | tee "$LOGFILE"
  echo "Deduplication summary saved to $LOGFILE"
fi
