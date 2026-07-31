# Workspace Surfaces Dependency Review

This record captures the package identity, provenance, licensing, and intended
use reviewed for the Workspace Surfaces frontend. Versions are exact in
`apps/web/package.json` and the npm lockfiles so release inputs do not drift.
The packages are bundled into Wright's frontend; Workspace Surfaces must not
load these libraries from a CDN at runtime.

Review date: 2026-07-30

| Package | Version | License | Upstream and registry evidence | Workspace Surfaces use |
|---|---:|---|---|---|
| `@modelcontextprotocol/ext-apps` | `1.7.5` | MIT | [upstream](https://github.com/modelcontextprotocol/ext-apps), [npm tarball](https://registry.npmjs.org/@modelcontextprotocol/ext-apps/-/ext-apps-1.7.5.tgz), integrity `sha512-TjPH2S2y5UEGKhmI6+XGFuqfqOV4ppe1x6DA3txnUaEWkgtA4G5vo14jGKFZmegdkZ1H4QMLyujLvoU1BEdnAg==` | Standards-aligned MCP Apps host/client contracts. |
| `dompurify` | `3.4.12` | MPL-2.0 OR Apache-2.0 | [upstream](https://github.com/cure53/DOMPurify), [npm tarball](https://registry.npmjs.org/dompurify/-/dompurify-3.4.12.tgz), integrity `sha512-zQvGet8Z2sWbQhCmfFz/T5QWH2oBmjnqK3qvOjaqaNLrLEF912WamU+ohnTp0TCep/MFVHpdJuCZEdFOdTnEFg==` | Sanitize explicitly allowed passive HTML before rendering. |
| `plotly.js-dist-min` | `3.7.0` | MIT | [upstream](https://github.com/plotly/plotly.js), [npm tarball](https://registry.npmjs.org/plotly.js-dist-min/-/plotly.js-dist-min-3.7.0.tgz), integrity `sha512-IRWNnBJZmKss3URDnicBK2nvt/VTSi/MD1GnUscAYFjwSuN6g/CTde5R1UC0RYtblehj8rkT4BL8r05e/c8j5Q==` | Lazy, local-only rendering of Plotly display envelopes. |
| `@types/plotly.js` | `3.0.10` | MIT | [upstream](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/plotly.js), [npm tarball](https://registry.npmjs.org/@types/plotly.js/-/plotly.js-3.0.10.tgz), integrity `sha512-q+MgO4aajC2HrO7FllTYWzrpdfbTjboSMfjkz/aXKjg1v7HNo1zMEFfAW7quKfk6SL+bH74A5ThBEps/7hZxOA==` | Compile-time declarations for the Plotly renderer. |

DOMPurify includes its own TypeScript declarations, so no separate DOMPurify
types package is required. Package-lock integrity values are the enforcement
source; the values above make the review input human-auditable. Vulnerability
and generated-license gates remain separate release checks and are not implied
to pass merely by this provenance review.

## Audit Observation

`npm audit --workspace web --omit=dev` on 2026-07-30 reported two high-severity
findings in the pre-existing `react-router-dom`/`react-router` chain
(`GHSA-qwww-vcr4-c8h2`). None of the four packages introduced above appeared in
the finding path. The release security gate remains blocked until the router
advisory is upgraded, safely pinned to an unaffected compatible version, or
handled under the repository's documented vulnerability policy; this review
does not waive it.
