# Workspace Surfaces Test Fixtures

This directory owns deterministic conformance and hostile fixtures. A fixture
must document its expected outcome, protocol version, security intent, required
feature detection, and cleanup behavior. Hostile fixtures are test-only and may
never be imported by production packages or copied into user documentation.

Tests resolve this root through the `workspace_surfaces_fixture_root` fixture;
they must not assume a current directory, path separator, drive letter, or
repository-relative shell path.
