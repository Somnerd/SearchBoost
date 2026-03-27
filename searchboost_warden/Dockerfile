FROM rust:1.93.1-slim AS builder

ARG BUILD_PROFILE=release

RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependencies
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN if [ "$BUILD_PROFILE" = "release" ]; then cargo build --release; else cargo build; fi
RUN rm -rf src

# Build application
COPY . .
RUN touch src/main.rs
RUN if [ "$BUILD_PROFILE" = "release" ]; then cargo build --release; else cargo build; fi

FROM debian:bookworm-slim
ARG BUILD_PROFILE=release

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/${BUILD_PROFILE}/sb_warden /usr/local/bin/warden

RUN mkdir -p /logs

WORKDIR /usr/local/bin
CMD ["warden"]
