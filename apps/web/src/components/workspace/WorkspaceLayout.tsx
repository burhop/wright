import { forwardRef, type CSSProperties, type HTMLAttributes } from "react";

import {
  resolveWorkspaceLayout,
  type WorkspaceLayoutState,
} from "./workspace-layout";

interface Props extends HTMLAttributes<HTMLDivElement> {
  readonly layout: WorkspaceLayoutState;
  readonly paneContainerWidth: number;
  readonly leftSidebarWidth: number;
  readonly leftSidebarCollapsed: boolean;
  readonly chatCollapsed?: boolean;
  readonly resizing?: boolean;
  readonly adaptive?: boolean;
  readonly legacyChatWidth?: number;
}

export const WorkspaceLayout = forwardRef<HTMLDivElement, Props>(
  function WorkspaceLayout(
    {
      layout,
      paneContainerWidth,
      leftSidebarWidth,
      leftSidebarCollapsed,
      chatCollapsed = false,
      resizing = false,
      adaptive = true,
      legacyChatWidth = 360,
      style,
      className,
      children,
      ...attributes
    },
    ref,
  ) {
    const resolved = resolveWorkspaceLayout(layout, paneContainerWidth);
    const focus = layout.wideMode === "focus" && layout.mode !== "narrow";
    const narrow = layout.mode === "narrow";
    const chromeColumns =
      focus || narrow
        ? "0px 0px 0px"
        : `48px ${leftSidebarCollapsed ? "0px" : `${leftSidebarWidth}px`} ${leftSidebarCollapsed ? "0px" : "4px"}`;
    const paneColumns = narrow
      ? "minmax(0, 1fr)"
      : chatCollapsed
        ? "minmax(480px, 1fr) 0px 0px"
        : `minmax(480px, 1fr) ${resolved.separatorPixels}px ${resolved.chatPixels}px`;
    const legacyColumns = `48px ${leftSidebarCollapsed ? "0px" : `${leftSidebarWidth}px`} ${leftSidebarCollapsed ? "0px" : "4px"} 1fr ${chatCollapsed ? "0px" : "4px"} ${chatCollapsed ? "0px" : `${legacyChatWidth}px`}`;
    const layoutStyle: CSSProperties = {
      display: "grid",
      gridTemplateColumns: adaptive
        ? narrow
          ? paneColumns
          : `${chromeColumns} ${paneColumns}`
        : legacyColumns,
      height: "100%",
      width: "100%",
      backgroundColor: "var(--color-neutral)",
      color: "var(--color-primary)",
      overflow: "hidden",
      position: "relative",
      transition: resizing ? "none" : "grid-template-columns 0.15s ease-out",
      ...style,
    };

    return (
      <div
        ref={ref}
        className={`workspace-surfaces-layout ${className ?? ""}`.trim()}
        {...(adaptive
          ? {
              "data-layout-mode": layout.mode,
              "data-wide-layout-mode": layout.wideMode,
            }
          : {})}
        style={layoutStyle}
        {...attributes}
      >
        {children}
      </div>
    );
  },
);
