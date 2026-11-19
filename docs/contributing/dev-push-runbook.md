# Standalone Wright development checks

Before pushing a feature branch for a pull request to `dev`, run `scripts/check-dev-push.ps1` on Windows or `sh scripts/check-dev-push.sh` on Unix. Use Python 3.11 or newer with the current security patches. Windows accepts `-Python` to select an interpreter. The Unix script accepts the `PYTHON` environment variable.

The gate creates a temporary environment, builds the sdist and its wheel, checks their contents, installs the wheel and runs the tests from the unpacked sdist. The tests exercise actual MCP subprocesses and a file handoff. Configure pip with a local wheelhouse for offline runs. Point the operating system's temporary directory at the desired build volume.

Open a draft pull request with the gate result and both artifact digests. CI builds one distribution pair and tests those same artifacts on Windows, Linux and macOS with Python 3.11 and 3.13. Review the installed test results before merging. Package publication requires its own release decision.

The reviewed 0.1.0.dev2 artifacts use Hatchling 1.31.0 and Windows line endings for the shipped source files. Git attributes preserve those exact example and source bytes across checkouts. The gate compares the built artifacts with the recorded SHA-256 digests in `.github/shared-distributions.sha256`.
