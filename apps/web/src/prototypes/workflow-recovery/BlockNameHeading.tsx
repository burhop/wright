import { useEffect, useRef, useState } from "react";

export function BlockNameHeading({ title, readOnly, onRename }: {
  title: string;
  readOnly: boolean;
  onRename: (title: string) => boolean;
}) {
  const [draft, setDraft] = useState(title);
  const cancelled = useRef(false);
  useEffect(() => setDraft(title), [title]);

  return <h2 aria-label={title}><input
    className="recovery-block-name"
    data-testid="workflow-recovery-block-name"
    aria-label="Block name"
    title={readOnly ? title : "Rename block. Enter to apply; Escape to cancel."}
    value={draft}
    readOnly={readOnly}
    onChange={(event) => setDraft(event.target.value)}
    onFocus={(event) => event.target.select()}
    onBlur={() => {
      const name = draft.trim();
      if (!cancelled.current && !readOnly && name && name !== title) {
        if (!onRename(name)) setDraft(title);
        else setDraft(name);
      } else setDraft(title);
      cancelled.current = false;
    }}
    onKeyDown={(event) => {
      if (event.key === "Enter" || event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        cancelled.current = event.key === "Escape";
        event.currentTarget.blur();
      }
    }}
  /></h2>;
}
