# 1) Builder stage: compile fuzz target
# Image source from https://aflplus.plus/docs/install/. Will remain up to date with AFL++.
FROM aflplusplus/aflplusplus:latest AS builder

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Force CMake / Make to use AFL's compilers
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++

# ----- TODO: FILL THIS SECTION OUT -----

# PART 1:
# Install required dependencies
RUN apt-get update && apt-get install -y \
    libass-dev libfreetype6-dev libfribidi-dev pkg-config make autoconf automake libtool \
    && rm -rf /var/lib/apt/lists/*

# Create build directory and copy fuzz target source and dictionary
WORKDIR /src
COPY fuzz.c .
COPY ass.dict .
COPY writeout.h .

# Ensure required directories exist before changing ownership and permissions
RUN mkdir -p /corpus /afl-output /out /corpus_min

# Compile the fuzz target with proper AFL++ instrumentation
RUN afl-clang-fast -std=c11 -g \
    -DASS_FUZZMODE=0 \
    -fsanitize=address \
    -I/usr/include/ass \
    fuzz.c -lass \
    -o /out/ass_parser_fuzzer && \
    cp ass.dict /out/ass.dict && \
    afl-showmap -o /dev/null -q /out/ass_parser_fuzzer < /dev/null

# PART 2:
# Set the environment variable for the fuzz target binary
ENV FUZZER_BIN=/out/ass_parser_fuzzer

# -----      END OF SECTION       -----


# Copy the entrypoint script into the image and grant executable permissions
COPY entrypoint.sh /entrypoint.sh
COPY minimize.sh /minimize.sh
RUN chmod +x /entrypoint.sh /minimize.sh

# Create a non-root user "fuzz" for running fuzzing tasks
RUN useradd -ms /bin/bash fuzz \
 && chown -R fuzz:fuzz /corpus /afl-output /out \
 && chmod -R u+rwX /corpus /afl-output /out

# Switch to non-root user's home directory
USER fuzz
WORKDIR /home/fuzz
