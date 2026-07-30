import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthGate } from "../src/components/common/AuthGate";

vi.mock("../src/services/host-adapter", () => ({
  hostAdapter: {
    mode: "browser",
    getApiBaseUrl: () => "",
  },
}));

describe("AuthGate", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("asks for the local access token when auth is enforced and no session exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(
            JSON.stringify({ auth_required: true, authenticated: false }),
            { status: 200 },
          ),
        ),
    );

    render(
      <AuthGate>
        <div>Dashboard</div>
      </AuthGate>,
    );

    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
    expect(await screen.findByText("Unlock Wright")).toBeInTheDocument();
  });

  it("exchanges the entered token and hides the prompt", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ auth_required: true, authenticated: false }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthGate>
        <div>Dashboard</div>
      </AuthGate>,
    );

    await userEvent.type(
      await screen.findByLabelText("Access Token"),
      "abc123",
    );
    await userEvent.click(screen.getByRole("button", { name: "Unlock" }));

    await waitFor(() =>
      expect(screen.queryByText("Unlock Wright")).not.toBeInTheDocument(),
    );
    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringMatching(/\/api\/auth\/session$/),
      {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: "abc123" }),
      },
    );
  });
});
