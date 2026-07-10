from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_image_has_no_sudo_or_universal_key():
    dockerfile = text("docker/Dockerfile")
    supervisor = text("docker/supervisord.conf")
    entrypoint = text("docker/entrypoint.sh")

    assert "NOPASSWD" not in dockerfile
    assert "    sudo \\" not in dockerfile
    assert "wright-local-dev-key" not in supervisor
    assert "wright-local-dev-key" not in entrypoint
    assert "generate_secret" in entrypoint
    assert "WRIGHT_API_TOKEN must be set" in entrypoint


def test_native_profile_setup_has_no_universal_key():
    setup = text("scripts/setup-wright-profile.sh")

    assert "wright-local-dev-key" not in setup
    assert "HERMES_API_KEY:?" in setup


def test_default_compose_is_read_only_least_privilege_and_narrow():
    prohibited = {"/home/", "/usr/local/", "/opt/", "/var/lib/", "/var/cache/", "/etc/"}
    for filename in ("docker-compose.yml", "docker-compose.minimal.yml"):
        compose = yaml.safe_load(text(filename))
        agent = compose["services"]["agent"]
        assert agent["read_only"] is True
        assert agent["cap_drop"] == ["ALL"]
        assert "no-new-privileges:true" in agent["security_opt"]
        targets = {mount.rsplit(":", 1)[-1] for mount in agent["volumes"]}
        assert targets.isdisjoint(prohibited)
        assert "/home/agent/.local/share/wright" in targets
        assert "/home/agent/workspace" in targets


def test_legacy_compose_is_explicitly_migration_only():
    legacy = text("docker-compose.legacy.yml")
    assert "Migration-only" in legacy
    assert "external: true" in legacy
