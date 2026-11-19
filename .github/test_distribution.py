"""Install the built wheel and run the sdist's tests in a separate directory."""

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile


def verify(dist):
    wheel, = dist.glob("*.whl")
    archive, = dist.glob("*.tar.gz")
    expected = pinned_digests()
    for artifact in (wheel, archive):
        with artifact.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        print(f"{artifact.name}  sha256 {digest}", flush=True)
        if artifact.name in expected and digest != expected[artifact.name]:
            raise ValueError(f"{artifact.name} differs from the reviewed shared artifact")
    with zipfile.ZipFile(wheel) as contents:
        for member in contents.namelist():
            path = PurePosixPath(member)
            if ".." in path.parts or path.parts[0] not in {"wright_workflow", wheel.name.split("-py", 1)[0] + ".dist-info"}:
                raise ValueError(f"Unexpected wheel member {member}")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
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
        subprocess.run([sys.executable, "-m", "pip", "install", str(wheel)], check=True, cwd=root)
        subprocess.run(
            [sys.executable, "-I", "-m", "pytest", "-q", str(source / "tests")],
            check=True, cwd=root,
        )


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
        builder = venv.EnvBuilder(with_pip=True)
        environment = scratch / "installed"
        builder.create(environment)
        python = builder.ensure_directories(environment).env_exec_cmd
        subprocess.run([python, "-m", "pip", "install", "pytest"], check=True)
        subprocess.run([python, "-I", str(Path(__file__).resolve()), "--dist", str(dist)], check=True, cwd=scratch)


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
