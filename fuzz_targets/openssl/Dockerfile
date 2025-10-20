# Image source from https://aflplus.plus/docs/install/. Will remain up to date with AFL++.
FROM aflplusplus/aflplusplus:latest

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libtool-bin \
    unzip \
    afl-clang \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Clone the OpenSSL repository into /openssl
RUN git clone --depth 1 https://github.com/openssl/openssl.git /openssl

# Switch working directory to /openssl
WORKDIR /openssl

# Set AFL++ compiler wrappers for instrumentation
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++

# Configure openssl to enable fuzz testing with AFL as specified in
# the documentation.
RUN ./config enable-fuzz-afl no-shared no-module \
    -DPEDANTIC enable-tls1_3 enable-weak-ssl-ciphers enable-rc5 \
    enable-md2 enable-ssl3 enable-ssl3-method enable-nextprotoneg \
    enable-ec_nistp_64_gcc_128 -fno-sanitize=alignment \
    --debug && make && make install

# Create directories for the fuzzing corpus and AFL++ output.
# These will be overwritten by the mounted volumes, These are only here for fallback.
RUN mkdir -p /corpus /afl-output /corpus_min

# Copy the entrypoint script into the image and grant executable permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create a non-root user "fuzz" for running fuzzing tasks
RUN useradd -ms /bin/bash fuzz \
 && chown -R fuzz:fuzz /corpus /afl-output /corpus_min

# Switch to non-root user
USER fuzz

# Switched the working directory to the home directory of the fuzz user
WORKDIR /home/fuzz

# Run the entry point script, this should begin fuzzing.
ENTRYPOINT ["/entrypoint.sh"]
