# Use the official AFL++ base image
FROM aflplusplus/aflplusplus:latest

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies required for building libjpeg-turbo and fuzzing
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    yasm \
    curl \
    libtool-bin \
    unzip \
 && rm -rf /var/lib/apt/lists/*

# Clone the libjpeg-turbo repo
RUN git clone --depth 1 https://github.com/libjpeg-turbo/libjpeg-turbo.git /libjpeg-turbo

# Clone the fuzzing scripts repository
RUN git clone --depth 1 https://github.com/libjpeg-turbo/fuzz /fuzz

# Copy your custom build.sh into the /fuzz directory
COPY build.sh /fuzz/build.sh

# Fetch and checkout the 'main' branch (or any other branch you prefer) and run build script
RUN cd /libjpeg-turbo && \
    git checkout main && \
    if [ -f /fuzz/build.sh ]; then \
        bash /fuzz/build.sh; \
    else \
        echo "Warning: build.sh not found in /fuzz"; \
    fi

# Set AFL++ compiler wrappers for instrumentation
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++

# Install libjpeg-turbo dependencies for building the JPEG tools (jpegtran, etc.)
RUN cd /libjpeg-turbo && \
    cmake . && \
    make && \
    make install

# Create directories for corpus and AFL++ output
RUN mkdir -p /corpus /afl-output

# Create a non-root user "fuzz" for running fuzzing tasks
RUN useradd -ms /bin/bash fuzz

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ensure the necessary files have correct ownership (after the build is complete)
RUN chown -R fuzz:fuzz /libjpeg-turbo/jpegtran /corpus /afl-output

# Set the working directory
WORKDIR /home/fuzz

# Switch to the non-root user
USER fuzz

# Set the entrypoint for the fuzzing container
ENTRYPOINT ["/entrypoint.sh"]
