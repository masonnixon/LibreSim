# C compiler for LibreSim Coder
FROM gcc:13-bookworm

LABEL maintainer="LibreSim Team"
LABEL description="C compiler for LibreSim code generation"

# Install build tools
RUN apt-get update && apt-get install -y \
    cmake \
    make \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Copy compile script
COPY compile-c.sh /compile.sh
RUN chmod +x /compile.sh

ENTRYPOINT ["/compile.sh"]
