import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import definitionRaw from "../../../../src/wright_engineering/static/process-definitions/product-definition-v1.json?raw";
import recoveryFixturesRaw from "../../../../specs/078-process-definition-view/contracts/recovery-fixtures.json?raw";
import { ProcessDefinitionPage } from "../components/pages/ProcessDefinitionPage";
import { hostAdapter } from "../services/host-adapter";
import {
  PROCESS_DEFINITION_SOURCE_ID,
  type ProcessDefinitionError,
} from "../services/process-definition";

vi.mock("../services/host-adapter", () => ({
  hostAdapter: {
    getApiBaseUrl: () => "http://wright.local",
    fetch: vi.fn(),
  },
}));

interface RecoveryFixture {
  id: string;
  kind: "request_descriptor" | "payload";
  exact_text: string;
  sha256: string;
  expected_http_status: number;
  expected_code: ProcessDefinitionError["error_code"];
  expected_recovery: ProcessDefinitionError["recovery_class"];
}

const recoveryContract = JSON.parse(recoveryFixturesRaw) as {
  schema_version: string;
  encoding: string;
  fixtures: RecoveryFixture[];
};
const mockedFetch = vi.mocked(hostAdapter.fetch);

const recoveryCopy: Record<RecoveryFixture["id"], string> = {
  "missing-unavailable":
    "Enable the process-definition data or reinstall this Wright build.",
  "invalid-truncated-json":
    "Replace the local definition with a validated Wright process-definition artifact.",
  "unsupported-version":
    "Install a compatible Wright version before opening this definition.",
};

function errorResponse(fixture: RecoveryFixture): Response {
  return new Response(
    JSON.stringify({
      error_code: fixture.expected_code,
      message: `Unsafe server detail ${fixture.exact_text}`,
      recovery_class: fixture.expected_recovery,
      trace_id: `trace-${fixture.id}`,
      ...(fixture.expected_code === "PROCESS_DEFINITION_UNSUPPORTED_VERSION"
        ? { supported_schema_versions: ["1.0.0"] }
        : {}),
    }),
    { status: fixture.expected_http_status },
  );
}

function unverifiedEnvelope(): Record<string, unknown> {
  return {
    definition: JSON.parse(definitionRaw),
    source_kind: "packaged_fallback",
    source_id: PROCESS_DEFINITION_SOURCE_ID,
    source_sha256: "a".repeat(64),
    source_available: true,
    etag: "b".repeat(64),
    supported_schema_versions: ["1.0.0"],
  };
}

async function renderFailure(): Promise<HTMLElement> {
  render(
    <MemoryRouter>
      <ProcessDefinitionPage />
    </MemoryRouter>,
  );
  return screen.findByRole("alert");
}

function expectNoPartialOrMutationUi(): void {
  expect(screen.queryByTestId("process-definition-text")).toBeNull();
  expect(screen.queryByTestId("process-definition-diagram")).toBeNull();
  expect(screen.queryByTestId("process-definition-source-details")).toBeNull();
  expect(
    document.querySelector(
      "form, button, input, textarea, select, [contenteditable='true']",
    ),
  ).toBeNull();
}

describe.sequential("ProcessDefinitionPage closed recovery", () => {
  beforeEach(() => mockedFetch.mockReset());

  it("binds the three frozen recovery fixtures to exact UTF-8 digests", async () => {
    expect(recoveryContract.schema_version).toBe("1.0.0");
    expect(recoveryContract.encoding).toBe("UTF-8 without BOM");
    expect(recoveryContract.fixtures.map(({ id }) => id)).toEqual([
      "missing-unavailable",
      "invalid-truncated-json",
      "unsupported-version",
    ]);

    for (const fixture of recoveryContract.fixtures) {
      const bytes = new TextEncoder().encode(fixture.exact_text);
      const digest = await crypto.subtle.digest("SHA-256", bytes);
      expect(
        Array.from(new Uint8Array(digest), (byte) =>
          byte.toString(16).padStart(2, "0"),
        ).join(""),
      ).toBe(fixture.sha256);
    }
  });

  it.each(recoveryContract.fixtures)(
    "renders closed support-safe recovery for $id",
    async (fixture) => {
      mockedFetch.mockResolvedValue(errorResponse(fixture));

      const alert = await renderFailure();

      expect(alert).toHaveTextContent(fixture.expected_code);
      expect(alert).toHaveTextContent(PROCESS_DEFINITION_SOURCE_ID);
      expect(alert).toHaveTextContent(recoveryCopy[fixture.id]);
      expect(alert).toHaveTextContent(`trace-${fixture.id}`);
      expect(alert).not.toHaveTextContent(fixture.exact_text);
      expect(alert).not.toHaveTextContent("Unsafe server detail");
      if (fixture.id === "unsupported-version") {
        expect(
          screen.getByTestId("process-definition-supported-versions"),
        ).toHaveTextContent("1.0.0");
      } else {
        expect(
          screen.queryByTestId("process-definition-supported-versions"),
        ).toBeNull();
      }
      expect(
        screen.getByTestId("process-definition-return-dashboard"),
      ).toHaveAttribute("href", "/");
      expectNoPartialOrMutationUi();
      expect(mockedFetch).toHaveBeenCalledTimes(1);
      const [url, init] = mockedFetch.mock.calls[0]!;
      expect(url).toBe(
        "http://wright.local/api/process-definitions/product-definition-v1",
      );
      expect(init).toMatchObject({ headers: {}, cache: "no-cache" });
      expect(init).not.toHaveProperty("body");
      expect(init).not.toHaveProperty("method");
      expect(JSON.stringify(mockedFetch.mock.calls)).not.toContain(
        fixture.exact_text,
      );
    },
  );

  it("maps identity drift to exact-artifact recovery without partial content", async () => {
    const envelope = unverifiedEnvelope();
    const definition = envelope.definition as Record<string, unknown>;
    definition.title = "Untrusted changed title";
    mockedFetch.mockResolvedValue(
      new Response(JSON.stringify(envelope), {
        status: 200,
        headers: { etag: `"${"b".repeat(64)}"` },
      }),
    );

    const alert = await renderFailure();

    expect(alert).toHaveTextContent("PROCESS_DEFINITION_IDENTITY_MISMATCH");
    expect(alert).toHaveTextContent(
      "Reinstall the exact Wright artifact that supplied this process definition.",
    );
    expect(alert).not.toHaveTextContent("Untrusted changed title");
    expectNoPartialOrMutationUi();
  });

  it.each([
    {
      name: "missing schema version",
      mutate: (envelope: Record<string, unknown>) => {
        delete (envelope.definition as Record<string, unknown>).schema_version;
      },
    },
    {
      name: "non-text schema version",
      mutate: (envelope: Record<string, unknown>) => {
        (envelope.definition as Record<string, unknown>).schema_version = 99;
      },
    },
    {
      name: "malformed supported versions",
      mutate: (envelope: Record<string, unknown>) => {
        envelope.supported_schema_versions = [];
      },
    },
  ])(
    "classifies $name as invalid rather than unsupported",
    async ({ mutate }) => {
      const envelope = unverifiedEnvelope();
      mutate(envelope);
      mockedFetch.mockResolvedValue(
        new Response(JSON.stringify(envelope), {
          status: 200,
          headers: { etag: `"${"b".repeat(64)}"` },
        }),
      );

      const alert = await renderFailure();

      expect(alert).toHaveTextContent("PROCESS_DEFINITION_INVALID");
      expect(alert).not.toHaveTextContent(
        "PROCESS_DEFINITION_UNSUPPORTED_VERSION",
      );
      expect(
        screen.queryByTestId("process-definition-supported-versions"),
      ).toBeNull();
      expectNoPartialOrMutationUi();
    },
  );

  it.each([
    {
      name: "closed 503",
      response: new Response(
        JSON.stringify({
          error_code: "PROCESS_DEFINITION_READ_FAILED",
          message:
            "C:\\private\\definition.json https://bad.example secret-token Traceback",
          recovery_class: "inspect_local_data_root",
          trace_id: "C:\\private\\trace",
        }),
        { status: 503 },
      ),
    },
    {
      name: "malformed success",
      response: new Response('{"definition":', { status: 200 }),
    },
  ])("renders a bounded static failure for $name", async ({ response }) => {
    mockedFetch.mockResolvedValue(response);

    const alert = await renderFailure();

    expect(alert).not.toHaveTextContent("private");
    expect(alert).not.toHaveTextContent("bad.example");
    expect(alert).not.toHaveTextContent("secret-token");
    expect(alert).not.toHaveTextContent("Traceback");
    expect(screen.queryByTestId("process-definition-trace-id")).toBeNull();
    expectNoPartialOrMutationUi();
  });
});
