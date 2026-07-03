# System Requirements & Prerequisites

Before installing and booting Wright, ensure your host environment meets these system and hardware requirements.

---

## 1. Hardware Requirements

### Minimum Configuration
*   **CPU**: 4-Core x86_64 or ARM64 processor
*   **Memory**: 16 GB RAM
*   **Disk**: 20 GB free space (SSD recommended)

### Recommended Configuration (For Local Inference & Advanced Solvers)
*   **Appliance Workstation**: Dell GB10 / NVIDIA DGX Spark
*   **CPU**: 16-Core / 32-Thread AMD Threadripper or Intel Xeon
*   **GPU**: NVIDIA RTX 4090 or NVIDIA H100 (128 GB+ Unified VRAM)
*   **Memory**: 128 GB RAM
*   **Disk**: 500 GB NVMe PCIe Gen 5 SSD

---

## 2. Software Requirements

Ensure the following base tools are installed on your host system:

### Operating System
*   **Linux**: Ubuntu 22.04 LTS / 24.04 LTS (Recommended), Debian 12, Fedora 40
    *   *Note for Ubuntu 24.04+*: Default AppArmor rules restrict unprivileged user namespaces, which can cause sandboxing tools (e.g. `bwrap`) to fail. See the [GB10 Workstation Guide](workstation-gb10-dgx.md#troubleshooting-sandboxing-ubuntu-2404) for AppArmor setup instructions.
*   **macOS**: macOS Sonoma 14+ (Compatible, though CalculiX/OpenFOAM solvers require Docker setup)
*   **Windows**: Windows 11 with WSL2 (Ubuntu runtime)

### Core Dependencies
*   **Docker Engine**: v24.0+ and **Docker Compose** v2.20+
*   **Python**: v3.11 or v3.12 (For running locally on the host)
*   **Node.js**: v20+ and **npm / yarn** (For frontend development)
*   **Git**: v2.34+ (For workspace history tracking)
