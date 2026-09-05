import { useEffect, useRef } from "react";
export function NativeConfirmDialog({
  title,
  children,
  stay,
  proceed,
}: {
  title: string;
  children: React.ReactNode;
  stay: () => void;
  proceed: () => void;
}) {
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
        dialog.current?.querySelectorAll<HTMLButtonElement>("button") ?? [],
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
      aria-labelledby="native-leave-title"
      className="native-dialog"
    >
      <div>
        <h2 id="native-leave-title">{title}</h2>
        {children}
        <button data-testid="native-stay" onClick={stay}>
          Stay and keep editing
        </button>
        <button data-testid="native-leave" onClick={proceed}>
          Continue
        </button>
      </div>
    </div>
  );
}
