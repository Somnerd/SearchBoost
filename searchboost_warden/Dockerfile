FROM rust:1.93.1-slim AS builder

RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    gcc \
    &&rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN cargo build --release
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/sb_warden /usr/local/bin/warden

RUN mkdir -p /logs

WORKDIR /usr/local/bin
CMD ["warden"]
