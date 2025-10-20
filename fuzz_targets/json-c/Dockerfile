# 1) Builder stage: compile json-c and produce dictionaries + fuzzers
# Image source from https://aflplus.plus/docs/install/. Will remain up to date with AFL++.
FROM aflplusplus/aflplusplus:latest AS builder

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Force CMake / Make to use AFL’s compilers
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++

# Install required dependencies
RUN apt-get update && apt-get install -y \
      git cmake build-essential libtool-bin unzip \
    && rm -rf /var/lib/apt/lists/*

# Clone the repository
WORKDIR /src
RUN git clone --depth 1 https://github.com/json-c/json-c.git json-c

# Build static lib and fuzzers
WORKDIR /src/json-c
RUN mkdir build && cd build \
 && cmake -DBUILD_SHARED_LIBS=OFF .. \
 && make -j"$(nproc)"

# Create /out, copy .dict files, and compile each *_fuzzer
RUN mkdir -p /out
# Copy all dictionaries into /out
RUN cp /src/json-c/fuzz/*.dict /out/

# Now compile every fuzz harness into /out
# RUN for f in /src/json-c/fuzz/*_fuzzer.cc; do \
#       name=$(basename "$f" .cc); \
#       afl-clang-fast++ -std=c++11 -g\
#         -fsanitize=fuzzer,address \
#         -I/src/json-c \
#         -I/src/json-c/build \
#         -I/src/json-c/src \
#         -I/src/json-c/include \
#         /src/json-c/fuzz/${name}.cc \
#         /src/json-c/build/libjson-c.a \
#         -o /out/${name}; \
#     done

RUN echo "Starting fuzzer compilation..." && \
    for f in /src/json-c/fuzz/*_fuzzer.cc; do \
      echo "Attempting to compile $f"; \
      name=$(basename "$f" .cc); \
      afl-clang-fast++ -std=c++11 -g \
        -fsanitize=fuzzer,address \
        -I/src/json-c \
        -I/src/json-c/build \
        -I/src/json-c/src \
        -I/src/json-c/include \
        /src/json-c/fuzz/${name}.cc \
        /src/json-c/build/libjson-c.a \
        -o /out/${name}; \
      if [ $? -ne 0 ]; then \
        echo "ERROR: Failed to compile ${name}. Halting build." >&2; \
        exit 1; \
      else \
        echo "Successfully compiled ${name} to /out/${name}"; \
      fi; \
    done && \
    echo "Fuzzer compilation loop finished." && \
    echo "Contents of /out immediately after compilation:" && \
    ls -la /out && \
    echo "Checking execute permissions specifically:" && \
    find /out -type f -executable -ls

# 2) Final stage: copy only what's needed for runtime
FROM aflplusplus/aflplusplus:latest

# Copy over only the artifacts we need
WORKDIR /out
COPY --from=builder /out/*_fuzzer.dict ./
COPY --from=builder /out/*_fuzzer ./

# Set the default fuzzer binary (override with ENV if needed)
ENV FUZZER_BIN=/out/json_object_fuzzer

# Create directories for the fuzzing corpus and AFL++ output.
# These might be overwritten by mounted volumes.
RUN mkdir -p /corpus /afl-output

# Copy the entrypoint script into the image and grant executable permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create a non-root user "fuzz" for running fuzzing tasks
RUN useradd -ms /bin/bash fuzz \
 && chown -R fuzz:fuzz /corpus /afl-output /out
#  && chown -R fuzz:fuzz /usr/local/bin/mutool /corpus /afl-output

# Switch to non-root user
USER fuzz

# Switched the working directly the home directly of the fuzz user
WORKDIR /home/fuzz

# Run the entry point script, this should begin fuzzing.
ENTRYPOINT ["/entrypoint.sh"]
