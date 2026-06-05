# Model Context Protocol Tools Directory

This page provides a comprehensive index of Model Context Protocol (MCP) integrations across CAD, CAM, FEA, 2D drafting, and 3D geometry engines. 

---

## 1. Enterprise PLM & Cloud CAD Integrations

### Autodesk Ecosystem
*   **`aps-mcp-server-nodejs`**: Simple Node.js-based server that integrates with Autodesk Platform Services (APS) API (Data Management, Model Derivative, AEC Data Modeling). Requires Secure Service Account authentication.
*   **`fusion360-mcp-server`**: Python-based server that communicates via TCP with an add-in running inside native Autodesk Fusion 360 desktop. Exposes 84 parametric modeling and CAM toolpath setup tools.
*   **`revit-mcp`**: Provides CRUD commands for BIM elements within Autodesk Revit.

### Siemens Ecosystem
*   **`@siemens/element-mcp`**: RAG-based integration providing access to element component library structures, design guidelines, and UI component APIs.
*   **`WinCC Unified MCP`**: Connects runtime machine alarms, SCADA telemetry, and tags to LLM chat sessions using the Openness API.
*   **`Fuse EDA AI Agent`**: Orchestrates Electronic Design Automation (EDA) pipelines across the Siemens EDA semiconductor portfolio.

### PTC Ecosystem
*   **`ThingWorx MCP`**: Public preview connector integrating IoT telemetry and machine KPIs directly into agent prompts.
*   **`hedless-onshape-mcp`**: REST-based integration with Onshape cloud CAD, offering sketch creation, assembly navigation, and variable tables.
*   **`creo-mcp`**: Connects via JLINK/CREOSON JSON-RPC to PTC Creo Parametric sessions.

### Dassault Systèmes Ecosystem
*   **`SolidworksMCP-python`**: Exposes 109 solid modeling tools to Windows COM APIs, utilizing SQLite for timeline checkpointing and body rollbacks.
*   **`SolidworksMCP-TS`**: TypeScript variant that falls back to VBA macro injections for complex (>12 params) parameters.

---

## 2. Open-Source Geometry Engines

### FreeCAD Integrations
*   **`freecad-mcp` (contextform)**: Integrates directly as a workbench user interface copilot, allowing real-time viewport screenshot verifications.
*   **`freecad-addon-robust-mcp-server` (spkane)**: Headless process-based executor for Linux CI environments with over 150 geometric tools.
*   **`freecad-mcp` (sandraschi)**: Full-pipeline executor that connects FreeCAD geometry to CalculiX structural FEA and OpenFOAM CFD solvers.

### Code-Driven CAD
*   **`openscad-mcp`**: Renders OpenSCAD geometries to Base64 PNG frames to complete the visual design feedback loop.
*   **`zoo-mcp`**: Cloud-native CAD API connection to Zoo.dev geometric compute kernels.

---

## 3. Consolidated Directory of MCP Servers

| Server / Tool Name | Primary Domain | Creator / Vendor | Type | URL / Repository |
| :--- | :--- | :--- | :--- | :--- |
| **aps-mcp-server-nodejs** | PLM / Cloud CAD API | Autodesk Platform Services | Enterprise (OSS) | [GitHub Repository](https://github.com/autodesk-platform-services/aps-mcp-server-nodejs) |
| **fusion360-mcp-server** | 3D CAD / CAM | faust-machines | Open Source | [GitHub Repository](https://github.com/faust-machines/fusion360-mcp-server) |
| **revit-mcp** | BIM / AEC | mcp-servers-for-revit | Open Source | [GitHub Repository](https://github.com/mcp-servers-for-revit/revit-mcp) |
| **@siemens/element-mcp** | UI/UX / Design System | Siemens | Enterprise | [Official Docs](https://element.siemens.io/get-started/element-mcp/) |
| **WinCC Unified MCP** | HMI / SCADA | Siemens | Enterprise | [Support Page](https://support.industry.siemens.com/cs/document/110002407) |
| **ThingWorx MCP** | IoT / PLM | PTC | Enterprise | [Support Page](https://support.ptc.com/help/thingworx/platform/r10.1/) |
| **creo-mcp** | 3D CAD | yangkunyi | Open Source | [GitHub Repository](https://github.com/yangkunyi/creo-mcp) |
| **hedless-onshape-mcp** | Cloud 3D CAD | hedless | Startup / OSS | [GitHub Repository](https://github.com/hedless/onshape-mcp) |
| **SolidworksMCP-python** | 3D CAD | andrewbartels1 | Open Source | [GitHub Repository](https://github.com/andrewbartels1/SolidworksMCP-python) |
| **SolidworksMCP-TS** | 3D CAD | vespo92 | Open Source | [GitHub Repository](https://github.com/vespo92/SolidworksMCP-TS) |
| **freecad-mcp (sandraschi)** | 3D CAD / FEA / CFD | sandraschi | Open Source | [GitHub Repository](https://github.com/sandraschi/freecad-mcp) |
| **freecad-mcp (contextform)** | 3D CAD Copilot | contextform | Open Source | [GitHub Repository](https://github.com/contextform/freecad-mcp) |
| **freecad-addon-robust** | 3D CAD / Macros | spkane | Open Source | [GitHub Repository](https://github.com/spkane/freecad-addon-robust-mcp-server) |
| **openscad-mcp** | Code CAD | quellant | Open Source | [GitHub Repository](https://github.com/quellant/openscad-mcp) |
| **RhinoMCP** | 3D NURBS / Scripting | jingcheng-chen (McNeel) | Enterprise (OSS) | [GitHub Repository](https://github.com/jingcheng-chen/rhinomcp) |
| **blender-mcp** | 3D Mesh / Blender | ahujasid | Open Source | [GitHub Repository](https://github.com/ahujasid/blender-mcp) |
| **zoo-mcp** | Cloud CAD API | Zoo.dev | Startup (OSS) | [GitHub Repository](https://github.com/KittyCAD/zoo-mcp) |
| **webmcp-openscad** | Web 3D Modeling | jherr | Open Source | [GitHub Repository](https://github.com/jherr/webmcp-openscad) |
