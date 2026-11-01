# Dedicated userspace launcher for an actual KVM virtual machine.
# Building/running this optional recipe requires the recorded VM-route approval.
# The Wright runtime/base image is not modified and contains no new CAD software.
FROM ubuntu:24.04@sha256:786a8b558f7be160c6c8c4a54f9a57274f3b4fb1491cf65146521ae77ff1dc54
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    qemu-system-arm qemu-utils qemu-efi-aarch64 cloud-image-utils \
    python3 ca-certificates curl openssh-client && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /lab
CMD ["qemu-system-aarch64", "--version"]
