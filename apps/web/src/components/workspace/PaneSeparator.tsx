import { useRef, type KeyboardEvent, type PointerEvent } from "react";

interface Props {
  readonly valueBasisPoints: number;
  readonly minimumBasisPoints: number;
  readonly maximumBasisPoints: number;
  readonly onChange: (valueBasisPoints: number) => void;
  readonly chatPosition?: "left" | "right";
}

const clamp = (value: number, minimum: number, maximum: number) =>
  Math.min(maximum, Math.max(minimum, Math.round(value)));

export function PaneSeparator({
  valueBasisPoints,
  minimumBasisPoints,
  maximumBasisPoints,
  onChange,
  chatPosition = "right",
}: Props) {
  const separatorRef = useRef<HTMLDivElement>(null);

  const change = (value: number) =>
    onChange(clamp(value, minimumBasisPoints, maximumBasisPoints));

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    let value: number | undefined;
    switch (event.key) {
      case "ArrowRight":
        value = valueBasisPoints + 200;
        break;
      case "ArrowLeft":
        value = valueBasisPoints - 200;
        break;
      case "PageUp":
        value = valueBasisPoints + 1000;
        break;
      case "PageDown":
        value = valueBasisPoints - 1000;
        break;
      case "Home":
        value = minimumBasisPoints;
        break;
      case "End":
        value = maximumBasisPoints;
        break;
    }
    if (value === undefined) return;
    event.preventDefault();
    change(value);
  };

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!separatorRef.current?.hasPointerCapture(event.pointerId)) return;
    const container = separatorRef.current.parentElement?.getBoundingClientRect();
    if (!container || container.width <= 0) return;
    const fromLeft = clamp(
      ((event.clientX - container.left) / container.width) * 10_000,
      0,
      10_000,
    );
    change(chatPosition === "right" ? 10_000 - fromLeft : fromLeft);
  };

  return (
    <div
      ref={separatorRef}
      className="workspace-pane-separator"
      data-testid="surface-chat-separator"
      role="separator"
      aria-label="Resize chat and surface"
      aria-orientation="vertical"
      aria-valuemin={Math.round(minimumBasisPoints / 100)}
      aria-valuemax={Math.round(maximumBasisPoints / 100)}
      aria-valuenow={Math.round(valueBasisPoints / 100)}
      aria-valuetext={`Chat width ${Math.round(valueBasisPoints / 100)} percent`}
      tabIndex={0}
      onKeyDown={onKeyDown}
      onPointerDown={(event) => event.currentTarget.setPointerCapture(event.pointerId)}
      onPointerMove={onPointerMove}
      onPointerUp={(event) => event.currentTarget.releasePointerCapture(event.pointerId)}
    />
  );
}
