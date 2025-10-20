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
 && rm -rf /var/lib/apt/lists/*

# Clone the MuPDF repository into /mupdf
RUN git clone --recursive https://github.com/ArtifexSoftware/mupdf.git /mupdf

WORKDIR /mupdf

RUN git submodule update --init

# Set AFL++ compiler wrappers for instrumentation
ENV CC=afl-clang-fast
ENV CXX=afl-clang-fast++

# Build and install only the command line tools (e.g. mutool)
# Disabling X11 and GLUT support as per instructions
RUN make HAVE_X11=no HAVE_GLUT=no -j$(nproc) prefix=/usr/local install

# Create directories for the fuzzing corpus and AFL++ output.
# These will be overwritten by the mounted volumes, These are only here for fallback.
# RUN mkdir -p /corpus /afl-output
RUN mkdir -p /corpus /afl-output /corpus_min

# Copy the entrypoint script into the image and grant executable permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create a non-root user "fuzz" for running fuzzing tasks
RUN useradd -ms /bin/bash fuzz \
 && chown -R fuzz:fuzz /usr/local/bin/mutool /corpus /afl-output

# Switch to non-root user
USER fuzz

# Switched the working directly the home directly of the fuzz user
WORKDIR /home/fuzz

# Run the entry point script, this should begin fuzzing.
ENTRYPOINT ["/entrypoint.sh"]
