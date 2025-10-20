FROM debian:bullseye

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    llvm \
    git \
    wget \
    make \
    autoconf \
    libtool \
    automake \
    ca-certificates \
    curl \
    python3 \
    python3-pip

# Set compiler so AFL++ builds properly
ENV CC=clang
ENV CXX=clang++

# Install AFL++
RUN git clone https://github.com/AFLplusplus/AFLplusplus.git && \
    cd AFLplusplus && \
    make -j$(nproc) && \
    make install

# Clone and build libyaml
RUN git clone https://github.com/yaml/libyaml.git

WORKDIR /libyaml
RUN export CC=afl-clang-fast && \
    ./bootstrap || true && \
    ./configure && \
    make -j$(nproc)

# Add and compile fuzz target (link with AFL++ runtime)
COPY fuzz_yaml.c /libyaml/fuzz_yaml.c
RUN afl-clang-fast fuzz_yaml.c -I./include ./src/.libs/libyaml.a -o fuzz_yaml

# Seed and run fuzzing
CMD AFL_SKIP_CPUFREQ=1 afl-fuzz -i /input -o /output /libyaml/fuzz_yaml


