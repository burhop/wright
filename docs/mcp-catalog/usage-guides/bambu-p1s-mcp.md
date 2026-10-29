# Bambu P1S MCP: offline slicing qualification

Updated 28 October 2026. Status: isolated Linux ARM64 coupon slicing and passive nominal-path inspection verified; embedded package preview missing. This guide does not qualify or authorize printer access.

## Identity and existing evidence

Independent provider: [marctheshark3/bambu-p1s-mcp](https://github.com/marctheshark3/bambu-p1s-mcp/tree/7b50d0288fb7b91af8af422b96c4df4db0f1110c), exact catalog revision `7b50d0288fb7b91af8af422b96c4df4db0f1110c`. Catalog ID `bambu-p1s-mcp-marctheshark3`. Existing Windows qualification and limitations are recorded in [assessments](../status/assessments.yaml); its PLA coupon is not PETG handle qualification. See [setup recipe](../mcp-server-setup-recipes.md#bambu-p1s-mcp-offline-slicing).

## Selected host and readiness

The pinned provider discovers `orca-slicer` and accepts an explicit `BAMBU_SLICER`. Its slice implementation invokes a local CLI and does not require printer credentials. A separate selected provider container must contain the runtime and native application; do not add it to Wright's base image.

Official Bambu Studio v02.08.02.61 Linux assets have x86_64 ELF headers. [OrcaSlicer v2.4.2](https://github.com/OrcaSlicer/OrcaSlicer/releases/tag/v2.4.2) publishes `OrcaSlicer_Linux_AppImage_Ubuntu2404_aarch64_V2.4.2.AppImage`, with release SHA-256 `e1a07275a25f176626c55a5df39e91bc4476d8c28ee4a3192ff758e29dd5c3ba`. Its documented ARM64 availability does not establish compatibility with the pinned MCP's CLI arguments. Verify that boundary before binding a workflow.

Provide exact machine, process and filament JSON files. The provider's defaults select PLA; the handle requires PETG, 0.20 mm layers, five walls and 40% infill. Never silently use defaults or declare profiles equivalent. Record resolved profile hashes and inspect actual package settings.

## Scope and verification

Only `slice_model_file` is proposed for the isolated qualification. Use network-disabled runtime containers, no printer credentials, a fresh output path and exact declared input. Do not call printer discovery/status/upload/print. The tool requires `confirm=true` for offline slicing; that flag is not human print approval.

A fresh offline synthetic 10 mm coupon call through GatewayService/StdioRunner succeeded with OrcaSlicer 2.4.2. Its actual package confirms PETG, P1S 0.4 mm, 0.20 mm layers, five walls, 40% infill and Textured PEI Plate. This is not handle qualification. After a call, check both MCP errors and returned `ok`, exact source/output paths and actual artifact bytes. Feed the package into Wright's existing passive manufacturing checks. A produced 3MF or preview is not physical verification or engineering acceptance.

## Recovery and follow-up

The pinned tool uses a synchronous native subprocess and may overwrite a supplied output path. Record the attempt before dispatch. After timeout or disconnect, reconcile the process and exact output before allowing a fresh attempt; never replay an uncertain call automatically. Preserve failed artifacts. No provider defect has been established and no report has been submitted.

Private qualification inputs/source audit: `.local-run/experience-review/slicer-provider-audit/`. Protocol, native CLI, gateway slicing and nominal toolpath inspection passed. The unchanged mandatory package-PNG check fails because this headless package contains no PNG. Full handle and clean Intel-Linux catalog qualification remain open. Windows and Linux ARM64 remain separate qualification scopes.

The first attempt returned `ok:false` for incompatible default Cool Plate despite a successful MCP envelope. Explicit Textured PEI Plate corrected a fresh attempt. Whole-file motion inspection rejects startup G380; the existing reader accepts explicit unique `;VT0` to `; filament end gcode` nominal boundaries. Preserve that scoped interpretation and do not claim machine simulation. Public receipt: `prototypes/desktop-harness/engineering-experience/evidence/offline-slicer-qualification/`.

## Prerelease preview qualification

The stable 2.4.2 image still lacks a native package PNG, including under Xvfb. A separate official OrcaSlicer **2.5.0-alpha** ARM64 image passed the existing mandatory preview gate on the same synthetic coupon. This is explicitly a prerelease selection for isolated digital qualification, not an installed upgrade or production recommendation. Official asset SHA-256: `b64c705537a80ca0f4a5d0b51fa21d1f789191141f54b7f3599d2f2b9bfad0be`. Tested image: `sha256:ec4229b057a0a4897ce1a614b4cd627a366704a7f8b071965a0ec084d14b60d3`.

Use Docker's `--init` before `xvfb-run -a --server-args=-screen 0 1280x1024x24 /opt/venv/bin/bambu-p1s-mcp`; set `BAMBU_SLICER=/opt/orca-alpha/AppRun` and the exact three profiles. The extracted public application directories initially denied nonroot traversal; correcting their read/execute permissions inside the selected image fixed native startup. Keep the network disabled and printer credentials absent. Native PNG generation is qualified; human manufacturing acceptance is not.

[Upstream thumbnail fix](https://github.com/OrcaSlicer/OrcaSlicer/pull/15745) and [official prerelease](https://github.com/OrcaSlicer/OrcaSlicer/releases/tag/v2.5.0-alpha). The public evidence directory above includes separate stable and alpha receipts and exact failures; do not overwrite one version's qualification with the other.

## Support generation — two-orientation digital check

A fresh support-enabled copy of the coupon process profile has now been qualified
with the same pinned alpha image through Wright's gateway. A synthetic L-shaped
overhang produced 14,042 nominal support segments upright and zero laid on its
side. Both packages retained the required PETG/P1S settings and native PNGs.
The original candidate profile remains unchanged with supports disabled: it must
not be used to claim the handle's support comparison is ready. Select/freeze the
new profile explicitly before that workflow runs.

Evidence and exact profile bytes:
`prototypes/desktop-harness/engineering-experience/evidence/support-profile-qualification/`.
The PNG depicts the model orientation, not generated supports; the passive
nominal-path SVG depicts one actual layer. Contact areas, strength applicability,
support removal and real handle acceptance remain unverified. No physical action
or catalog-wide compatibility claim follows from this isolated ARM64 check.
