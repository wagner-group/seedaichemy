# Image source from https://aflplus.plus/docs/install/. Will remain up to date with AFL++.
FROM aflplusplus/aflplusplus:latest

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Force CMake / Make to use AFL’s compilers
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++

# Install required dependencies
RUN apt-get update && apt-get install -y \
      git make autoconf automake libtool \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository
WORKDIR /src
RUN git clone --depth 1 https://github.com/madler/zlib.git
RUN git clone --depth 1 https://github.com/glennrp/libpng.git

# Build libpng
WORKDIR /src/libpng
RUN autoreconf -f -i && \
    ./configure && \
    make -j$(nproc) clean && \
    make -j$(nproc) libpng16.la

# Compile the fuzz target
RUN mkdir -p /corpus /afl-output /out /corpus_min
RUN afl-clang-fast++ -std=c++11 -g \
        -fsanitize=fuzzer,address \
        -I. \
        /src/libpng/contrib/oss-fuzz/libpng_read_fuzzer.cc \
        -o /out/fuzz_target \
        .libs/libpng16.a -lz

# Copy the entrypoint script into the image and grant executable permissions
COPY entrypoint.sh /entrypoint.sh
COPY minimize.sh /minimize.sh
RUN chmod +x /entrypoint.sh
RUN chmod +x /minimize.sh

# Create a non-root user "fuzz" for running fuzzing tasks
RUN useradd -ms /bin/bash fuzz \
 && chown -R fuzz:fuzz /corpus /afl-output /out \
 && chmod -R u+rwX /corpus /afl-output /out

# Switch to non-root user
USER fuzz

# Switched the working directly the home directly of the fuzz user
WORKDIR /home/fuzz

# Run the entry point script, this should begin fuzzing.
# ENTRYPOINT ["/entrypoint.sh"]
