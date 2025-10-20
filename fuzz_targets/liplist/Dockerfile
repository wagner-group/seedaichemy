# Use the official AFL++ image
FROM aflplusplus/aflplusplus:latest

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && \
    apt-get install -y \
        git \
        build-essential \
        libtool-bin \
        autoconf \
        automake \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Clone libplist into /libplist
RUN git clone --depth 1 https://github.com/libimobiledevice/libplist.git /libplist

# Set working directory to libplist
WORKDIR /libplist

# Use AFL++ compiler wrappers
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++
ENV CFLAGS="-O2 -g"
ENV CXXFLAGS="-O2 -g"

# Build libplist
RUN ./autogen.sh && \
    ./configure --disable-shared --enable-static && \
    make -j$(nproc)

# Create the output directory for the compiled fuzzers
RUN mkdir -p /home/fuzz

# Copy your custom fuzzer code (with main for AFL++)
COPY bplist_fuzzer_afl.cc /libplist/fuzz/bplist_fuzzer_afl.cc

WORKDIR /libplist
# Compile your custom fuzzer binary
RUN $CXX $CXXFLAGS -std=c++11 -Iinclude/ \
    fuzz/bplist_fuzzer_afl.cc -o /home/fuzz/bplist_fuzzer\
    src/.libs/libplist-2.0.a

# Create corpus and output directories (for fallback if not using volumes)
RUN mkdir -p /corpus /afl-output /corpus_min /home/fuzz

# Create fuzz user
RUN useradd -ms /bin/bash fuzz

# Now change ownership
RUN chown -R fuzz:fuzz /corpus /afl-output /corpus_min /home/fuzz /usr/local/bin /libplist

# Copy the entrypoint script into the image and make it executable
COPY --chown=fuzz:fuzz entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to fuzz user
USER fuzz
WORKDIR /home/fuzz

# Start the fuzzing entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

