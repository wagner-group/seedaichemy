FROM local-base-builder
USER root
# Install dependencies required by libpng + autotools
RUN apt-get update && apt-get install -y \
    autoconf \
    automake \
    libtool \
    make \
    zlib1g-dev \
    wget \
    zip \
    git \
    pkg-config
# Step 2: Create and fix permissions for directories
RUN mkdir -p /src /out /opt/seeds

WORKDIR /src
# Clone zlib
RUN git clone --depth 1 --branch v1.2.13 https://github.com/madler/zlib.git

# Clone libpng at the specified commit
RUN git clone https://github.com/glennrp/libpng.git && \
    cd libpng && \
    git checkout cd0ea2a7f53b603d3d9b5b891c779c430047b39a

# Copy the build script
COPY build.sh /src/

# Download dictionary and optional seed files
RUN wget --no-check-certificate -qO /out/libpng_read_fuzzer.dict \
    https://raw.githubusercontent.com/google/fuzzing/master/dictionaries/png.dict

# Optional seed inputs
ADD seeds /opt/seeds

