#!/bin/bash -eu

cd /src/libpng

# Disable unneeded features in pnglibconf.dfa
cat scripts/pnglibconf.dfa | \
  sed -e "s/option STDIO/option STDIO disabled/" \
      -e "s/option WARNING /option WARNING disabled/" \
      -e "s/option WRITE enables WRITE_INT_FUNCTIONS/option WRITE disabled/" \
> scripts/pnglibconf.dfa.temp
mv scripts/pnglibconf.dfa.temp scripts/pnglibconf.dfa

# Generate configure script
autoreconf -f -i

# Configure with custom prefix
./configure --with-libpng-prefix=OSS_FUZZ_

# Clean and build libpng
make -j$(nproc) clean
make -j$(nproc) libpng16.la

# Build the fuzzer binary
$CXX $CXXFLAGS -std=c++11 -I. \
     contrib/oss-fuzz/libpng_read_fuzzer.cc \
     -o /out/libpng_read_fuzzer \
     .libs/libpng16.a -lz $LIB_FUZZING_ENGINE

# Create seed corpus from existing PNGs
find . -name "*.png" | grep -v crashers | \
     xargs zip /out/libpng_read_fuzzer_seed_corpus.zip || echo "no PNGs found"

# Copy dict/options if available
cp contrib/oss-fuzz/*.dict contrib/oss-fuzz/*.options /out/ || true
