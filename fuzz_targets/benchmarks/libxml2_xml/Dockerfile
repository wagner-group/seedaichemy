# 1) Builder stage: compile fuzz target
# Image source from https://aflplus.plus/docs/install/. Will remain up to date with AFL++.
FROM aflplusplus/aflplusplus:latest AS builder

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Force CMake / Make to use AFL's compilers
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++
ENV PYTHONUNBUFFERED=1

# ----- TODO: FILL THIS SECTION OUT -----

# Install required dependencies
RUN apt-get update && \
    apt-get install -y \
        make \
        git \
        autoconf \
        automake \
        libtool \
        pkg-config \
        wget

# Clone libxml2 and checkout the specific version
RUN git clone https://gitlab.gnome.org/GNOME/libxml2.git /libxml2 && \
    cd /libxml2 && \
    git checkout -f v2.9.2

# Copy fuzz target and patch into the image
COPY target.cc /target.cc
COPY old/fr_injection.patch /fr_injection.patch

# Apply patch and build libxml2 with AFL++ compilers
RUN cd /libxml2 && \
    git apply /fr_injection.patch && \
    ./autogen.sh && \
    ./configure --without-python --with-threads=no --with-zlib=no --with-lzma=no && \
    make -j1

# Create output directory for the fuzz target
RUN mkdir -p /out 
RUN mkdir -p /corpus /afl-output /out

# Build the fuzz target
RUN $CXX $CXXFLAGS -std=c++11 /target.cc -I/libxml2/include /libxml2/.libs/libxml2.a -o /out/xml -lpthread -ldl

# Set the fuzzer binary path
ENV FUZZER_BIN=/out/xml

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
