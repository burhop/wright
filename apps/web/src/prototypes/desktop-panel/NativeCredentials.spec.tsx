import { compactDecrypt, exportJWK, generateKeyPair } from "jose";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeCredentials } from "./NativeCredentials";
const { webcrypto } = await vi.importActual<{ webcrypto: Crypto }>(
  "node:crypto",
);
const scope = {
  workspace_id: "w",
  session_id: "s",
  plan_id: "p",
  plan_digest: "a".repeat(64),
};
const status = {
  ...scope,
  server_id: "provider",
  active: false,
  fields: [{ name: "KEY", label: "API key", required: true, secret: true }],
  configured: { KEY: false },
};
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("encrypts before the tool boundary and clears input without granting or validating tools", async () => {
  vi.stubGlobal("crypto", webcrypto);
  // Match Node WebCrypto/TextEncoder buffers in jsdom; real browsers use one realm.
  vi.stubGlobal("Uint8Array", new TextEncoder().encode("").constructor);
  const { publicKey, privateKey } = await generateKeyPair("RSA-OAEP-256");
  const form = {
    form_id: "f",
    public_key: await exportJWK(publicKey),
    expires_in: 300,
    alg: "RSA-OAEP-256",
    enc: "A256GCM",
  };
  const call = vi.fn(async (name: string) =>
    name === "wright_connection_credentials_form"
      ? {
          content: [],
          structuredContent: status,
          _meta: { "wright/credential-form": form },
        }
      : {
          content: [],
          structuredContent: { ...status, configured: { KEY: true } },
        },
  );
  render(<NativeCredentials scope={scope} call={call} />);
  expect(call).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("API keys and configuration values"));
  fireEvent.click(
    screen.getByRole("button", { name: "Enter missing credentials" }),
  );
  const input = await screen.findByLabelText("API key");
  expect(input).toHaveAttribute("type", "password");
  fireEvent.change(input, { target: { value: "synthetic-private-value" } });
  fireEvent.click(screen.getByRole("button", { name: "Save credentials" }));
  await screen.findByText(/Credentials saved/);
  expect(screen.queryByLabelText("API key")).toBeNull();
  expect(JSON.stringify(call.mock.calls)).not.toContain(
    "synthetic-private-value",
  );
  const args = (
    call.mock.calls as unknown as [string, Record<string, string>][]
  ).find(([name]) => name === "wright_connection_credentials_save")![1];
  const { plaintext } = await compactDecrypt(args.ciphertext, privateKey);
  expect(JSON.parse(new TextDecoder().decode(plaintext))).toEqual({
    form_id: "f",
    values: { KEY: "synthetic-private-value" },
  });
  expect(call.mock.calls.map(([name]) => name)).toEqual([
    "wright_connection_credentials_form",
    "wright_connection_credentials_save",
  ]);
});

it("reads status after an uncertain save and never repeats it", async () => {
  vi.stubGlobal("crypto", webcrypto);
  // Match Node WebCrypto/TextEncoder buffers in jsdom; real browsers use one realm.
  vi.stubGlobal("Uint8Array", new TextEncoder().encode("").constructor);
  const { publicKey } = await generateKeyPair("RSA-OAEP-256");
  const call = vi.fn(async (name: string) => {
    if (name === "wright_connection_credentials_save")
      throw Error("lost acknowledgement");
    return {
      content: [],
      structuredContent: status,
      _meta: {
        "wright/credential-form": {
          form_id: "f",
          public_key: await exportJWK(publicKey),
          expires_in: 300,
          alg: "RSA-OAEP-256",
          enc: "A256GCM",
        },
      },
    };
  });
  render(<NativeCredentials scope={scope} call={call} />);
  fireEvent.click(screen.getByText("API keys and configuration values"));
  fireEvent.click(
    screen.getByRole("button", { name: "Enter missing credentials" }),
  );
  fireEvent.change(await screen.findByLabelText("API key"), {
    target: { value: "synthetic-value" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save credentials" }));
  await screen.findByText(/Save outcome is unconfirmed/);
  expect(
    screen.getByRole("button", { name: "Enter missing credentials" }),
  ).toBeDisabled();
  fireEvent.click(
    screen.getByRole("button", { name: "Read credential status" }),
  );
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Enter missing credentials" }),
    ).toBeEnabled(),
  );
  expect(
    call.mock.calls.filter(
      ([name]) => name === "wright_connection_credentials_save",
    ),
  ).toHaveLength(1);
  expect(screen.queryByLabelText("API key")).toBeNull();
});

it("rejects another subject and clears fields when the form closes", async () => {
  vi.stubGlobal("crypto", webcrypto);
  // Match Node WebCrypto/TextEncoder buffers in jsdom; real browsers use one realm.
  vi.stubGlobal("Uint8Array", new TextEncoder().encode("").constructor);
  const { publicKey } = await generateKeyPair("RSA-OAEP-256");
  const call = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: { ...status, plan_digest: "b".repeat(64) },
  });
  render(<NativeCredentials scope={scope} call={call} />);
  const summary = screen.getByText("API keys and configuration values");
  fireEvent.click(summary);
  fireEvent.click(
    screen.getByRole("button", { name: "Enter missing credentials" }),
  );
  await screen.findByText(/Credential form unavailable/);
  expect(screen.queryByLabelText("API key")).toBeNull();
  call.mockResolvedValue({
    content: [],
    structuredContent: status,
    _meta: {
      "wright/credential-form": {
        form_id: "f",
        public_key: await exportJWK(publicKey),
        expires_in: 300,
        alg: "RSA-OAEP-256",
        enc: "A256GCM",
      },
    },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Enter missing credentials" }),
  );
  fireEvent.change(await screen.findByLabelText("API key"), {
    target: { value: "synthetic-value" },
  });
  fireEvent.click(summary);
  await waitFor(() => expect(screen.queryByLabelText("API key")).toBeNull());
  fireEvent.click(summary);
  expect(screen.queryByLabelText("API key")).toBeNull();
  expect(call.mock.calls).toHaveLength(2);
});

it("reports unavailable encryption without submitting plaintext or a save request", async () => {
  vi.stubGlobal("crypto", webcrypto);
  vi.stubGlobal("Uint8Array", new TextEncoder().encode("").constructor);
  const { publicKey } = await generateKeyPair("RSA-OAEP-256");
  const call = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: status,
    _meta: {
      "wright/credential-form": {
        form_id: "f",
        public_key: await exportJWK(publicKey),
        expires_in: 300,
        alg: "RSA-OAEP-256",
        enc: "A256GCM",
      },
    },
  });
  render(<NativeCredentials scope={scope} call={call} />);
  fireEvent.click(screen.getByText("API keys and configuration values"));
  fireEvent.click(
    screen.getByRole("button", { name: "Enter missing credentials" }),
  );
  fireEvent.change(await screen.findByLabelText("API key"), {
    target: { value: "synthetic-secret" },
  });
  vi.stubGlobal("crypto", {});
  fireEvent.click(screen.getByRole("button", { name: "Save credentials" }));
  await screen.findByText(
    /Encrypted credential entry is unavailable or expired/,
  );
  expect(call.mock.calls).toHaveLength(1);
  expect(JSON.stringify(call.mock.calls)).not.toContain("synthetic-secret");
});
