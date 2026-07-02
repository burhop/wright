import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ChatTranscript from "../src/components/chat/ChatTranscript";
import type { ChatSession, StreamActivityEntry } from "../src/store/types";

function makeSession(): ChatSession {
  return {
    sessionId: "session-1",
    title: "Test Session",
    messages: [],
    createdAt: 1000,
    updatedAt: 1000,
    isActive: true,
  };
}

describe("ChatTranscript", () => {
  it("renders expandable stream activity details", () => {
    const entries: StreamActivityEntry[] = [
      {
        id: "activity-1",
        kind: "status",
        title: "Hermes is preparing a response",
        detail: "Waiting for the first response event.",
        timestamp: 1000,
      },
      {
        id: "activity-2",
        kind: "tool",
        title: "Calling jarvisonshapemcp__list_documents",
        detail: '{"query":"bracket"}',
        timestamp: 2000,
      },
    ];

    render(
      <ChatTranscript
        session={makeSession()}
        isStreaming={true}
        streamActivity={entries}
        activeTool={{
          name: "jarvisonshapemcp__list_documents",
          preview: '{"query":"bracket"}',
        }}
      />,
    );

    expect(screen.getByTestId("stream-activity-panel")).toBeInTheDocument();
    expect(screen.getByText("Working")).toBeInTheDocument();
    expect(screen.queryByTestId("stream-activity-details")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /Working/i }));

    expect(screen.getByTestId("stream-activity-details")).toBeInTheDocument();
    expect(
      screen.getByText("Calling jarvisonshapemcp__list_documents"),
    ).toBeInTheDocument();
  });
  it("renders Hermes progress titles with tool and status details", () => {
    const entries: StreamActivityEntry[] = [
      {
        id: "activity-1",
        kind: "progress",
        title: "development: Running",
        detail: "Creating sketch geometry",
        timestamp: 1000,
      },
    ];

    render(
      <ChatTranscript
        session={makeSession()}
        isStreaming={true}
        streamActivity={entries}
      />,
    );

    expect(screen.getByText("development: Running")).toBeInTheDocument();
    expect(screen.getByText("Creating sketch geometry")).toBeInTheDocument();
  });

});
