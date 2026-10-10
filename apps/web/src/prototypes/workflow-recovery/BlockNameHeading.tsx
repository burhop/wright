import { useEffect, useRef, useState } from "react";

type NameHeadingProps = {
  title: string;
  readOnly: boolean;
  onRename: (title: string) => boolean;
};

export function BlockNameHeading(props: NameHeadingProps) {
  return <EditableNameHeading {...props} kind="block" />;
}

export function WorkflowNameHeading(
  props: NameHeadingProps & { fileTitle: string },
) {
  return <EditableNameHeading {...props} kind="workflow" />;
}

function EditableNameHeading({
  title,
  readOnly,
  onRename,
  kind,
  fileTitle,
}: NameHeadingProps & {
  kind: "block" | "workflow";
  fileTitle?: string;
}) {
  const [draft, setDraft] = useState(title);
  const cancelled = useRef(false);
  useEffect(() => setDraft(title), [title]);
  const Heading = kind === "workflow" ? "h1" : "h2";

  return (
    <Heading aria-label={title} title={fileTitle}>
      <input
        className={`recovery-${kind}-name`}
        data-testid={`workflow-recovery-${kind}-name`}
        aria-label={kind === "workflow" ? "Workflow name" : "Block name"}
        title={
          readOnly ? title : `Rename ${kind}. Enter to apply; Escape to cancel.`
        }
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
      />
    </Heading>
  );
}
