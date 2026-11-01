import { NativeActionForm } from "./NativeActionForm";
import { useRef, useState } from "react";
import { CompactEncrypt, importJWK, type JWK } from "jose";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

type CredentialCall = (
  name:
    | "wright_connection_credentials"
    | "wright_connection_credentials_form"
    | "wright_connection_credentials_save",
  args: Record<string, unknown>,
) => Promise<CallToolResult>;
interface Scope {
  workspace_id: string;
  session_id: string;
  plan_id: string;
  plan_digest: string;
}
interface Field {
  name: string;
  label: string;
  description?: string;
  required: boolean;
}
interface Status extends Scope {
  server_id: string;
  active: boolean;
  fields: Field[];
  configured: Record<string, boolean>;
}
interface Form {
  form_id: string;
  public_key: JWK;
  expires_in: number;
  alg: string;
  enc: string;
}

export function NativeCredentials({
  scope,
  call,
}: {
  readonly scope: Scope;
  readonly call: CredentialCall;
}) {
  const [status, setStatus] = useState<Status>();
  const [form, setForm] = useState<Form>();
  const [values, setValues] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const busy = useRef(false);
  const expires = useRef(0);
  const [needsRead, setNeedsRead] = useState(false);
  function confirmed(result: CallToolResult): Status {
    const data = result.structuredContent as unknown as Status | undefined;
    if (
      result.isError ||
      !data ||
      data.workspace_id !== scope.workspace_id ||
      data.session_id !== scope.session_id ||
      data.plan_id !== scope.plan_id ||
      data.plan_digest !== scope.plan_digest ||
      typeof data.server_id !== "string" ||
      !Array.isArray(data.fields) ||
      typeof data.configured !== "object" ||
      !data.configured ||
      data.fields.length > 32 ||
      data.fields.some(
        (field) =>
          typeof field.name !== "string" ||
          typeof field.label !== "string" ||
          typeof data.configured[field.name] !== "boolean",
      )
    )
      throw Error("Unconfirmed credential subject");
    return data;
  }
  async function load(open: boolean) {
    if (busy.current || (open && needsRead)) return;
    busy.current = true;
    setPending(true);
    setValues({});
    setForm(undefined);
    try {
      const result = await call(
        open
          ? "wright_connection_credentials_form"
          : "wright_connection_credentials",
        open
          ? { ...scope }
          : {
              workspace_id: scope.workspace_id,
              session_id: scope.session_id,
              plan_id: scope.plan_id,
            },
      );
      const data = confirmed(result);
      setStatus(data);
      if (open) {
        const candidate = result._meta?.["wright/credential-form"] as
          Form | undefined;
        if (
          !candidate ||
          candidate.alg !== "RSA-OAEP-256" ||
          candidate.enc !== "A256GCM" ||
          typeof candidate.form_id !== "string" ||
          candidate.public_key?.kty !== "RSA" ||
          candidate.public_key.d ||
          !Number.isFinite(candidate.expires_in) ||
          candidate.expires_in <= 0 ||
          candidate.expires_in > 300
        )
          throw Error("Unsupported credential form");
        expires.current = Date.now() + candidate.expires_in * 1000;
        setForm(candidate);
        setMessage(
          "Enter only missing fields. Existing values are never displayed or replaced.",
        );
      } else {
        setNeedsRead(false);
        setMessage(
          "Configured status read. This does not confirm the value of an earlier uncertain save.",
        );
      }
    } catch {
      setMessage(
        open
          ? "Credential form unavailable. Stop an active provider first. Already configured values cannot be replaced here."
          : "Credential status could not be confirmed.",
      );
    } finally {
      busy.current = false;
      setPending(false);
    }
  }
  async function save() {
    if (busy.current || !form || !status) return;
    busy.current = true;
    setPending(true);
    setValues({});
    setForm(undefined);
    let submitted = false;
    try {
      if (Date.now() >= expires.current) throw Error("Expired form");
      const supplied = Object.fromEntries(
        Object.entries(values).filter(([, value]) => value.trim()),
      );
      const key = await importJWK(form.public_key, "RSA-OAEP-256");
      const ciphertext = await new CompactEncrypt(
        new TextEncoder().encode(
          JSON.stringify({ form_id: form.form_id, values: supplied }),
        ),
      )
        .setProtectedHeader({ alg: "RSA-OAEP-256", enc: "A256GCM" })
        .encrypt(key);
      // Plaintext stays in this form and Wright's existing secret owner. The
      // desktop tool boundary receives only a one-use encrypted envelope.
      submitted = true;
      const result = await call("wright_connection_credentials_save", {
        ...scope,
        form_id: form.form_id,
        ciphertext,
      });
      const data = confirmed(result);
      if (data.server_id !== status.server_id) throw Error("Changed server");
      setStatus(data);
      setMessage(
        "Credentials saved. Check the provider connection before enabling it; no tools were granted.",
      );
    } catch {
      setNeedsRead(submitted);
      setMessage(
        submitted
          ? "Save outcome is unconfirmed. Read credential status before opening another form. No save was repeated."
          : "Encrypted credential entry is unavailable or expired. Nothing was submitted; reopen the form.",
      );
    } finally {
      busy.current = false;
      setPending(false);
    }
  }
  const fields =
    status?.fields.filter((field) => !status.configured[field.name]) ?? [];
  return (
    <details
      onToggle={(event) => {
        if (!event.currentTarget.open) {
          setValues({});
          setForm(undefined);
        }
      }}
    >
      <summary>API keys and configuration values</summary>
      <p>
        Use provider sign-in above for OAuth. Enter API keys only in this form,
        never in chat. Values are encrypted before leaving the form and stored
        by Wright.
      </p>
      <button disabled={pending} onClick={() => void load(false)}>
        Read credential status
      </button>
      <button disabled={pending || needsRead} onClick={() => void load(true)}>
        Enter missing credentials
      </button>
      {status?.fields.map((field) => (
        <p key={field.name}>
          {field.label}:{" "}
          {status.configured[field.name] ? "Configured" : "Missing"}
        </p>
      ))}
      {form && (
        <NativeActionForm
          onAction={() => {
            void save();
          }}
        >
          {fields.map((field) => (
            <label key={field.name}>
              {field.label}
              <input
                type="password"
                autoComplete="off"
                name={field.name}
                required={field.required}
                maxLength={4096}
                value={values[field.name] ?? ""}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    [field.name]: event.target.value,
                  }))
                }
              />
              {field.description && <small>{field.description}</small>}
            </label>
          ))}
          <button disabled={pending || !fields.length} type="submit">
            Save credentials
          </button>
        </NativeActionForm>
      )}
      {message && <p role="status">{message}</p>}
    </details>
  );
}
