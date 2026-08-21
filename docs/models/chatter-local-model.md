# Local Chatter screening model

Wright exposes Chatter as a private engineering-model source record first. The source record is inspectable, but it cannot be downloaded, installed, enabled, or invoked. A usable package exists only after an owner explicitly runs the trusted local qualification and the resulting numeric serving package passes import, verification, parity, and mandatory-vector checks.

The model is a screening aid for discrete, caller-supplied simulated cutting candidates. Its score is an uncalibrated classifier output. It is not a real-world safety probability, confidence interval, certification, machining recommendation, or machine authority.

## Fixed source and recipe boundary

The bundled record pins:

- source revision `4eeb36dbfede3c194c43b3d2039abd5860a675f6`;
- Dataset 2 digest `1d7880d3fd321a86885c825003bfc8c1ba3ccd15cf0e0e7b9c283a48b0d51d5f`;
- 37 ordered process features with explicit units, origins, contract ranges, and qualification-population ranges;
- grouped 80/20 membership using seed 42, with 96 training groups, 24 validation groups, and zero group overlap;
- a 500-tree Random Forest recipe and the exact preprocessing/class-order/threshold contract;
- internal-use, non-redistributable terms until the owner records a broader grant.

Any changed source, data, membership, recipe, feature, preprocessing, classifier, threshold, serving byte, runtime, vector, resource ceiling, limitation, or parity fact requires a new reviewed package revision.

## Trusted qualification

Qualification is deliberately outside normal installation. It requires reviewed local source, Data Vault source, immutable Dataset 2, reference evidence, an environment lock, a new caller-owned output directory, and the exact acknowledgement recorded in `specs/072-chatter-rivet-scenarios/quickstart.md`.

The command runs without network access, validates every input identity before training, deterministically rebuilds the reviewed forest, exports only strict JSON plus numeric NPZ arrays, and evaluates source-versus-serving parity. It succeeds only when class agreement is at least 99.5%, mean score delta is no more than 0.01, maximum score delta is no more than 0.05, and all mandatory boundary decisions agree.

Qualification output is private and ignored. Wright never commits or distributes the dataset, source artifacts, environment, Joblib/pickle estimator, serving NPZ, or `.wright-model.zip` archive. A failed transaction removes its partial output.

## Safe serving package

The adapter accepts only `wright-chatter-forest-npz-1.0`:

- a bounded serving-metadata JSON document;
- numeric one-dimensional arrays with exact names, dtypes, shapes, counts, topology, feature indices, and finite values;
- passed conversion-parity evidence bound to the exact serving identities;
- an internal-use notice.

NumPy loads the archive with `allow_pickle=False`. Object arrays, extra members, source code, native libraries, plugins, training files, estimator objects, Joblib, pickle, remote code, unsafe paths, resource bombs, changed digests, and stale parity fail closed.

Package installation does not install NumPy, a training framework, a converter, driver, compiler, service, or global dependency. The separately reviewed `wright-chatter-forest-numpy` adapter must already be compatible and healthy.

## Typed result semantics

Each request contains one to 100 uniquely named candidates in the exact 37-feature order. Wright validates units, finite values, allowed origins, ranges, provenance, invariants, item count, and encoded size before inference.

Each ordered result includes the candidate identity, `stable` or `chatter` state, uncalibrated score, exact threshold, signed margin, applicability, warnings, limitations, review eligibility, and exact package/installation/adapter/vector/schema evidence. Threshold equality is classified as chatter. Near-threshold, out-of-population, or invariant-failing candidates require review and cannot be preferred.

The model never interpolates a stability lobe, invents an operating point, generates G-code, prescribes speeds or feeds, or controls a machine.

## Recovery

- **Source only**: run the explicit trusted qualification; normal install remains unavailable.
- **Adapter incompatible**: install or select a separately reviewed compatible adapter; do not weaken the package policy.
- **Parity stale or failed**: repeat qualification from the exact pinned inputs and create a new package revision.
- **Mandatory vector failed**: keep the installation unready and inspect the exact vector/evidence difference.
- **Insufficient resources**: free the declared local RAM/disk reservation and re-run preflight.
- **Cancelled or crashed**: inspect cleanup/residue, then start a fresh bounded run. Late output cannot become success.

Export remains prohibited for every real private Chatter package. Disable, uninstall, and reference-safe purge use the ordinary Engineering Models lifecycle.
