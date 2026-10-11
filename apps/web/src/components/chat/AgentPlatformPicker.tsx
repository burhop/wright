interface AgentPlatformPickerProps {
  value: string;
  onChange: (value: string) => void;
}

export function AgentPlatformPicker({ value, onChange }: AgentPlatformPickerProps) {
  return (
    <label title={value === "codex" ? "Experimental Codex chats permit remaining native Codex tools. Process-UI authoring and workflow execution remain unavailable. Existing chats keep their agent." : "Default for new chats. Existing chats keep their agent."} style={{ fontSize: "0.65rem" }}>
      New chats
      <select aria-label="Agent for new chats" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="hermes">Hermes</option>
        <option value="codex">Codex (experimental)</option>
        {value !== "hermes" && value !== "codex" && <option value={value}>{value}</option>}
      </select>
    </label>
  );
}
