"""Install the built wheel and run the sdist's tests in a separate directory."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile


def verify(dist):
    dist = dist.resolve(strict=True)
    wheel, = dist.glob("*.whl")
    archive, = dist.glob("*.tar.gz")
    expected = pinned_digests()
    if {p.name for p in dist.iterdir()} != expected.keys() or {wheel.name, archive.name} != expected.keys():
        raise ValueError("The distribution directory must contain exactly the reviewed wheel and sdist")
    for artifact in (wheel, archive):
        with artifact.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        print(f"{artifact.name}  sha256 {digest}", flush=True)
        if digest != expected[artifact.name]:
            raise ValueError(f"{artifact.name} differs from the reviewed shared artifact")
    with zipfile.ZipFile(wheel) as contents:
        for member in contents.namelist():
            path = PurePosixPath(member)
            if ".." in path.parts or path.parts[0] not in {"wright_workflow", wheel.name.split("-py", 1)[0] + ".dist-info"}:
                raise ValueError(f"Unexpected wheel member {member}")
    with tempfile.TemporaryDirectory() as directory:
        # macOS can put TMPDIR under /var, a symlink to /private/var.
        root = Path(directory).resolve(strict=True)
        with tarfile.open(archive) as contents:
            prefix = archive.name.removesuffix(".tar.gz")
            for item in contents:
                path = PurePosixPath(item.name)
                if path.is_absolute() or ".." in path.parts or path.parts[0] != prefix or not (item.isfile() or item.isdir()):
                    raise ValueError(f"Unexpected archive member {item.name}")
                relative = path.relative_to(prefix)
                if item.isfile() and not (
                    relative.as_posix() in {".gitignore", "FORMAT.md", "LICENSE", "PKG-INFO", "pyproject.toml"}
                    or relative.is_relative_to("src/wright_workflow")
                    or relative.is_relative_to("examples/handoff")
                    or relative.is_relative_to("tests") and relative.suffix == ".py"
                ):
                    raise ValueError(f"Unexpected source distribution file {relative}")
            contents.extractall(root, filter="data")
        source, = root.iterdir()
        environment = root / "installed"
        builder = venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt")
        builder.create(environment)
        python = builder.ensure_directories(environment).env_exec_cmd
        report = root / "installation.json"
        subprocess.run(
            [python, "-m", "pip", "install", "--report", str(report), str(wheel)],
            check=True, cwd=root,
        )
        packages = [entry["metadata"] for entry in json.loads(report.read_bytes())["install"]]
        print("Installed runtime dependencies:", ", ".join(sorted(
            f"{package['name']}=={package['version']}" for package in packages
        )), flush=True)
        subprocess.run([python, "-m", "pip", "check"], check=True, cwd=root)
        check_quickstart(Path(python), environment, source / "examples" / "handoff", root)
        subprocess.run([python, "-m", "pip", "install", "pytest"], check=True, cwd=root)
        checks = Path(__file__).resolve().parent
        test_env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
        subprocess.run(
            [python, "-I", "-m", "pytest", "-q", str(checks / "test_boundaries.py")],
            check=True, cwd=root, env=test_env,
        )
        subprocess.run(
            [python, "-I", str(checks / "check_installed.py"),
             str(report), str(source / "tests")],
            check=True, cwd=root, env=test_env,
        )


def check_provider_python(command, environment):
    # A launcher can have multiple paths, and two venvs can link to the same binary.
    if not command.is_absolute():
        raise ValueError(f"Expected an absolute Python launcher path, got {command}")
    prefix = Path(subprocess.check_output(
        [command, "-I", "-c", "import sys; print(sys.prefix)"], text=True,
    ).rstrip("\r\n"))
    if not prefix.samefile(environment):
        raise ValueError(f"Provider command {command} started {prefix}, expected {environment}")
    print(f"Provider command {command} uses the selected environment {prefix}", flush=True)


def check_quickstart(python, environment, example, root):
    bindings = root / "bindings.json"
    subprocess.run([python, example / "configure.py", bindings], cwd=root, check=True)
    servers = json.loads(bindings.read_bytes()).values()
    for command in {Path(server["command"]) for server in servers}:
        check_provider_python(command, environment)
    cli = python.with_name("wright-workflow.exe" if os.name == "nt" else "wright-workflow")
    source = example / "length.workflow.wflow"
    parsed = json.loads(subprocess.check_output([cli, "parse", source], cwd=root))
    if parsed["source_digest"] != hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError("The installed CLI parsed a different source")
    run_dir = root / "quickstart"
    receipt = json.loads(subprocess.check_output(
        [cli, "run", source, "--bindings", bindings, "--run-dir", run_dir], cwd=root,
    ))
    if receipt["status"] != "completed":
        raise ValueError(f"The installed quickstart stopped at {receipt['status']}")
    produced = receipt["ports"]["writer.coordinates"]
    consumed = receipt["attempts"][1]["consumed"]["writer.coordinates"]
    digest = hashlib.sha256((run_dir / "files" / produced["path"]).read_bytes()).hexdigest()
    measured = receipt["ports"]["reader.measurement"]["value"]
    if produced != consumed or produced["sha256"] != digest or measured != {"length_mm": 5, "sha256": digest}:
        raise ValueError("The installed CLI handoff did not match the measured file")
    print(f"Installed quickstart: {produced['size']} bytes, SHA-256 {digest}, {measured['length_mm']} mm", flush=True)


def pinned_digests():
    receipt = Path(__file__).with_name("shared-distributions.sha256")
    return {filename: digest for digest, filename in (line.split() for line in receipt.read_text().splitlines())}


def build_in_isolation(dist):
    repository = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        builder = venv.EnvBuilder(with_pip=True)
        environment = scratch / "venv"
        builder.create(environment)
        python = builder.ensure_directories(environment).env_exec_cmd
        subprocess.run([python, "-m", "pip", "install", "build", "hatchling==1.31.0"], check=True)
        subprocess.run([python, "-m", "build", "--no-isolation", "--outdir", str(dist), str(repository)], check=True, cwd=scratch)


def check_dev_push():
    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        dist = scratch / "artifacts"
        build_in_isolation(dist)
        verify(dist)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path(__file__).resolve().parents[1] / "dist")
    parser.add_argument("--check-dev-push", action="store_true")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    if args.check_dev_push:
        check_dev_push()
    elif args.build:
        build_in_isolation(args.dist.resolve())
    else:
        verify(args.dist.resolve())
