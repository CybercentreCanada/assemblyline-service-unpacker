FROM cccs/assemblyline-v4-service-base:latest

ENV SERVICE_PATH unpacker.Unpacker

RUN apt-get update && apt-get install -y \
  upx-ucl

# Switch to assemblyline user
USER assemblyline

# Copy Unpacker service code
WORKDIR /opt/al_service
COPY . .