# 1) Builder stage: compile fuzz target
# Image source from https://aflplus.plus/docs/install/. Will remain up to date with AFL++.
FROM aflplusplus/aflplusplus:latest AS builder

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Force CMake / Make to use AFL’s compilers
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++

# Create input/output directories
RUN mkdir -p /corpus /corpus_min /afl-output /out

# ----- TODO: FILL THIS SECTION OUT -----

# PART 1:
# Compile the fuzz target in /out. An example workflow is:
#   1) Install the required dependencies
#   2) Clone the github repository
#   3) Compile the fuzz target using afl-clang-fast or afl-clang-fast++ and setting
#      the -o flag to /out/fuzz_target.

# PART 2:
# After compiling the fuzz target, assign it to the environment variable FUZZER_BIN
# Example:
#   ENV FUZZER_BIN=/out/fuzz_target

# -----      END OF SECTION       -----

# Copy the entrypoint script into the image and grant executable permissions
COPY entrypoint.sh /entrypoint.sh
COPY minimize.sh /minimize.sh
RUN chmod +x /entrypoint.sh /minimize.sh

# Create a non-root user "fuzz" for running fuzzing tasks
RUN useradd -ms /bin/bash fuzz \
 && chown -R fuzz:fuzz /corpus /corpus_min /afl-output /out \
 && chmod -R u+rwX /corpus /corpus_min /afl-output /out

# Switch to non-root user's home directory
USER fuzz
WORKDIR /home/fuzz
