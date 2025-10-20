# Image source from https://aflplus.plus/docs/install/. Will remain up to date with AFL++.
FROM aflplusplus/aflplusplus:latest

# Set noninteractive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

ENV FIXREVERTER="on 0 1 2"


# Install required dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libtool-bin \
    unzip \
    autoconf \
    automake \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

# Clone the libxml2 repository into /src/libxml2
WORKDIR /src
RUN git clone https://gitlab.gnome.org/GNOME/libxml2.git libxml2
RUN git -C libxml2 checkout -f 99a864a1f7a9cb59865f803770d7d62fb47cad69

# Build libxml2 as a static library
WORKDIR /src/libxml2
RUN ./autogen.sh
RUN ./configure --enable-static --disable-shared --without-python --with-threads=no --with-zlib=no --with-lzma=no
RUN make -j$(nproc)

# Copy the fuzzer into the image
COPY libxml2_xml_reader_for_file_fuzzer.cc /src/libxml2/
COPY fuzzer_temp_file.h /src/libxml2/

# Build the AFL++-instrumented fuzzer
RUN mkdir -p /out && \
    afl-clang-fast++ -std=c++11 -g \
    -fsanitize=fuzzer,address \
    -I/src/libxml2/include -I/src/libxml2 \
    /src/libxml2/libxml2_xml_reader_for_file_fuzzer.cc \
    .libs/libxml2.a \
    -o /out/libxml2_reader_fuzzer

# Create directories for the corpus and afl output (fallback if volume mount is not used)
RUN mkdir -p /corpus /afl-output

# Copy the entrypoint script into the image and grant executable permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


# Create a non-root user "fuzz" for running fuzzing tasks and set proper ownership
RUN useradd -ms /bin/bash fuzz && \
    chown -R fuzz:fuzz /corpus /afl-output /out

# Switch to non-root user and set working directory to fuzz user's home
USER fuzz
WORKDIR /home/fuzz

# Run the fuzzer entrypoint
ENTRYPOINT ["/entrypoint.sh"]
