ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

ENV SERVICE_PATH unpacker.Unpacker

USER root

RUN apt-get update && apt-get install -y upx-ucl && rm -rf /var/lib/apt/lists/*

# Switch to assemblyline user
USER assemblyline

# Copy Unpacker service code
WORKDIR /opt/al_service
COPY . .

# Patch version in manifest
ARG version=4.0.0.dev1
USER root
RUN sed -i -e "s/\$SERVICE_TAG/$version/g" service_manifest.yml

# Switch to assemblyline user
USER assemblyline