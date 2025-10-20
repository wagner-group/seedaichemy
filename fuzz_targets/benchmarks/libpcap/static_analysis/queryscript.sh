#!/bin/bash
set -e

# Set a permissive umask so that new files are created with broad permissions.
umask 000

: "${QUERY_PATH:=$SRC/codeql_callpath}"

cd $QUERY_PATH

codeql query run --database=../libpcap-db callpath_stmt.ql --output=out.bqrs

codeql bqrs decode --format=csv --output=out.csv out.bqrs

mv out.csv $OUTPUT_DIR
