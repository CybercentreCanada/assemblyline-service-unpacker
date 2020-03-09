FROM cccs/assemblyline-v4-service-base:latest

ENV SERVICE_PATH unpacker.Unpacker

USER root

RUN apt-get update && apt-get install -y upx-ucl && rm -rf /var/lib/apt/lists/*

# Switch to assemblyline user
USER assemblyline

# Copy Unpacker service code
WORKDIR /opt/al_service
COPY . .