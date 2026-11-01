import { NativeActionForm } from "./NativeActionForm";
import { useEffect, useMemo, useState } from "react";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";
import {
  NativeSettingsClient,
  publicGitRemote,
  type WorkspaceSettings,
  type WorkspaceSettingsChanges,
} from "./native-settings-client";

const MiB = 1024 * 1024;
type Form = {
  workspace_prompt: string;
  git_remote_url: string;
  git_username: string;
  git_large_file_threshold: string;
};
function formFor(saved: WorkspaceSettings): Form {
  return {
    workspace_prompt: saved.workspace_prompt ?? "",
    git_remote_url: saved.git_remote_url ?? "",
    git_username: saved.git_username ?? "",
    git_large_file_threshold:
      saved.git_large_file_threshold === null
        ? ""
        : String(saved.git_large_file_threshold / MiB),
  };
}
export function NativeWorkspaceSettings({
  workspace,
  call,
  onDirty,
}: {
  readonly workspace: DesktopWorkspace;
  readonly call: HomeCall;
  readonly onDirty: (dirty: boolean) => void;
}) {
  const client = useMemo(
    () => new NativeSettingsClient(workspace, call),
    [workspace, call],
  );
  const [base, setBase] = useState<WorkspaceSettings>();
  const [form, setForm] = useState<Form>();
  const [touched, setTouched] = useState<Partial<Record<keyof Form, true>>>({});
  const [observed, setObserved] = useState<WorkspaceSettings>();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [blocked, setBlocked] = useState(false);
  const [message, setMessage] = useState("Reading workspace settings…");
  const dirty = Object.keys(touched).length > 0;
  useEffect(() => {
    let active = true;
    void client
      .read()
      .then((saved) => {
        if (!active) return;
        setBase(saved);
        setForm(formFor(saved));
        setMessage("");
      })
      .catch(() => {
        if (active)
          setMessage("Settings could not be read. Try Read saved settings.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [client]);
  useEffect(() => {
    onDirty(dirty || saving || client.requiresRead);
  }, [onDirty, dirty, saving, client, message]);
  function edit(key: keyof Form, value: string) {
    setForm((current) => (current ? { ...current, [key]: value } : current));
    setTouched((current) => ({ ...current, [key]: true }));
  }
  function replace(saved: WorkspaceSettings) {
    client.accept(saved);
    setBase(saved);
    setForm(formFor(saved));
    setTouched({});
    setObserved(undefined);
    setBlocked(false);
  }
  async function read() {
    const uncertain = client.requiresRead;
    setLoading(true);
    try {
      const saved = await client.read();
      if (!form || (uncertain && !client.requiresRead)) {
        replace(saved);
        setMessage(
          uncertain
            ? "Saved settings match your requested values. No write was repeated."
            : "Saved settings loaded.",
        );
      } else {
        setObserved(saved);
        setMessage(
          client.requiresRead
            ? "The earlier save remains unconfirmed. Your edit is preserved; no write was repeated."
            : "Saved settings read. Choose which values to keep; your edit is preserved.",
        );
      }
    } catch {
      setMessage(
        "Saved settings are unavailable. Your edit is preserved; no save was repeated.",
      );
    } finally {
      setLoading(false);
    }
  }
  async function save() {
    if (!form || !base || saving || blocked || client.requiresRead) return;
    const changes: WorkspaceSettingsChanges = {};
    for (const key of Object.keys(touched) as (keyof Form)[]) {
      if (key === "git_large_file_threshold") {
        const bytes = form[key].trim()
          ? Math.round(Number(form[key]) * MiB)
          : null;
        if (bytes !== null && (!Number.isSafeInteger(bytes) || bytes < 1)) {
          setMessage(
            "Choose a positive large-file threshold or leave it blank for the Wright default.",
          );
          return;
        }
        changes[key] = bytes;
      } else changes[key] = form[key] || null;
    }
    if (changes.git_remote_url && !publicGitRemote(changes.git_remote_url)) {
      setMessage(
        "Use HTTPS or SSH without passwords, tokens, query or fragment.",
      );
      return;
    }
    if (
      changes.workspace_prompt &&
      (changes.workspace_prompt.includes("\0") ||
        new TextEncoder().encode(changes.workspace_prompt).length > 131072)
    ) {
      setMessage(
        "Workflow context must be text without NUL characters, up to128KiB.",
      );
      return;
    }
    setSaving(true);
    setMessage("Saving workspace settings…");
    try {
      replace(await client.save(changes));
      setMessage(
        "Settings saved. Workflow context applies to newly created workflows.",
      );
    } catch (error) {
      setBlocked(true);
      setMessage(
        error instanceof Error
          ? error.message
          : "Save is unconfirmed. Read saved settings.",
      );
    } finally {
      setSaving(false);
    }
  }
  const locked = saving || loading || client.requiresRead;
  return (
    <section
      className="native-workspace-settings"
      aria-label="Workspace settings"
    >
      <h2>Workspace settings</h2>
      <p>
        Default context is embedded in new workflows. Saved workflows keep their
        accepted instructions. Use this desktop conversation to work with them.
      </p>
      {form && (
        <NativeActionForm
          onAction={() => {
            void save();
          }}
        >
          <label htmlFor="wright-workspace-context">
            Default workflow context
          </label>
          <textarea
            id="wright-workspace-context"
            value={form.workspace_prompt}
            disabled={locked}
            onChange={(event) => edit("workspace_prompt", event.target.value)}
            maxLength={131072}
          />
          <details>
            <summary>Git settings</summary>
            <p>
              Settings only. Saving does not push, pull or contact a repository.
              Credentials stay in Wright’s external authentication setup.
            </p>
            {base?.remote_hidden && (
              <p>
                A legacy or private remote is configured outside this panel.
                Leave this field untouched to preserve it; edit only to replace
                it.
              </p>
            )}
            <label htmlFor="wright-git-remote">Git remote URL</label>
            <input
              id="wright-git-remote"
              value={form.git_remote_url}
              disabled={locked}
              onChange={(event) => edit("git_remote_url", event.target.value)}
              maxLength={2048}
            />
            <label htmlFor="wright-git-user">Git username</label>
            <input
              id="wright-git-user"
              value={form.git_username}
              disabled={locked}
              onChange={(event) => edit("git_username", event.target.value)}
              maxLength={256}
            />
            <label htmlFor="wright-git-threshold">
              Large-file threshold (MiB)
            </label>
            <input
              id="wright-git-threshold"
              type="number"
              step="any"
              min="0.000001"
              placeholder="Wright default: 10"
              value={form.git_large_file_threshold}
              disabled={locked}
              onChange={(event) =>
                edit("git_large_file_threshold", event.target.value)
              }
            />
          </details>
          <button
            type="submit"
            disabled={!dirty || saving || blocked || client.requiresRead}
          >
            {saving ? "Saving…" : "Save settings"}
          </button>
          <button
            type="button"
            disabled={locked || !dirty}
            onClick={() => {
              if (base) replace(base);
              setMessage("Local settings edit discarded.");
            }}
          >
            Discard edit
          </button>
        </NativeActionForm>
      )}
      <button
        type="button"
        disabled={saving || loading}
        onClick={() => void read()}
      >
        Read saved settings
      </button>
      {observed && !client.requiresRead && (
        <div>
          <p>Saved workflow context:</p>
          <pre>{observed.workspace_prompt || "No workspace context"}</pre>
          <dl>
            <dt>Saved remote</dt>
            <dd>
              {observed.remote_hidden
                ? "Configured outside this panel"
                : observed.git_remote_url || "None"}
            </dd>
            <dt>Saved Git username</dt>
            <dd>{observed.git_username || "None"}</dd>
            <dt>Saved large-file threshold</dt>
            <dd>
              {observed.git_large_file_threshold === null
                ? "Wright default"
                : `${observed.git_large_file_threshold / MiB} MiB`}
            </dd>
          </dl>
          <button
            type="button"
            onClick={() => {
              replace(observed);
              setMessage("Using saved settings.");
            }}
          >
            Use saved values
          </button>
          <button
            type="button"
            onClick={() => {
              client.accept(observed);
              setBase(observed);
              setObserved(undefined);
              setBlocked(false);
              setMessage(
                "Your edit is retained against the observed settings. Review it before saving.",
              );
            }}
          >
            Keep my edit
          </button>
        </div>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
