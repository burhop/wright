# Wright synthetic beta-testing loop

This is the operating guide for the bounded lab in
[the accepted plan](../design/synthetic-beta-testing-plan.md). The scripts support
one real disposable customer VM, customer feedback, independent evidence review
and one narrow calibration comparison. Commands below are a procedure, not claims
of completed customer sessions. Actual status belongs to
the single progress record (retained local evidence: `artifacts/first-contact/synthetic-beta-001/progress.md`).

The implemented backend uses the explicitly approved local **ARM64/KVM** route:
Ubuntu 24.04 ARM64, XFCE, Firefox and Hermes 0.19.0. It is a real QEMU guest with
its own kernel; Docker contains the user-space hypervisor launcher. It is not an
x86_64 qualification or a container substituted for the customer desktop.

## Roles and boundaries

For a newcomer journey, give the customer an ordinary problem and available
personal facts. The opening message must not name a provider, prescribe tool
calls, use Wright-specific workflow terminology, or recite the observer's success
checklist. Wright must introduce those concepts and guide setup through its normal
interface. Keep existing access authorizations private until the product asks the
relevant question; they are not provider recommendations. A prescribed process is
a guided exercise and must be labeled separately from unaided discovery. Preserve
earlier assignments and reports when changing future profiles.

| Role | Access and responsibility |
| --- | --- |
| Technical preparation | Builds/fixes the lab before observation, freezes packages, restores clean guests and supplies temporary model access. Uses preparation SSH; intervention during an attempt must be recorded. |
| Customer | A fresh GPT-6.1 Sol Medium process receives visible guest controls and records feedback. No host repository/history, host-shell callback, DOM callback or calibration key is supplied. It can type arbitrary commands in the guest terminal; the customer instructions prohibit source debugging/private API shortcuts, and the observer checks the actual route afterward. |
| Independent reviewer | A separate GPT-6.1 Sol High process receives the original report, event log and scoped retained captures/result receipts after observation. It returns a separate verification; it cannot guide or alter the live attempt. |

Customer and evaluator instructions are versioned in
[`assets/customer.md`](https://github.com/burhop/wright/blob/e9710f58596e8ed601e2cfd17267ec260f46017a/scripts/synthetic_beta_testing/assets/customer.md) and
[`assets/evaluator.md`](https://github.com/burhop/wright/blob/e9710f58596e8ed601e2cfd17267ec260f46017a/scripts/synthetic_beta_testing/assets/evaluator.md).
The controller enforces the host/guest boundary, exposed tool set, resource
limits and observation deadline outside these prompts. It does not semantically
filter every guest keystroke: ordinary terminal access can reach guest commands
and native APIs. The customer-only route is an instruction plus a post-session
evidence requirement, not a capability isolation claim. An observed shortcut must
be reported and can disqualify the affected stage. Real
engineering approvals and physical operations are outside the test. An accurate
report of a product blocker can qualify as an observed journey; absent desktop,
authentication or reliable evaluation cannot establish usable product behavior.

## Prepare the laboratory

Run from `/home/burhop/repos/wright`. Use a real absolute lab path outside Git.
The examples use shell variables with the `WRIGHT_BETA_` prefix; they do not change
the user's HOME, Codex home or saved Hermes profile.

```bash
export WRIGHT_BETA_LAB=/tmp/wright-beta-lab
export WRIGHT_BETA_LAUNCHER=sha256:172e37d60f74c316521b1ff81d9d3d228e76809b3c917aa3a0feee9ecf2f55ee
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" init --launcher-image "$WRIGHT_BETA_LAUNCHER"
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" download-image
```

`init` requires an existing usable `/dev/kvm`, Docker access and the immutable
local launcher image. It does not install host virtualization. The launcher build
recipe is [`vm-launcher.Dockerfile`](https://github.com/burhop/wright/blob/e9710f58596e8ed601e2cfd17267ec260f46017a/scripts/synthetic_beta_testing/assets/vm-launcher.Dockerfile).
Rebuilding that recipe produces a separately identified launcher; freeze and
qualify its resulting image ID before use. The OS download is dated and hash
checked; inspect the saved download receipt rather than trusting its filename.
The default VM has 4 vCPUs, 8 GiB guest RAM and a minimum 24 GiB virtual disk.

Create a dedicated preparation key, then boot the package-installation recipe:

```bash
mkdir -p "$WRIGHT_BETA_LAB/private"
ssh-keygen -t ed25519 -N '' -f "$WRIGHT_BETA_LAB/private/provision-key"
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" prepare --session preparation --base-image "$WRIGHT_BETA_LAB/images/noble-server-cloudimg-arm64.img" --base-sha256 50e24e1fb79e89116e939d90aa7738f7af48c442fa1bc2510131e0b39c50348e --ssh-public-key "$WRIGHT_BETA_LAB/private/provision-key.pub"
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" start --session preparation
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" state --session preparation
```

The first cloud-init recipe is
[`hermes-baseline.cloud-init.yaml`](https://github.com/burhop/wright/blob/e9710f58596e8ed601e2cfd17267ec260f46017a/scripts/synthetic_beta_testing/assets/hermes-baseline.cloud-init.yaml).
It installs the desktop and pinned Hermes package. Package installation alone is
not qualification. Before freezing, inspect the actual desktop/control, browser,
Hermes executable and version, installed package/dependency inventory, and absence
of Wright, engineering applications/MCPs, workspaces, credentials and customer
history. Retain screenshots and resulting-state receipts. Do not authenticate a
browser or save model credentials to this reusable disk.

Preparation SSH uses `guest.ssh_command(lab_root, session_id="preparation")`,
loopback port 18091, the dedicated key and per-session known-host files. It never
disables host-key checks. This channel is not exposed to the customer model.

After qualification, run the guest's `/usr/local/sbin/wright-beta-freeze` as root
through that preparation channel. Its shutdown may close SSH before the command
returns. Verify actual guest termination with `state`, then flatten the stopped
overlay with the immutable launcher's `qemu-img convert -O qcow2`. Write a new
file under `LAB/images/`, record its SHA256 and complete installed inventory,
and keep the old image. Never convert a live disk or overwrite a frozen baseline.
The freeze helper removes runtime state/keys and clears free blocks; its marker
does not replace an independent clean-disk inspection and restore proof.

```bash
.venv/bin/python - <<'PY'
import os, subprocess
from scripts.synthetic_beta_testing.guest import ssh_command
lab = os.environ["WRIGHT_BETA_LAB"]
result = subprocess.run(ssh_command(lab, session_id="preparation") +
    ["sudo -n /usr/local/sbin/wright-beta-freeze"], timeout=600)
print({"freeze_ssh_exit": result.returncode, "shutdown_requires_state_check": True})
PY
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" state --session preparation
.venv/bin/python - <<'PY'
import json, os, subprocess
from pathlib import Path
from scripts.synthetic_beta_testing.provision import backend_for, image_prefix, load_config
from scripts.synthetic_beta_testing.vm import sha256
lab = Path(os.environ["WRIGHT_BETA_LAB"])
config = load_config(lab)
backend = backend_for(lab, config)
if backend.state("preparation")["live"]:
    raise SystemExit("Guest is still live; do not freeze its disk")
_, manifest = backend._load("preparation")
target = lab / "images/hermes-only.qcow2"
if target.exists() or target.is_symlink():
    raise SystemExit("Frozen baseline already exists; preserve its identity")
subprocess.run(image_prefix(lab, config) + ["qemu-img", "convert", "-O", "qcow2",
    manifest["overlay"], str(target)], check=True)
receipt = {"path": str(target), "sha256": sha256(target),
    "scope": "stopped disk identity; clean baseline still requires restored inspection"}
(lab / "images/hermes-only.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
PY
```

Restore a fresh technical clone from that image, verify cleanliness again and
exercise control. A failed reset or PATH/authentication correction belongs to
technical preparation. Freeze a new baseline identity after any correction.

## Reuse the retained baseline

This execution retained its inspected Hermes-only baseline and both frozen
candidate bundles under ignored
`.local-run/synthetic-beta-001-retained/`, identified by
`retained-baseline.json` (retained local evidence: `artifacts/first-contact/synthetic-beta-001/retained-baseline.json`).
The baseline is `hermes-baseline-v2.qcow2`, SHA256
`d04171fa45390d4698aadd03b66598080b3247f8c114575aaf56fe7117779cca`.
It contains the desktop and Hermes, not Wright, engineering tools, authenticated
sessions or model access. The retained manifest is a source of expected identities;
check the actual copied bytes before use.

Initialize a **new owned lab** with the already-qualified launcher, rather than
copying the old machine directory or editing its ownership marker. This avoids
reusing old socket paths, PIDs, container labels, credential paths or observed
session identities. On the existing approved ARM64 host:

```bash
export WRIGHT_BETA_LAB=/tmp/wright-beta-reuse-001
export WRIGHT_BETA_RETAINED=/home/burhop/repos/wright/.local-run/synthetic-beta-001-retained
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" init --launcher-image sha256:172e37d60f74c316521b1ff81d9d3d228e76809b3c917aa3a0feee9ecf2f55ee
.venv/bin/python - <<'PY'
import json, os, shutil, subprocess
from pathlib import Path
from scripts.synthetic_beta_testing.vm import sha256
lab = Path(os.environ["WRIGHT_BETA_LAB"])
retained = Path(os.environ["WRIGHT_BETA_RETAINED"])
identity = json.loads((retained / "retention.json").read_text())["baseline"]
source = retained / "images/hermes-baseline-v2.qcow2"
target = lab / "images/hermes-baseline-v2.qcow2"
target.parent.mkdir(exist_ok=True)
if target.exists() or target.is_symlink():
    raise SystemExit("Preserve the existing destination; choose a fresh lab")
subprocess.run(["cp", "--reflink=auto", "--no-clobber", str(source), str(target)], check=True)
if sha256(target) != identity["sha256"]:
    raise SystemExit("Copied baseline identity mismatch; do not boot it")
shutil.copytree(retained / "public", lab / "public",
    ignore=shutil.ignore_patterns("public-manifest.json"))
print({"baseline": str(target), "sha256": identity["sha256"],
    "public_manifest": "Regenerate for the new lab owner before serving"})
PY
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" freeze-public
mkdir -p "$WRIGHT_BETA_LAB/private"
ssh-keygen -t ed25519 -N '' -f "$WRIGHT_BETA_LAB/private/provision-key"
export WRIGHT_BETA_BASELINE="$WRIGHT_BETA_LAB/images/hermes-baseline-v2.qcow2"
export WRIGHT_BETA_BASELINE_SHA256=d04171fa45390d4698aadd03b66598080b3247f8c114575aaf56fe7117779cca
```

Use the normal `prepare --clone-seed`, `start`, RAM-access and `serve-public`
commands below with a new session ID. Verify the restored desktop and clean state
before observation. Regenerated manifests describe the new owner and paths while
the baseline/candidate content identities stay fixed. Do not copy the original
`provision.json`, `vm.json`, `.synthetic-beta-lab.json`, container IDs, private key,
known-host files or raw session directory into the new active lab. Old reports,
reviews and protocols remain unchanged archival evidence; they are not new
observations or permission to resume an old run. A missing launcher requires a
separately identified rebuild/qualification, not replacement of its recorded ID.

## Freeze the candidate and restore the customer

Use an isolated source checkout if the main worktree contains unrelated edits.
Record the complete source set, declared toolchain/dependencies and adapter commit.
Build the native application, including its packaged frontend:

```bash
.venv/bin/python scripts/build-native-runtime.py --output "$WRIGHT_BETA_LAB/candidate" --evidence "$WRIGHT_BETA_LAB/candidate-build.json"
```

Do not use `--skip-frontend-build` or a development frontend for the customer.
Pin the wheel, packaged UI, dependency artifacts, Hermes adapter and candidate
handoff/channel by their actual hashes/commit identities. A local package with an
existing version string is private candidate evidence, not a public release.
Read the selected MCP's recipe, qualification and usage guide before freezing its
safe digital readiness operation and expected output. No provider installed during
technical preparation belongs in the clean customer baseline.

Stage only examined customer-facing package/dependency/adapter artifacts and the
clearly labelled installation handoff under `LAB/public/`. Never stage the whole
lab, auth files, recordings, source checkout or preparation key. Then freeze it:

```bash
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" freeze-public
```

Set these two values from the retained frozen-baseline receipt:

```bash
export WRIGHT_BETA_BASELINE=/absolute/lab/images/hermes-only.qcow2
export WRIGHT_BETA_BASELINE_SHA256=REPLACE_WITH_ACTUAL_64_CHARACTER_SHA256
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" prepare --session customer-001 --base-image "$WRIGHT_BETA_BASELINE" --base-sha256 "$WRIGHT_BETA_BASELINE_SHA256" --clone-seed --ssh-public-key "$WRIGHT_BETA_LAB/private/provision-key.pub"
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" start --session customer-001
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" serve-public --session customer-001
```

`--clone-seed` attaches fresh preparation access without reinstalling packages.
`--no-seed` instead creates a clone with no SSH seed, when preparation access is
unneeded. Each restored guest has independent host-key trust. The candidate server
is confined to the verified owned QEMU container, binds container loopback and is
reachable by the guest at `http://10.0.2.2:18092/`. It publishes no host port.
Its manifest must still match the frozen files. Label this departure from the
public website in the task and resulting report.

## Supply access and observe

The current goal includes the user's explicit approval for temporarily supplying
an existing supported **access token** to this VM. That approval does not include
refresh credentials or permanent authenticated snapshots. The preparation helper
copies only selected allowlisted credential fields, checks the provider endpoint,
disables guest swap and writes the entire Hermes runtime profile in `/run` tmpfs.
Never print the source credential file or put tokens in command arguments.
The guest wrapper keeps `WRIGHT_HOME=/run/hermes-beta/wright-home` and
`TMPDIR=/run/hermes-beta/tmp`. **Fresh disposable guests now separate software
storage from private state:**

| Content | Guest storage | Reason |
|---|---|---|
| Wright native runtimes, bootstrap environments and package cache | Disk, beneath `/var/lib/wright-beta/native-software`, bind-mounted at `WRIGHT_HOME` | Repeated candidate installation must not fill unreclaimable tmpfs with software copies. |
| Wright `data`, `state` and `logs` | Subdirectories of one private 4 GiB tmpfs, bind-mounted at their unchanged native paths | Native lifecycle imports provider credentials into `data/credentials.json` and `data/secrets.d`; `data/control-plane.token` is also private. Keep possible private state/log content in RAM. |
| Hermes profile, temporary access and general temporary files | `/run/hermes-beta` tmpfs | Atomic credential replacement stays on RAM storage; general temporary files are not assumed secret-free. |
| Engineering files and run evidence | Still within Wright's RAM-backed `data` | This bounded correction does not establish safe credential separation for all workspace/provider files. Retain evidence before guest teardown. |

The implementation preserves ordinary native paths and ownership checks. It does
not move or delete any existing active, rollback or failed runtime. Software
versions accumulate on the disposable **disk**, subject to its available space;
there is no automatic runtime garbage collector. Disk-backed file cache is
reclaimable by the OS, although running processes still require memory.

Preparation is permitted only before Wright installation in a fresh guest.
Existing software, target paths or storage guards are refused. The protected live
guest and reusable baseline are unchanged. The dedicated private tmpfs is
`/run/hermes-beta/wright-private`, with
`exec,nosuid,nodev,uid=1000,gid=1000,mode=0700,size=4G`; four GiB is a size limit,
not preallocated RAM. The guest `/run` remains `noexec`. Only the exact software
bind mount is remounted with `exec,nosuid,nodev`; the disk parent is unchanged.

Before credentials are written, preparation verifies the disk filesystem, exact
mount targets, matching source/destination filesystem and inode identities,
private tmpfs size/options, disabled swap and credential-bearing bindings. A
root-owned guard repeats those checks before the lab's `hermes` wrapper launches,
failing closed if mounts are absent after reboot or otherwise changed. The
`runtime_mount` receipt records the mounts, available disk bytes and observed
`MemTotal`, `MemAvailable`, `Shmem` and swap bytes. The technical candidate installer
uses that same guard and retains its observation. These are observations at that
instant, not a memory reservation or guarantee that an arbitrary solve will fit.

This arrangement is intended to retain native install/start/update/rollback and
ordinary uninstall behavior: their software directories remain normal disk
subdirectories, not individual mount roots. **Do not run native purge in this
laboratory layout.** Purge recursively removes `data`; its mounted root cannot be
removed and failure can occur after destructive partial cleanup. No product purge
behavior is changed or claimed qualified here. Use scoped disposable-guest
teardown after evidence retention. Reboot discards private state and credentials;
only same-boot workspace reopening is supported. Future purge qualification or
moving engineering data to disk requires a separate storage design.

Source inspection establishes this layout's intended boundaries. Direct fresh
installation/update observations must establish its actual behavior; regression
suites remain deferred under the current campaign instruction.

```bash
export WRIGHT_BETA_HERMES_AUTH=/absolute/path/to/approved/hermes/auth.json
.venv/bin/python -m scripts.synthetic_beta_testing.guest --lab-root "$WRIGHT_BETA_LAB" --session customer-001 supply-runtime-access --auth-source "$WRIGHT_BETA_HERMES_AUTH" --receipt "$WRIGHT_BETA_LAB/machine/sessions/customer-001/runtime-access.json"
```

Verify Hermes model access before observation and retain that separately. Supply
the task as a short customer-facing file: visit MakerEngineer.com, begin the
replacement-handle job, use the labelled candidate instructions, and attempt the
initial useful operation. Do not include a developer click sequence or the
calibration answer key. The task must not promise a finished printable handle.

The private handoff downloads a frozen candidate bundle containing its local bare
adapter repository. After extracting it in the guest's download directory, the
documented adapter installation command is:

```bash
hermes plugins install "file://$PWD/wright-candidate/adapter.git" --enable
```

Keep the `file://` scheme. Technical preparation found that the Hermes shallow
clone failed against the static dumb-HTTP Git route, and that a raw local path
was interpreted as a GitHub target. A third technical attempt using the file URI
installed/enabled the adapter and passed native start/core doctor checks. These
are preparation results, not customer feedback or proof of a complete configured
engineering environment. The frozen customer-facing bundle/handoff must use
this corrected route; changing its bytes requires a new recorded identity.

```bash
export WRIGHT_BETA_CODEX_BINARY=/home/burhop/.codex/packages/standalone/releases/0.159.2-aarch64-unknown-linux-musl/bin/codex
export WRIGHT_BETA_CUSTOMER_TASK=/absolute/path/to/customer-task.txt
.venv/bin/python -m scripts.synthetic_beta_testing.cli --lab-root "$WRIGHT_BETA_LAB" --auth /home/burhop/.codex/auth.json --binary "$WRIGHT_BETA_CODEX_BINARY" run --session customer-001 --task "$WRIGHT_BETA_CUSTOMER_TASK" --timeout 3600 --model gpt-6.1-sol --effort medium
```

The customer process mounts only the native CLI, its exact adjacent
`codex-code-mode-host` helper and the read-only scoped auth file. The controller
rejects a missing helper and records both executable hashes; Code Mode routing
is part of the native CLI, not a fixed customer navigation script.
Its writable configuration/history is tmpfs, thread is ephemeral and cwd is empty.
No host repository, user config, AGENTS files, plugins or implementation history
are mounted into the customer model process. Desktop and feedback callbacks are
its only supplied tools. This does not remove the terminal's ability to run
commands inside the disposable guest; inspect the recorded route for compliance.
The customer
chooses its own actions and may stop after two unsuccessful recovery strategies.
Keep all failed attempts; a timeout, authentication failure or intervention is
recorded separately from product feedback. Screens and terminal contents during
authentication require preparation-time exclusion. Existing text redaction does
not inspect or redact screenshot pixels. Raw captures remain private; inspect
selected exported images before committing or sharing them.

## Independently review and render

```bash
.venv/bin/python -m scripts.synthetic_beta_testing.cli --lab-root "$WRIGHT_BETA_LAB" --auth /home/burhop/.codex/auth.json --binary "$WRIGHT_BETA_CODEX_BINARY" review --session customer-001 --receipts /absolute/path/to/result-state-receipts.json
.venv/bin/python -m scripts.synthetic_beta_testing.cli --lab-root "$WRIGHT_BETA_LAB" audit --session customer-001
.venv/bin/python -m scripts.synthetic_beta_testing.cli --lab-root "$WRIGHT_BETA_LAB" storyboard --session customer-001 --output "$WRIGHT_BETA_LAB/storyboards/customer-001"
```

Review receipts must establish only observed outcomes: exact installed package,
customer-created/reopened workspace, MCP discovery/access, actual gateway call and
the declared output properties where reached. Use not-reached/failed dispositions
when necessary. The reviewer sees session-scoped retained captures through its own
tool; it has no live guest controls. It never edits `report.json`. The rendered
`report.md` combines that original account with a visibly separate audit.
Each reviewer attempt retains its unchanged raw `verification.json` and resulting
`audit.json` inside its own `review-ID/` directory before canonical latest files
are updated. Invalid responses keep an `audit-error.json` instead. Earlier
canonical reviews are archived to their original attempt before replacement.
The supplied reviewer ID, customer session ID and event-log digest must match
exactly; model-generated suffixes or replacement identities are not repaired.
The deterministic `storyboard` command exports five HTML frames from the same
report/events/audit, with at most six hash-validated session PNGs and a source
manifest. It requires the saved independent audit to match current evidence,
escapes customer text and refuses to overwrite an earlier export. It makes no
model calls and leaves the original report unchanged. Open the resulting
`storyboard.html` locally; no external assets are needed.

Audit validates event/session identities, retained capture paths/hashes, the
evaluator's separate identity and event-log hash, findings and stage claims.
Unsupported completion or contradictory outcomes are rejected. Missing evaluation
of a finding remains uncertain. A structured report or green integrity audit does
not independently prove engineering correctness or human usability.
All `evidence_refs` arrays contain only exact IDs from `allowed_event_ids`, such
as `e00024`. Capture paths and receipt-field expressions are not event references;
the reviewer may describe those details in `reason`. The controller preserves
and rejects an invalid reference rather than translating it silently. This is a
schema clarification, not permission to alter the customer's narrative or the
calibration acceptance rule.
Both roles also receive a structural native `turn/start.outputSchema` derived
from the existing report contract. Customer output fixes the session, field types,
stage/status enums and event-ID shape; reviewer output fixes the supplied subject
IDs/digest, actual known event IDs, customer finding IDs and registered target key
when present. Resolved schema files and canonical schema hashes are retained with
each role's configuration/transport. These constraints reduce schema drift; the
independent backend audit still checks actual files, event existence, identities
and consequential claims. Schema-valid model text creates no completion or
engineering approval authority.

## Calibrate one obstacle

Before any calibration session, retain a private protocol with a timestamp,
opaque variant IDs, distinct immutable candidate/documentation hashes, inspected
intended difference and randomized order. Freeze the same baseline/checkpoint,
task, model/effort, help policy, input and instruction identities. Keep the answer
key, expected findings and previous reports out of the customer's context.

Restore four fresh sessions from the matched checkpoint: two per variant, each
at most 900 seconds. Attach runtime access after restoration, never in the saved
checkpoint. Run/review each with the commands above and its own session ID. For
review only, `--target /absolute/path/to/private-registered-target.json` supplies
the evaluator's private `issue_key` and rule. The reviewer maps evidenced customer
findings privately; the customer's original report needs no answer-key tag.
Because Wright private state lives in tmpfs, a stopped-disk checkpoint cannot preserve it
implicitly. Recreate the matched prepared UI state after each restore, or restore
a separately inspected, credential-free declared state artifact; retain its exact
identity and preparation receipt. Do not snapshot runtime tokens or call the
technical checkpoint setup customer-created work.
For new protocols that explicitly declare the separate accomplishment contract,
use `run --observation-scope calibration_checkpoint_v2 --timeout 900` and record
that same `observation_scope` in the preregistered protocol. Ordinary runs default
to `first_contact` and allow at most 3,600 seconds. The controller writes its typed
scope to `customer-session.json`; comparison requires the protocol's declared
scope and the comparison record's scope to match that controller record. Neither
task wording nor a model's claim selects the contract.

The original `calibration_checkpoint` scope retains its v1 semantics: a completion
claim requires independently evidenced registered-target progress. Protocol001,
its feedback, reviews and comparison retain that rule and their original
identities. Do not relabel or re-evaluate those observations as v2. Its obstacle
accounts disclosed losing and restoring Side; the v1 audit rejected their
completion labels because restoration did not establish the registered
friction-free progression. Preserve this distinction between an accurate factual
account and that original completion rule.

The explicit v2 scope selects the versioned
[evaluator-v5 instructions](https://github.com/burhop/wright/blob/e9710f58596e8ed601e2cfd17267ec260f46017a/scripts/synthetic_beta_testing/assets/evaluator-v5.md)
and adds a separately typed verification object, `checkpoint_accomplishment`:
`claim_disposition` (`supported`, `unsupported` or `uncertain`),
`final_state_reached` (boolean), `evidence_refs` (exact known event IDs) and
`reason`. This assesses the factual account and whether the declared final task
state was reached. An honestly disclosed loss and restoration can support that
account and final state. It cannot establish uninterrupted retention or change
`target_observation.present/progressed`: those retain the exact preregistered
target rule. The corrected variant must still pass the point without the issue
or restoration. Unsupported statements, omitted restoration and unsupported final
states remain rejected or uncertain; the evaluator never repairs the narrative.
Earlier full-journey stages the checkpoint customer did not perform remain
`not_reached`; neither scope grants installation, engineering or approval claims.

Protocol002 preregistered this one permitted rubric correction before its four
new sessions, with a new controller freeze and evaluator identity. It preserves
the customer task/instructions, target rule, candidate identities, baseline,
checkpoint, model/effort and help policy. Keep both protocols and their outcomes;
v2 is an explicit new contract, not a correction to old evidence.

Independent completion permits ordinary product documentation, Hermes assistance
and within-policy workarounds. Nonempty `help[]` is informational and does not
imply external assistance. The controller records `assistance=none` for its
UI-only runner; actual implementer/human intervention must be recorded separately
and ends an unassisted calibration observation. A customer's text cannot grant or
remove that controller classification.

The protocol JSON uses `protocol_id`, `preregistered_at`, `observation_scope`,
`target_issue`, `variants`
(`id`, `candidate_sha256`, `has_obstacle`) and `context` containing
`baseline_digest`, `task_digest`, `model`, `effort`, `help_policy_digest`,
`inputs_digest`, `checkpoint_digest`, `instructions_digest`. Each comparison
session record includes actual `root`, inline `report` and `verification`,
`session_id`, unique `reset_id`, `variant_id`, `protocol_id`, `candidate_sha256`,
matching `context`, `status`, `started_at`, `customer_context_isolated` and
`variant_blinded`. Populate these from retained receipts, not assertions invented
afterward. See the focused fixture tests for exact machine-readable shapes.

```bash
.venv/bin/python -m scripts.synthetic_beta_testing.cli --lab-root "$WRIGHT_BETA_LAB" compare --protocol /absolute/path/to/private-protocol.json --sessions /absolute/path/to/comparison-sessions.json
```

Comparison re-audits all four sessions. Both obstacle sessions must identify the
target with evidence; both corrections must pass the point without that issue,
with actual observed progress. Unsupported consequential completion and
high-impact findings prevent a pass, as do evidence-integrity or subject failures.
High impact conservatively includes every defined impact except `minor_friction`.
Unsupported or uncertain non-target minor friction remains visibly rejected or
uncertain in the full audit; alone it does not fail this narrow calibration when
the target proof is strong. The audit records typed `calibration_blockers` so the
comparison never treats an entire report as uniformly good or bad.
Missing/failed sessions remain incomplete. Preserve inconclusive results; the
accepted plan permits only one bounded protocol correction and one additional
four-session comparison. This calibrates one obstacle and establishes no
statistical usability rate or human-equivalence claim.

## Evidence, cost and cleanup

Under `LAB/machine/sessions/SESSION/`, retain the VM/provisioning identity and
reset receipt, `events.jsonl`, capture hashes/images, `customer-agent/` transport
and final response, exact `report.json`, `report.md`, `customer-session.json`,
separate `review-*/` attempt, `verification.json` and `audit.json`. Preserve invalid
reports and failed reviewer attempts. Generate storyboards from this same report
and event data; do not maintain another manual progress dashboard.

Record implementation/setup, technical probes, VM runtime, customer inference,
product waits, evaluator work and interventions separately. Use actual app-server
usage when available, and label unavailable usage/cost as unavailable. Machine
time is not human task time or a dollar estimate. Raw screenshots can contain
private information: text-field redaction does not sanitize image pixels. Keep
raw captures private and inspect selected exports before committing or sharing.

The derived resource ledger (retained local evidence: `artifacts/first-contact/synthetic-beta-001/resource-ledger.json`)
retains available app-server token counters and process windows with their exact
record sources. Regenerate it after the final sessions/reviews and cleanup using
the file-only accounting recipe (retained local evidence: `artifacts/first-contact/synthetic-beta-001/recipes/README.md`).
Count a cumulative thread total once; never add its `last` counter or add cached
input/reasoning subsets again. Failed probes, failed customer attempts and rejected
review attempts still consumed resources and remain included. Incomplete transport
snapshots are partial usage observations, not proof that a process is currently
live or finished. Model process wall time, explicit customer waits, VM observation
windows and overall goal wall time overlap and are not additive phase totals.
Whole-VM uptime, actual CPU/RAM utilization, guest-Hermes token usage and exclusive
implementation-versus-QA effort remain unavailable where no corresponding
measurement was retained. Missing measurements are not zero and no dollars are
inferred from elapsed time or model tokens.

The same recipes directory retains byte-identical copies of execution-specific
technical preparation, resulting-state collection and comparison helpers. They
contain original lab paths and protocol001/protocol002 identities and are observer-only
reconstruction material, not a generic launcher. Use the documented generic
commands for a new lab, and create new identities/qualification when adapting an
execution-specific recipe. Never provide the answer key or these preparation
scripts to the customer as a successful navigation sequence.

```bash
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" stop --session customer-001
.venv/bin/python -m scripts.synthetic_beta_testing.provision --lab-root "$WRIGHT_BETA_LAB" state --session customer-001
```

Model containers are ownership-checked and stopped by the session/reviewer
controller. Stopping the owned guest also ends its candidate server and discards
runtime tmpfs credentials. Verify absence; do not use broad Docker cleanup. Keep
the frozen baseline and manifests. `reset --session SESSION` is for an unobserved
stopped preparation session; after observation, use a new session ID so evidence
is retained. Large qcow2 images, private preparation keys, raw recordings and
credentials stay outside Git. Commit only scoped recipes/code, small reviewed
redacted evidence and manifests. Push, merge, release and public website changes
retain their separate authorization.

## Repeated product-improvement observations

Use the [golden-hour improvement loop](golden-hour-improvement-loop.md) to register
a benchmark, freeze the customer/environment, fix one supported obstacle and
compare a fresh candidate. The local operator dashboard (retained local evidence: `artifacts/first-contact/golden-hour-tracking/dashboard.html`)
projects original reports and saved independent assessments. It keeps full
journeys, checkpoint calibration and lab failures separate; it neither executes
the loop nor changes Wright's runtime/engineering acceptance authority.

For new customer attempts, use the [timed journey procedure](golden-hour-improvement-loop.md#timed-journeys-and-work-outside-the-loop--26-october-update).
Start its clock before environment launch, freeze scenario-specific steps, record
customer transitions and issue categories, and export the two journey files with
the normal evidence. The CLI records a partial clock if startup was not captured.
Track diagnosis/fix/check/reporting work, including outside-loop findings, through
the existing development metrics activity owner. New timing instructions require
a fresh baseline; old six-milestone results are not full workflow outcomes.

Local evidence references identify preserved operator records; they are not included in the public documentation build.
