FROM aflplusplus/aflplusplus:latest

USER root

# Add LLVM 16 official repo (Ubuntu)
RUN apt-get update && apt-get install -y \
    gnupg lsb-release wget software-properties-common && \
    wget https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && ./llvm.sh 16

# Install required tools using consistent LLVM 16 toolchain
RUN apt-get install -y --no-install-recommends \
    clang-16 \
    lld-16 \
    llvm-16 \
    llvm-16-dev \
    llvm-16-tools \
    libclang-common-16-dev \
    llvm-dev \
    binutils-gold \
    llvm-runtime \
    automake \
    autoconf \
    libtool \
    make \
    cmake \
    ninja-build \
    g++ \
    zlib1g-dev \
    libssl-dev \
    pkg-config \
    python3 \
    python3-pip \
    ca-certificates \
    libxml2-dev \
    libprotobuf-dev \
    protobuf-compiler \
    zip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Update PATH and set alternatives
RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-16 100 && \
    update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-16 100 && \
    update-alternatives --install /usr/bin/ld ld /usr/bin/ld.lld-16 100 && \
    update-alternatives --install /usr/bin/llvm-ar llvm-ar /usr/bin/llvm-ar-16 100 && \
    update-alternatives --install /usr/bin/llvm-nm llvm-nm /usr/bin/llvm-nm-16 100

# Use AFL++ compiler wrappers
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++
ENV CFLAGS="-O2 -g"
ENV CXXFLAGS="-O2 -g"
ENV LIB_FUZZING_ENGINE="-fsanitize=fuzzer"
ENV FUZZER_LIB="/usr/local/lib/afl/libAFLDriver.a"
ENV LDFLAGS="-lpthread"
# OSS-Fuzz-compatible dirs
ENV SRC=/src
ENV OUT=/out
ENV WORK=/work
ENV CORPUS_DIR=/seeds
RUN mkdir -p $SRC $OUT $WORK

# Upgrade Python tooling
RUN python3 -m pip install --upgrade pip setuptools

# Create fuzzing user
RUN useradd -m fuzzbuilder && chown -R fuzzbuilder:fuzzbuilder /src /out /work
USER fuzzbuilder
WORKDIR /home/fuzzbuilder

