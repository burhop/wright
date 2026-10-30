# Disposable ARM64 customer guest

These commands operate the approved local Docker/KVM backend. Docker supplies
QEMU; the customer uses a real ARM64 VM. They do not install a host hypervisor,
publish Wright, or establish that the guest or beta tester has passed validation.
Run from the Wright repository with `PYTHONPATH=scripts`.

The caller supplies an owned lab parent directory and an existing Docker image
by immutable `sha256:` ID. `init` verifies the local image and `/dev/kvm`; it does
not pull an image. The default Ubuntu URL identifies the qualified 17 October
2026 image and its required SHA256. Downloads fail rather than accepting changed
bytes. The lab's machine owner, configuration, image and session manifests remain
available for review.

```bash
beta_lab=/tmp/my-wright-beta-lab
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" init
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" download-image
```

Prepare the Hermes-only baseline using a controller-owned provisioning public
key; no private key, model token, Wright installation or engineering MCP belongs
in the seed. The default template installs Hermes 0.19.0 and an XFCE desktop.
Initial provisioning requires network access inside the guest. Its recorded
completion marker does not prove desktop, model access or cleanliness.

```bash
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" prepare \
  --session preparation --base-image "$beta_lab/images/noble-server-cloudimg-arm64.img" \
  --base-sha256 50e24e1fb79e89116e939d90aa7738f7af48c442fa1bc2510131e0b39c50348e \
  --ssh-public-key "$beta_lab/private/provision-key.pub"
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" start --session preparation
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" state --session preparation
```

Inspect the desktop and installed software independently. Before freezing a
baseline, remove runtime access, customer sessions and SSH keys through the
declared freezer, verify cleanliness, stop the guest and compact the disk.
Record the resulting standalone qcow2 SHA256. The baseline freezer disables no
host service; it operates inside its disposable guest. The guest's Hermes
wrapper uses `/run/hermes-beta`, and temporary model access must remain on tmpfs
with guest swap disabled. It also places native `WRIGHT_HOME` and `TMPDIR` under
that tmpfs profile because Wright's lifecycle can import credentials into its data
directory. Workspace reopen checks cover only the same guest boot; an OS
restart discards the temporary Wright state. Baseline creation and its inspection
are separate from the provisioning commands.
Runtime preparation creates only a dedicated executable tmpfs at
`/run/hermes-beta/wright-home` with
`exec,nosuid,nodev,uid=1000,gid=1000,mode=0700,size=4G`. Parent `/run` stays
`noexec`. The 4 GiB limit is recorded and checked with exact mount identity in
`runtime_mount`; a nonempty target is refused. Native installation requires this
dedicated executable guest mount so its runtime can run while lifecycle-imported
credentials remain in RAM. No host mount or virtualization setting is changed.

Create each observed session with a fresh identity and the exact frozen baseline
hash. `--clone-seed` only supplies a fresh public SSH key and regenerates guest
host keys; it performs no software installation. `--no-seed` is an explicit
alternative for a clone managed solely through its desktop, without SSH setup.
Disks smaller than 24 GiB grow to that minimum; larger baselines never shrink.

```bash
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" prepare \
  --session customer-001 --base-image "$beta_lab/images/hermes-baseline.qcow2" \
  --base-sha256 ACTUAL_BASELINE_SHA256 --clone-seed \
  --ssh-public-key "$beta_lab/private/provision-key.pub"
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" start --session customer-001
```

SSH preparation must pass `session_id="customer-001"` to `guest.ssh_command` or
`guest.supply_runtime_access`, or `--session customer-001` to the guest CLI.
Known host keys live under `private/guest-hosts/customer-001/known-hosts`; host-key
checking remains enabled. A replacement guest with changed keys does not inherit
another session's trust. Prefer fresh session IDs for all observations.

Stage only intended customer downloads and instructions under `LAB/public`.
Freeze this directory before exposing it. The public server runs inside the
exact owned QEMU container, on its loopback port 18092. QEMU's guest accesses it
at `http://10.0.2.2:18092/`; no additional host port is published.

```bash
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" freeze-public
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" serve-public --session customer-001
```

The manifest covers every staged file's identity. Validation rejects hidden
files, symlinks, credential-shaped text and private-key markers. The optional
inspection support for bare Git under `public/adapter.git` does **not** establish
Hermes installation over dumb HTTP: its shallow clone failed in technical
preparation. The working private handoff downloads a frozen bundle containing
`wright-candidate/adapter.git`, then installs the extracted repository with an
explicit file URI from the guest download directory:

```bash
hermes plugins install "file://$PWD/wright-candidate/adapter.git" --enable
```

A raw local path was misinterpreted as a GitHub target. The file-URI technical
attempt installed/enabled the adapter and passed native start/core doctor; this
is preparation evidence, not a customer result. For any separately served loose
Git content, retain metadata, refs and loose objects and remove hooks, including
samples. Loose objects are decompressed with a size limit and checked against
their Git identity. Packed Git objects are outside the loose-Git inspection path. Package
archives are identified by hash; these checks are not an exhaustive audit of
archive contents. Keep credentials and private evidence out of this staging area.

Each session must have its own guest/container and server receipt. Changed
candidate bytes require a new retained identity, not an overwritten manifest.
The static server ends when its owned QEMU container ends. `stop` checks the exact
QMP guest name; it never falls back to killing unknown processes. `reset` refuses
a live guest and retains reports while replacing only its declared overlay.

```bash
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" stop --session customer-001
PYTHONPATH=scripts python -m synthetic_beta_testing.provision --lab-root "$beta_lab" reset --session customer-001
```

Retain the baseline and redacted evidence. Large images, private SSH keys, raw
recordings and runtime access stay outside Git. A stopped container's CID file
is removed only after Docker successfully confirms that exact container absent.
Control, authentication, customer behavior and calibration require their own
recorded observations; fixture tests do not qualify them.

## Technical FreeCAD preparation

`assets/prepare-freecad-arm64.py` is a preparation-only recipe for a separate
Ubuntu 24.04 ARM64 technical clone. It requires the guest marker and customer
user, a fresh installation directory, and the exact cached FreeCAD 1.1.1
AppImage SHA256. Transfer that cache into the technical guest explicitly; this
does not establish the public customer download experience. The script fetches
the public provider at `63acb305573194a011641ab13ccfb391fe95769f`, installs its
0.1.18 package and MCP SDK 1.28.1 into a private venv, and copies its matching
addon to the documented FreeCAD directories with localhost-only RPC settings.
No Docker is installed in the guest.

The script intentionally does not start FreeCAD, call tools or register Wright
bindings. Its receipt and `start-freecad.sh` describe the next operation. Inspect
the actual GUI, TCP readiness, discovery/schema and direct tool behavior before
the observed customer session. Use the existing predeclared
`artifacts/first-contact/synthetic-beta-001/provider-operation.json` unchanged for
the 10 × 8 × 6 mm box export; independently inspect the actual STL and retain
failures even when MCP transport reports success. A direct technical probe does
not prove Wright gateway access or the customer setup route.

```bash
# Run inside the disposable technical guest, after explicit cache transfer.
python3 prepare-freecad-arm64.py --technical-preparation-only \
  --appimage /home/customer/Downloads/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage
```

This clone must never replace the Hermes-only customer baseline. The complete
provider guide, selected-server recipe and retained AMD64/ARM64 qualification
remain the source of setup requirements and scoped historical evidence.

## Declared calibration checkpoint

`assets/install-native-candidate.py --technical-preparation-only --bundle FILE
--bundle-sha256 SHA --wheel-sha256 SHA` prepares each fresh calibration guest
through normal Hermes plugin installation and the existing installed adapter's
native start/doctor boundary. It requires a verified candidate bundle and empty
Wright state, keeps the runtime under `/run/hermes-beta/wright-home`, and writes
only nonsensitive identities and command statuses to its receipt. This scripted
technical installation is not an observed customer action. Failure preserves
the attempt; no fallback or automatic retry is performed.

After a normal candidate installation in each fresh guest,
`assets/prepare-handle-checkpoint.py --technical-checkpoint-only --output FILE`
creates the matched calibration workspace using the native browser bootstrap and
existing workspace/template/setup APIs. It requires the exact packaged handle
template 1.0.1 with source SHA256 `a6c7cecd0289f66db5766e1be995fb1afafbee3be0cd4d49221cb5acb533594f`.
It accepts no bearer token and persists no browser cookies. It creates no review,
accepted revision, run, provider installation or engineering output.

The receipt records exact workspace/session/source identities and input hashes,
plus a canonical guest entry URL. Its logical comparison identity excludes only
the proven platform-generated placeholder expansion; all original source bytes
and engineering resource hashes remain required. The controller must still open
the setup dialog and select Side visibly before the calibration observation.
These are declared preparation actions; reports must never attribute checkpoint
workspace creation to the synthetic customer.

Native draft creation also snapshots the current packaged workflow instruction
defaults into a workflow-header field. The factory reads the existing
`instruction-defaults` API before creation, verifies the saved field against that
exact payload and its asset body hashes, and records profile/version/defaults
digest. Its normalized full-source identity retains this complete policy field;
it does not discard it to make clones compare equal. All original template bytes
must remain unchanged apart from declared identity expansion. The first actual
factory diagnostic retained policy profile `wright.workflow-defaults` 1.2.1;
fresh factory execution still requires independent qualification.

For a failed preparation, `--inspect-existing` performs only GET requests against
the already-created checkpoint and records its source, template and current
defaults. It neither recreates the workspace nor retries the failed mutation.
Use a fresh output path to preserve the original attempt and its diagnosis.
