import type { ReactNode } from "react";

/** Desktop iframes may permit scripts but prohibit native form submission. */
export function NativeActionForm({
  children,
  onAction,
}: {
  readonly children: ReactNode;
  readonly onAction: () => void;
}) {
  const act = (form: HTMLFormElement, button?: HTMLButtonElement) => {
    const submitter =
      button ??
      Array.from(form.querySelectorAll("button")).find(
        (item) => item.type === "submit" && !item.disabled,
      );
    if (!submitter || submitter.disabled || !form.reportValidity()) return;
    onAction();
  };
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        act(event.currentTarget);
      }}
      onClick={(event) => {
        const button =
          event.target instanceof Element
            ? event.target.closest("button")
            : null;
        if (
          !button ||
          button.type !== "submit" ||
          button.form !== event.currentTarget
        )
          return;
        event.preventDefault();
        act(event.currentTarget, button);
      }}
      onKeyDown={(event) => {
        if (
          event.key !== "Enter" ||
          event.nativeEvent.isComposing ||
          !(event.target instanceof HTMLInputElement)
        )
          return;
        event.preventDefault();
        act(event.currentTarget);
      }}
    >
      {children}
    </form>
  );
}
