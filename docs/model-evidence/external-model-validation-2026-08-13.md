# NeuralFoil External Model Validation — 2026-08-13

## Result

**Passed** for `neuralfoil-medium` package revision 1, variant `medium-npz-cpu-f64`, adapter `wright-neuralfoil-numpy` 1.0.0, and source commit `bb8a775199d1dafb5f410e68e027ba6eca1af9bc` only.

The opt-in probe ran beneath ignored `.local-run/` state on Windows x86-64. No downloaded model byte, repository checkout, export archive, virtual environment, or runtime scratch file is staged in Git. Normal tests remain offline and skip this probe unless `WRIGHT_EXTERNAL_MODEL_ROOT` is explicitly set.

## Source and artifact evidence

Primary sources:

- [immutable repository revision](https://github.com/peterdsharpe/NeuralFoil/tree/bb8a775199d1dafb5f410e68e027ba6eca1af9bc);
- [MIT license at that revision](https://github.com/peterdsharpe/NeuralFoil/blob/bb8a775199d1dafb5f410e68e027ba6eca1af9bc/LICENSE.txt);
- [NeuralFoil 0.3.3 on PyPI](https://pypi.org/project/neuralfoil/0.3.3/);
- [official golden-value test](https://github.com/peterdsharpe/NeuralFoil/blob/bb8a775199d1dafb5f410e68e027ba6eca1af9bc/tests/test_golden_values.py);
- [NeuralFoil paper](https://arxiv.org/abs/2503.16323).

The raw immutable URLs returned exactly:

| Selected artifact                     |  Bytes | SHA-256                                                            |
| ------------------------------------- | -----: | ------------------------------------------------------------------ |
| `LICENSE.txt`                         |   1074 | `f3a3857f0bfab1733bcea48be8b6f1ad2c43176f855362cdd6c334a360a93450` |
| `model/nn-medium.npz`                 | 103467 | `6cae229ce9ab9df0c3c68a1a441fae529a78481409d6b3ac4baf17ee58715952` |
| `model/scaled_input_distribution.npz` |   7696 | `63a33149c902ad01ecf537dd2d127d9e7ffbf86527893f4dc76f25f7087a3573` |

The first checkout observation changed `LICENSE.txt` to CRLF and therefore produced the wrong size/hash. The probe rejected that representation; the package now records the authoritative 1,074-byte raw Git blob. This is positive evidence that immutable digest checks catch line-ending changes rather than silently normalizing source bytes.

NPZ inspection used `allow_pickle=False`. The medium weights contained only numeric finite arrays with the declared dense-layer shapes: 25 inputs, four 64-wide hidden layers, and 198 outputs. The distribution file contained finite numeric 25-vector mean and 25-by-25 covariance/inverse-covariance arrays. Publisher training `.pth` files and all source/repository archives were excluded.

## Runtime and official-vector evidence

The publisher's PyPI 0.3.3 runtime and Wright's independent reviewed adapter returned identical values for the official fixed medium-model Kulfan vector:

```text
analysis_confidence = 0.9557118377834403
CL                  = 1.1033280967904384
CD                  = 0.009198824384558149
CM                  = -0.11059803045101073
Top_Xtr             = 0.25054349678066945
Bot_Xtr             = 0.9648784090579786
```

The Wright mandatory vector passed relative tolerance `1e-6` with:

- manifest digest: `2afa85dc40e7ddbc196e8cc5fb91b5bbe3e26738c0122ea6df9f86202b22e488`;
- artifact-set digest: `c8a189ca73d05bd2d94831336b0fdb9fa3db68b5ae2b5355cb2036ce24689683`;
- installation digest: `e2fc45a46f1d278366d844082724e72b25f1facba832d3fe051ab35a3317c13c`;
- input digest: `1119168dab03b5ca13721badade0c27ed1178e58cf4405d96d8c4ee67a0001f4`;
- output digest: `18cd384bfb5ae9c4aad4857c94923621a0486454684e77dd1814e614ee057746`;
- material digest: `9bc8a48dfa9c4213306ceb63cc7f3b81f7354e22fafb71933ab1a7e541721f06`;
- persisted evidence ID: `evidence-e1eb804fad44197fe986232e`.

One isolated adapter measurement observed 29.878 ms verification, 8.796 ms load, 4,292,608 bytes resident set after load, and 20 Gateway-protocol inference exchanges between 1.496 ms and 3.275 ms (2.171 ms median). The adapter-reported model calculation was 1 ms. These host observations are below the conservative package ceilings of 256 MiB RAM, 5 seconds load, 2 seconds inference, and 4 KiB output.

## Lifecycle evidence

The opt-in test `tests/external/test_neuralfoil_external_model.py` performed the following against the exact public raw URLs and a real local database/content store:

1. loaded the bundled approved catalog entry and computed compatible status only after the optional NumPy adapter was present;
2. created and confirmed an exact 112,237-byte network plan;
3. acquired all three immutable HTTPS artifacts, verified size and SHA-256, promoted them into content-addressed storage, and atomically installed them;
4. created a second plan from verified cache with `network: none` and no network effects;
5. launched the isolated adapter, verified NPZ keys/shapes, loaded, passed the mandatory official vector, shut down, and left zero runtime scratch entries;
6. enabled the typed `airfoil_aerodynamics` task for one workspace and invoked it through the governed model capability path;
7. previewed and confirmed a deterministic offline export (`119,163` bytes in the recorded run), then re-inspected its exact package identity;
8. disabled the workspace binding, previewed and confirmed installation disable and uninstall, archived the explicit export reference, and previewed and confirmed purge;
9. reclaimed exactly 112,237 verified bytes, left no content object payloads, and reported clean purge/runtime cleanup.

The recorded install, export, disable, uninstall, and purge operations all reached durable `succeeded` states. The export reference blocked purge until it was explicitly archived. No credential, external acceptance, paid service, GPU, physical actuation, runtime endpoint, process handle, host path, or reusable Rivet authority crossed a public result boundary.

## Reproduction

This is intentionally not a normal gate. From a checkout where the exact three files have been placed beneath ignored `.local-run/neuralfoil-selected/`:

```powershell
$env:WRIGHT_EXTERNAL_MODEL_ROOT=(Resolve-Path .local-run/neuralfoil-selected).Path
uv run --with numpy==2.3.2 pytest tests/external/test_neuralfoil_external_model.py -q --basetemp .local-run/neuralfoil-pytest
```

The probe passed on 2026-08-13. Delete the ignored probe checkout, selected files, virtual environments, and test state when local audit retention is no longer needed; none are required by the product or normal tests.
