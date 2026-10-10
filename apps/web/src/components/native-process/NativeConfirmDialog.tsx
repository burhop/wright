import { useEffect, useId, useRef } from "react";
export function NativeConfirmDialog({
  title,
  children,
  stay,
  proceed,
  stayLabel = "Stay and keep editing",
  proceedLabel = "Continue",
  proceedDisabled = false,
}: {
  title: string;
  children: React.ReactNode;
  stay: () => void;
  proceed: () => void;
  stayLabel?: string;
  proceedLabel?: string;
  proceedDisabled?: boolean;
}) {
  const titleId = useId();
  const dialog = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const original =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    dialog.current?.querySelector<HTMLButtonElement>("button")?.focus();
    function keydown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        stay();
      }
      if (event.key !== "Tab") return;
      const controls = Array.from(
        dialog.current?.querySelectorAll<HTMLButtonElement>(
          "button:not(:disabled)",
        ) ?? [],
      );
      const first = controls[0],
        last = controls.at(-1);
      if (
        event.shiftKey &&
        (document.activeElement === first ||
          !dialog.current?.contains(document.activeElement))
      ) {
        event.preventDefault();
        last?.focus();
      } else if (
        !event.shiftKey &&
        (document.activeElement === last ||
          !dialog.current?.contains(document.activeElement))
      ) {
        event.preventDefault();
        first?.focus();
      }
    }
    document.addEventListener("keydown", keydown, true);
    return () => {
      document.removeEventListener("keydown", keydown, true);
      original?.focus();
    };
  }, [stay]);
  return (
    <div
      ref={dialog}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      className="native-dialog"
    >
      <div>
        <h2 id={titleId}>{title}</h2>
        {children}
        <button data-testid="native-stay" onClick={stay}>
          {stayLabel}
        </button>
        <button
          data-testid="native-leave"
          onClick={proceed}
          disabled={proceedDisabled}
        >
          {proceedLabel}
        </button>
      </div>
    </div>
  );
}
