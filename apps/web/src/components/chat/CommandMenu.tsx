import React, { useEffect, useRef } from "react";
import type { AgentCommand } from "../../services/agent-service";

interface CommandMenuProps {
  commands: AgentCommand[];
  filter: string;
  prefix: string;
  onSelect: (command: AgentCommand) => void;
  position: { top: number; left: number };
}

export function CommandMenu({
  commands,
  filter,
  prefix,
  onSelect,
  position,
}: CommandMenuProps) {
  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.prefix === prefix &&
      cmd.name.toLowerCase().startsWith(filter.toLowerCase()),
  );

  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSelectedIndex(0);
  }, [filter, prefix]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (filteredCommands.length === 0) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(
          (prev) =>
            (prev - 1 + filteredCommands.length) % filteredCommands.length,
        );
      } else if (e.key === "Enter") {
        e.preventDefault();
        onSelect(filteredCommands[selectedIndex]);
      }
    };

    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [filteredCommands, selectedIndex, onSelect]);

  if (filteredCommands.length === 0) return null;

  return (
    <div
      ref={containerRef}
      style={{
        position: "fixed",
        top: position.top,
        left: position.left,
        transform: "translateY(-100%)",
        marginTop: "-8px",
        backgroundColor: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-xs)",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
        zIndex: 1000,
        minWidth: "200px",
        maxHeight: "300px",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        gap: "2px",
      }}
    >
      {filteredCommands.map((cmd, index) => (
        <button
          key={cmd.name}
          onClick={() => onSelect(cmd)}
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            padding: "var(--space-sm)",
            backgroundColor:
              index === selectedIndex
                ? "var(--color-surface-hover)"
                : "transparent",
            border: "none",
            borderRadius: "var(--radius-sm)",
            cursor: "pointer",
            width: "100%",
            textAlign: "left",
          }}
          onMouseEnter={() => setSelectedIndex(index)}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-xs)",
            }}
          >
            <span style={{ fontWeight: "bold", color: "var(--color-primary)" }}>
              {cmd.prefix}
              {cmd.name}
            </span>
          </div>
          <span
            style={{
              fontSize: "0.75rem",
              color: "var(--color-secondary)",
              marginTop: "2px",
            }}
          >
            {cmd.description}
          </span>
        </button>
      ))}
    </div>
  );
}
