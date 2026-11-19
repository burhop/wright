# Standalone Wright development checks

Before pushing a feature branch for a pull request to `dev`, run `scripts/check-dev-push.ps1` on Windows or `sh scripts/check-dev-push.sh` on Unix. Use Python 3.11 or newer with the current security patches. Windows accepts `-Python` to select an interpreter. The Unix script accepts the `PYTHON` environment variable.

The gate builds the sdist and its wheel, checks their contents and installs the wheel in a new virtual environment. Before adding test dependencies, it runs the quickstart from the sdist with the installed `wright-workflow` command and verifies the file received by the second MCP provider. It uses the platform default launcher layout, including linked Python executables on Linux and macOS. Configure pip with a local wheelhouse for offline runs. Point the operating system's temporary directory at the desired build volume.

Open a draft pull request with the gate result and both artifact digests. CI builds one distribution pair and tests those same artifacts on Windows, Linux and macOS with Python 3.11 and 3.13. Review the installed test results before merging. Package publication requires its own release decision.

The reviewed 0.1.0.dev2 artifacts use Hatchling 1.31.0 and Windows line endings for the shipped source files. Git attributes preserve those exact example and source bytes across checkouts. The gate requires both filenames and SHA-256 digests to match `.github/shared-distributions.sha256`.

Each installed job creates an empty virtual environment, records the engine's resolved runtime dependencies before adding pytest, and runs `pip check`. It checks imports in the installed Python files and loads each module from the wheel. During conformance the engine process rejects commercial module imports and external address lookups or connections. The two example MCP providers run as separate caller-configured stdio processes.

The quickstart gate starts each distinct configured Python launcher and verifies the active virtual environment reported by that process. This accepts alternate paths to the selected environment and detects a launcher that starts a different one. The normal handoff then exercises the example's pinned executable and provider files.
