# Security Policy

We take the security of Wright seriously. If you believe you have found a security vulnerability, please report it to us privately following the instructions below. 

**DO NOT open a public GitHub Issue for security vulnerabilities.**

---

## Supported Versions

Release candidates are blocked on fixable High/Critical image findings unless
a reviewed exception names the finding, owner, rationale, compensating control,
and expiry. Python dependency audit exceptions follow the same expiring model.
Published Python files and OCI version/SHA references are immutable: security
corrections use a new patch version, with PyPI yanking or OCI quarantine and
mutable-alias restoration applied only under the release recovery runbook.

Only the latest active development release is supported for security updates. We do not maintain security backports for older versions at this stage of development.

| Version | Supported |
| --- | --- |
| Latest Development | :white_check_mark: Yes |
| < Latest Release | :x: No |

---

## Reporting a Vulnerability

Please report security issues privately by emailing the maintainer directly:

**Email**: `burhop@gmail.com`

When reporting a vulnerability, please include:
1. A descriptive title and details of the vulnerability.
2. A description of the impact (what could an attacker accomplish?).
3. Step-by-step instructions to reproduce the issue, including any proof-of-concept (PoC) scripts.
4. The version/commit hash of Wright where the issue was identified.

---

## Our Security Response Commitment

Upon receiving a security report, we commit to the following timeline:

1. **Acknowledgment**: We will acknowledge receipt of your report within **48 hours**.
2. **Initial Assessment**: We will perform an initial assessment of the issue and provide a status update within **7 days**.
3. **Remediation**: If confirmed, we will work on a fix and release a patched version as quickly as possible, coordinate publication, and credit the researcher.

Thank you for helping keep the Wright community safe!
