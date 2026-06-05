import { useEffect, useState } from "react";
import useLogger from "../../hooks/useLogger";
import { FolderIcon, FileIcon, PlusIcon } from "../common/Icons";

interface VaultFile {
  name: string;
  category: string;
  size: string;
  modified: string;
}

const INITIAL_FILES: VaultFile[] = [
  {
    name: "beam_stress_analysis.py",
    category: "Calculations",
    size: "14.2 KB",
    modified: "2 hours ago",
  },
  {
    name: "chassis_cad_assembly.stl",
    category: "CAD Models",
    size: "2.4 MB",
    modified: "Yesterday",
  },
  {
    name: "compliance_report.pdf",
    category: "Compliance Records",
    size: "185 KB",
    modified: "3 days ago",
  },
  {
    name: "heat_sink_thermal.scad",
    category: "CAD Models",
    size: "8.7 KB",
    modified: "Last week",
  },
];

export function FileVaultPage() {
  const logger = useLogger("FileVaultPage");
  const [selectedFolder, setSelectedFolder] = useState<string>("All Files");
  const [files, setFiles] = useState<VaultFile[]>(INITIAL_FILES);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    logger.info("File Vault Page loaded");
  }, [logger]);

  const folders = [
    "All Files",
    "CAD Models",
    "Calculations",
    "FEA Outputs",
    "Compliance Records",
  ];

  const filteredFiles = files.filter(
    (file) =>
      selectedFolder === "All Files" || file.category === selectedFolder,
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    // Mock file import
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles: VaultFile[] = Array.from(e.dataTransfer.files).map(
        (f) => ({
          name: f.name,
          category:
            selectedFolder === "All Files" ? "CAD Models" : selectedFolder,
          size: `${(f.size / 1024).toFixed(1)} KB`,
          modified: "Just now",
        }),
      );
      setFiles((prev) => [...newFiles, ...prev]);
    }
  };

  return (
    <div
      data-testid="page-file-vault"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "var(--color-neutral)",
        color: "var(--color-primary)",
        overflow: "hidden",
      }}
      className="animate-fade-in-up"
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "var(--space-xl)",
          borderBottom: "1px solid var(--color-border)",
          backgroundColor: "var(--color-surface-subtle)",
        }}
      >
        <div>
          <h1
            style={{
              fontSize: "1.8rem",
              fontFamily: "var(--font-ui)",
              fontWeight: 700,
              color: "var(--color-primary)",
            }}
          >
            Workspace File Vault
          </h1>
          <p
            style={{
              fontSize: "0.9rem",
              color: "var(--color-secondary)",
              marginTop: "var(--space-xs)",
            }}
          >
            Secure local-first document storage for design sheets, compliance
            records, calculations, and FEA outputs.
          </p>
        </div>

        <button
          style={{
            padding: "var(--space-md) var(--space-lg)",
            backgroundColor: "var(--color-secondary)",
            color: "var(--color-surface-subtle)",
            fontWeight: 600,
            borderRadius: "var(--radius-lg)",
            border: "none",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-sm)",
            transition: "all var(--transition-smooth)",
            boxShadow: "var(--shadow-glow)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = "var(--shadow-glow-active)";
            e.currentTarget.style.transform = "translateY(-1px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = "var(--shadow-glow)";
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          <PlusIcon size={16} /> Import Document
        </button>
      </div>

      {/* Main vault area */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Categories / Folders Sidebar */}
        <div
          style={{
            width: "240px",
            borderRight: "1px solid var(--color-border)",
            backgroundColor: "var(--color-surface-subtle)",
            padding: "var(--space-xl) var(--space-lg)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-md)",
          }}
        >
          <span
            style={{
              fontSize: "0.8rem",
              textTransform: "uppercase",
              fontWeight: 600,
              color: "var(--color-secondary)",
              letterSpacing: "1px",
              paddingLeft: "var(--space-md)",
            }}
          >
            Vault Folders
          </span>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
            }}
          >
            {folders.map((fld) => (
              <button
                key={fld}
                onClick={() => setSelectedFolder(fld)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-md)",
                  textAlign: "left",
                  padding: "var(--space-md)",
                  borderRadius: "var(--radius-lg)",
                  fontSize: "0.9rem",
                  fontWeight: selectedFolder === fld ? 600 : 500,
                  backgroundColor:
                    selectedFolder === fld
                      ? "rgba(56, 189, 248, 0.08)"
                      : "transparent",
                  color:
                    selectedFolder === fld
                      ? "var(--color-secondary)"
                      : "rgba(255, 255, 255, 0.6)",
                  cursor: "pointer",
                  borderLeft:
                    selectedFolder === fld
                      ? "3px solid var(--color-secondary)"
                      : "3px solid transparent",
                  transition: "all var(--transition-smooth)",
                }}
                onMouseEnter={(e) => {
                  if (selectedFolder !== fld) {
                    e.currentTarget.style.color = "var(--color-primary)";
                    e.currentTarget.style.backgroundColor =
                      "rgba(255, 255, 255, 0.02)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedFolder !== fld) {
                    e.currentTarget.style.color = "rgba(255, 255, 255, 0.6)";
                    e.currentTarget.style.backgroundColor = "transparent";
                  }
                }}
              >
                <FolderIcon size={16} />
                <span>{fld}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content area: Upload Zone + File List */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflowY: "auto",
            padding: "var(--space-xl)",
            gap: "var(--space-xl)",
          }}
        >
          {/* Dropzone Container */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
              padding: "var(--space-2xl)",
              borderRadius: "var(--radius-lg)",
              border: isDragging
                ? "2px dashed var(--color-secondary)"
                : "2px dashed var(--color-border)",
              backgroundColor: isDragging
                ? "rgba(56, 189, 248, 0.05)"
                : "var(--color-surface)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "var(--space-md)",
              transition: "all var(--transition-smooth)",
              cursor: "pointer",
              boxShadow: isDragging ? "var(--shadow-glow)" : "none",
              textAlign: "center",
            }}
          >
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "50%",
                backgroundColor: "var(--color-surface-subtle)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--color-secondary)",
              }}
            >
              <PlusIcon size={24} />
            </div>
            <div>
              <p
                style={{
                  fontWeight: 600,
                  fontSize: "1rem",
                  color: "var(--color-primary)",
                }}
              >
                Drag and drop files to import into {selectedFolder}
              </p>
              <p
                style={{
                  fontSize: "0.85rem",
                  color: "var(--color-secondary)",
                  marginTop: "4px",
                }}
              >
                Files will be indexed and securely stored in your local-first
                wright database
              </p>
            </div>
          </div>

          {/* Files List */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-md)",
            }}
          >
            <h3
              style={{
                fontSize: "1.1rem",
                fontWeight: 600,
                color: "var(--color-primary)",
              }}
            >
              Recent Vault Files
            </h3>

            {filteredFiles.length === 0 ? (
              <div
                style={{
                  padding: "24px",
                  textAlign: "center",
                  color: "var(--color-secondary)",
                  backgroundColor: "var(--color-surface)",
                  borderRadius: "var(--radius-lg)",
                  border: "1px solid var(--color-border)",
                }}
              >
                No files found in {selectedFolder}.
              </div>
            ) : (
              <div
                style={{
                  overflow: "hidden",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-lg)",
                }}
              >
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: "0.9rem",
                  }}
                >
                  <thead>
                    <tr
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        borderBottom: "1px solid var(--color-border)",
                        textAlign: "left",
                      }}
                    >
                      <th
                        style={{
                          padding: "12px var(--space-lg)",
                          color: "var(--color-primary)",
                          fontWeight: 600,
                        }}
                      >
                        File Name
                      </th>
                      <th
                        style={{
                          padding: "12px var(--space-lg)",
                          color: "var(--color-primary)",
                          fontWeight: 600,
                        }}
                      >
                        Category
                      </th>
                      <th
                        style={{
                          padding: "12px var(--space-lg)",
                          color: "var(--color-primary)",
                          fontWeight: 600,
                        }}
                      >
                        Size
                      </th>
                      <th
                        style={{
                          padding: "12px var(--space-lg)",
                          color: "var(--color-primary)",
                          fontWeight: 600,
                        }}
                      >
                        Modified
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFiles.map((file, i) => (
                      <tr
                        key={i}
                        style={{
                          borderBottom:
                            i === filteredFiles.length - 1
                              ? "none"
                              : "1px solid var(--color-border)",
                          backgroundColor: "var(--color-surface)",
                          transition: "background-color var(--transition-fast)",
                        }}
                        onMouseEnter={(e) =>
                          (e.currentTarget.style.backgroundColor =
                            "var(--color-surface-hover)")
                        }
                        onMouseLeave={(e) =>
                          (e.currentTarget.style.backgroundColor =
                            "var(--color-surface)")
                        }
                      >
                        <td
                          style={{
                            padding: "14px var(--space-lg)",
                            display: "flex",
                            alignItems: "center",
                            gap: "var(--space-md)",
                            fontWeight: 500,
                            color: "var(--color-primary)",
                          }}
                        >
                          <FileIcon
                            size={16}
                            style={{ color: "var(--color-secondary)" }}
                          />
                          <span>{file.name}</span>
                        </td>
                        <td
                          style={{
                            padding: "14px var(--space-lg)",
                            color: "rgba(255, 255, 255, 0.7)",
                          }}
                        >
                          {file.category}
                        </td>
                        <td
                          style={{
                            padding: "14px var(--space-lg)",
                            color: "rgba(255, 255, 255, 0.7)",
                            fontFamily: "var(--font-mono)",
                          }}
                        >
                          {file.size}
                        </td>
                        <td
                          style={{
                            padding: "14px var(--space-lg)",
                            color: "var(--color-secondary)",
                          }}
                        >
                          {file.modified}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default FileVaultPage;
